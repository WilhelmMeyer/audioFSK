# audioFSK

Modem FSK acústico em Python. Transmite bytes como som pela placa de áudio (alto-falante → microfone) e recupera os bytes do outro lado. Tons Bell 202: mark 1200 Hz, space 2200 Hz, 1200 baud, enquadramento UART 8N1.

Uso típico: link de dados half-duplex entre duas máquinas sem rede — só áudio.

## Requisitos

- Python 3.10+
- PortAudio instalado no sistema (`sudo apt install libportaudio2` no Debian/Ubuntu)

```bash
python -m venv venv
./venv/bin/pip install -r requirements.txt
```

## Uso

Teste de loopback (sem hardware, sinal sintético + ruído gaussiano):

```bash
./venv/bin/python loopback_test.py
```

Modem ao vivo, modo terminal (stdin/stdout):

```bash
./venv/bin/python app.py
```

Modem ao vivo, modo PTY — expõe um dispositivo serial virtual:

```bash
./venv/bin/python app.py --pty
# [+] Created PTY: /dev/pts/N
picocom -b 1200 /dev/pts/N
```

O modo PTY é o mais útil: qualquer programa que fale com uma porta serial (picocom, minicom, `pppd`, scripts com pyserial) enxerga o canal acústico como `/dev/pts/N`.

## Arquitetura

```
stdin/PTY ──> tx_byte_queue ──> [modulator thread] ──> tx_audio_queue ──┐
                                                                        │
                                                            [audio_callback]
                                                                        │
stdout/PTY <── rx_byte_queue <── [demodulator thread] <── rx_audio_queue ┘
```

### Arquivos

| Arquivo | Papel |
|---|---|
| `modem.py` | DSP puro. `FSKModulator` + `FSKDemodulator`. Zero I/O, zero threads. |
| `app.py` | Runtime. Threads, filas, stream de áudio, interfaces stdio/PTY. |
| `loopback_test.py` | Teste ponta-a-ponta em memória com ruído injetado. |

## Decisões de arquitetura

### 1. DSP separado de I/O

`modem.py` não importa `sounddevice`, não cria threads e não toca em arquivo nenhum. Recebe `np.ndarray` de samples e devolve `bytes` (e vice-versa). Consequência prática: o loopback test roda sem hardware de áudio, sem PortAudio, sem device permissions — e testa exatamente o mesmo código que roda ao vivo.

### 2. FSK de fase contínua

`FSKModulator` acumula fase entre símbolos (`self.phase`) em vez de reiniciar o seno a cada bit. Descontinuidade de fase espalha energia espectral e produz cliques audíveis que o filtro passa-faixa do receptor não remove. Fase contínua mantém o sinal dentro da banda de 800–2600 Hz — importante porque o canal real é um alto-falante barato e um microfone barato.

Custo: o modulador tem estado. Ele **não** é reentrante e só pode ser usado por uma thread.

### 3. Discriminador delay-and-multiply

Demodulação não usa correlacionador de dois tons nem FFT. Usa o clássico:

```
bandpass → x[n] * x[n-D] → lowpass
```

com `D = fs / (4·f_center)` — um atraso de aproximadamente 90° na frequência central (1700 Hz). O produto de um sinal com sua versão atrasada gera um termo DC proporcional a `cos(2π·f·D/fs)`, que muda de sinal entre mark e space. Depois do passa-baixas, mark é positivo e space é negativo — a decisão de bit vira um teste de sinal.

Por quê esse método:

- Uma multiplicação e dois `lfilter` por bloco. Tudo em C via scipy. Roda folgado em tempo real.
- Não precisa de recuperação de portadora nem de estimativa de frequência.
- Tolera desvio de clock e de frequência muito melhor que correlação coerente.

Trade-off aceito: pior desempenho em SNR baixo que um detector coerente. Para acoplamento acústico curto (mesma sala) isso não é o gargalo.

### 4. Enquadramento UART em vez de protocolo próprio

Cada byte vai como start bit (0) + 8 bits LSB-first + stop bit (1). Não há framing de pacote, comprimento nem CRC.

Motivo: o modem se comporta como uma linha serial burra. Isso permite plugar em `/dev/pts/N` e reusar todo o ecossistema serial existente sem escrever driver. Recuperação de clock também sai de graça — o receptor sincroniza na borda de descida do start bit e amostra no meio de cada símbolo (`samples_per_symbol // 2`, depois de `samples_per_symbol` em `samples_per_symbol`).

O preço: **sem detecção de erro**. Um byte corrompido chega corrompido. Camada de link (comprimento + CRC + ARQ) é trabalho futuro, e o desenho já reserva o lugar dela — acima do modem, não dentro dele.

### 5. Squelch por amplitude de banda-base

Sem sinal, o discriminador entrega ruído em torno de zero, e a máquina de estados UART enxerga bordas de descida falsas e emite lixo. Solução: quando `|baseband| < squelch`, força o valor para `+1.0` (mark/idle).

Escolha deliberada de fazer isso *depois* do passa-baixas em vez de calcular um envelope de energia separado: `mult` já é proporcional à energia do sinal, então a amplitude da banda-base é ela própria um indicador de portadora presente. Isso evita um segundo filtro com estado a manter na cadeia de streaming.

Limitação: o limiar (`0.005` em `app.py`) é fixo. Ganho de microfone muito baixo derruba o link; muito alto deixa passar ruído. Um squelch adaptativo (limiar seguindo um piso de ruído médio móvel) é a melhoria óbvia.

### 6. Estado de filtro explícito para streaming

O áudio chega em blocos de 2048 samples. Chamar `lfilter` por bloco sem estado gera transiente na borda de cada bloco e destrói os bits ali. Por isso o demodulador carrega `bpf_state`, `lpf_state` e `prev_samples` (os `D` últimos samples, para o atraso do discriminador cruzar a fronteira de bloco) entre chamadas.

Consequência: `FSKDemodulator` é stateful e amarrado a uma stream. Duas streams simultâneas = duas instâncias. `reset()` existe para reaproveitar a instância entre sessões.

### 7. Callback de áudio faz o mínimo

`audio_callback` roda em thread de tempo real do PortAudio. Estourar o deadline dela causa underrun e áudio picotado. Então o callback só faz duas coisas: copiar o input para uma fila e copiar da fila de saída para `outdata`. Todo o DSP acontece em threads normais (`modulator_thread_fn`, `demodulator_thread_fn`) conectadas por `queue.Queue`.

Efeito colateral: latência maior (um bloco de fila a mais em cada direção), mas sem dropouts. Para 1200 baud, latência não importa.

### 8. Preâmbulo antes de cada rajada

`app.py` prefixa `0x55 × 10 + 0xFF` em cada rajada transmitida. `0x55` é `01010101`, que junto com start/stop bits gera uma alternância mark/space contínua — isso acorda o AGC do microfone, estabiliza os filtros do receptor e dá bordas para a máquina de estados sincronizar. `0xFF` marca o fim do preâmbulo.

Note que o preâmbulo vive em `app.py`, não em `modem.py` — é decisão de camada de enlace, não de modulação.

## Limitações conhecidas

- **Sem detecção de erro.** Bytes corrompidos passam silenciosamente.
- **Half-duplex na prática.** Não há CSMA nem controle de acesso ao meio; transmissão simultânea das duas pontas colide.
- **Squelch fixo.** Não se adapta ao nível de ruído do ambiente.
- **Preâmbulo aparece no RX.** O receptor não filtra `0x55`/`0xFF`; o modo stdio faz uma limpeza grosseira (`b < 128 and b != 0xff`), o modo PTY entrega tudo cru.
- **Sem eco cancelado.** O modem escuta a própria transmissão pelo microfone. Em loopback acústico real isso pode gerar bytes duplicados.
- `pyserial` está no `requirements.txt` mas nenhum código do projeto o importa.

## Próximos passos naturais

1. Camada de enlace: framing com comprimento + CRC-16, e ARQ stop-and-wait.
2. Squelch adaptativo baseado em piso de ruído móvel.
3. Supressão do próprio eco (mute do RX enquanto o TX está ativo).
4. Testes automatizados de BER varrendo SNR, em vez de um único caso pass/fail.

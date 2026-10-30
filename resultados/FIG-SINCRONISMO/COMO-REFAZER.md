# sincronismo-varreduras.png -- como refazer

Sintético: o `MaryModulator` e o `modem.chirp` do sistema geram varredura, 30 ms de silêncio, 12 bytes de 16-FSK, silêncio e varredura (S = 30 símbolos), sem ar. n1 e n2 por `modem.find_chirp_pair`, fronteiras em n1 + k (n2 - n1) / S. Formato e cores do visor. Gerada em 2026-10-29.

```bash
./venv/bin/python resultados/FIG-SINCRONISMO/figura_sincronismo.py
```

## sincronismo-bloco.png (2026-10-30)

Bits certos ao longo do quadro, malha contra varreduras, média das 24 gravações de `old/studies/20260903-111105-ganho-mary/` (16-FSK, 48 bytes, rep 1, varreduras nas duas pontas, uma máquina com caixa Bluetooth; fora do git). Cada gravação lida dos dois jeitos de `resultado.py` (malha e `sweep_llr`), régua única: o quadro (palavra de referência + bloco codificado, 1201 bits) alinhado pelo melhor deslizamento do quadro inteiro, acerto em 20 janelas de 5%.

- Blocos íntegros: malha 15 de 24, varreduras 23 de 24 (por `resultado.decodes`).
- Primeiros 10% do quadro: malha 83,5%, varreduras 91,0%. Resto: 89,3% contra 90,7%.
- A malha não cai no meio do quadro nestas gravações: perde no começo, enquanto ainda trava, que é onde fica a palavra de referência. Nenhuma gravação com áudio disponível mostrou queda no meio do quadro (conferido também em `old/captures-chirp/`).

    ./venv/bin/python resultados/FIG-SINCRONISMO/figura_sincronismo_bloco.py

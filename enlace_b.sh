#!/usr/bin/env bash
# Opera a ponta B (Windows) do enlace pelo SSH, a partir do Linux.
#
#   ./enlace_b.sh envia                       copia enlace.py, saudacao.py, painel.py e confere MD5
#   ./enlace_b.sh inicia --papel ouvinte --enviar "oi do B" --duracao 900
#                                             lança saudacao.py pelo SSH, como no H06 (morre se o SSH cair)
#   ./enlace_b.sh inicia-wmi ...               idem, mas fora da sessão SSH (sobrevive à queda; áudio
#                                             por esse caminho ainda não medido)
#   ./enlace_b.sh estado | log [n] | pausa | retoma | finaliza | para
#   ./enlace_b.sh segue                       acompanha o diário de B ao vivo (Ctrl-C só para de olhar)
#   ./enlace_b.sh mata                        taskkill no pid do estado, quando o painel não responde
#   ./enlace_b.sh puxa [destino]              traz a sessão mais recente de B
#
# Um processo filho do sshd morre quando a conexão cai; `inicia-wmi` cria o
# processo por WMI (Win32_Process.Create), que não pertence à sessão SSH e não
# deixa nada instalado. A saída vai para enlace_teste\saudacao.log nos dois.
set -euo pipefail

# Outra máquina B: ENLACE_B=gi_se@giselle ENLACE_B_REPO='C:\Users\gi_se\audioFSK'
# ENLACE_B_DIR='C:\Users\gi_se\audioFSK' ENLACE_B_REL=audioFSK (DIR relativo ao perfil, para o scp).
B=${ENLACE_B:-Home@100.114.48.25}
DIR=${ENLACE_B_DIR:-'C:\Users\Home\enlace_teste'}
REPO=${ENLACE_B_REPO:-'C:\Users\Home\Workspace\audioFSK'}
REL=${ENLACE_B_REL:-enlace_teste}
PY="$REPO\\venv\\Scripts\\python.exe"
AQUI=$(cd "$(dirname "$0")" && pwd)

ssh_b() { ssh -o BatchMode=yes -o ConnectTimeout=15 -o LogLevel=ERROR "$B" "$@"; }
painel() { ssh_b "cd /d $DIR && $PY painel.py $*"; }

cmd=${1:-}; shift || true
case "$cmd" in
  envia)
    scp -q -o LogLevel=ERROR "$AQUI"/{enlace.py,saudacao.py,painel.py} "$B:$REL/"
    for f in enlace.py saudacao.py painel.py; do
      l=$(md5sum "$AQUI/$f" | cut -d' ' -f1)
      r=$(ssh_b "certutil -hashfile $DIR\\$f MD5" | sed -n 2p | tr -d ' \r')
      [ "$l" = "$r" ] && echo "$f igual" || { echo "$f DIFERENTE ($l / $r)"; exit 1; }
    done ;;
  inicia|inicia-wmi)
    # Os argumentos vão para um .cmd copiado para B: evita três camadas de aspas
    # (ssh -> cmd -> powershell) num texto que pode ter espaços.
    t=$(mktemp)
    {
      printf 'cd /d %s\r\n' "$DIR"
      printf 'set PYTHONPATH=%s\r\n' "$REPO"
      printf 'set ENLACE_DEPURA=1\r\n'
      printf '"%s" -u saudacao.py' "$PY"
      for a in "$@"; do printf ' "%s"' "$a"; done
      printf ' --log saudacao.log\r\n'
    } > "$t"
    scp -q -o LogLevel=ERROR "$t" "$B:$REL/roda.cmd"; rm -f "$t"
    if [ "$cmd" = inicia ]; then
      # O ssh fica em segundo plano aqui; a sessão vive enquanto ele viver.
      nohup ssh -o BatchMode=yes -o LogLevel=ERROR -o ServerAliveInterval=15 "$B" \
        "cmd /c $DIR\\roda.cmd" > /dev/null 2>&1 &
      echo "ssh local em segundo plano, pid $!"
    else
    ssh_b "powershell -NoProfile -Command \"\$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine='cmd /c $DIR\\roda.cmd'; CurrentDirectory='$DIR'}; 'pid do cmd: ' + \$r.ProcessId + ' (retorno ' + \$r.ReturnValue + ')'\""
    fi
    sleep 6
    painel estado | head -12 || echo "o painel ainda não responde; veja: ./enlace_b.sh log ou saudacao.log" ;;
  estado|pausa|retoma|finaliza|para) painel "$cmd" ;;
  log) painel log "${1:-40}" ;;
  segue) ssh -t -o LogLevel=ERROR "$B" "cd /d $DIR && $PY painel.py segue" ;;
  mata)
    # Do arquivo, não do painel: se o painel respondesse, `para` bastaria.
    pid=$(ssh_b "powershell -NoProfile -Command \"Get-ChildItem $DIR\\sessoes-enlace\\*.estado.json | Sort-Object LastWriteTime | Select-Object -Last 1 | Get-Content -Raw\"" \
          | sed -n 's/.*"pid": \([0-9]*\).*/\1/p')
    [ -n "$pid" ] || { echo "sem pid no estado; procure com: ssh $B tasklist"; exit 1; }
    ssh_b "taskkill /pid $pid /f"
    echo "agora: ./enlace_b.sh puxa  e  painel.py recupera <stem>.parcial.f32" ;;
  puxa)
    # Só a sessão mais recente: as antigas têm WAV de centenas de MB e o
    # Tailscale leva minutos para cada um.
    dest=${1:-sessoes-enlace-B}; mkdir -p "$dest"
    stem=$(ssh_b "powershell -NoProfile -Command \"(Get-ChildItem $DIR\\sessoes-enlace\\*.diario.txt | Sort-Object LastWriteTime | Select-Object -Last 1).BaseName -replace '\\.diario$',''\"" | tr -d '\r')
    [ -n "$stem" ] || { echo "nenhuma sessão em B"; exit 1; }
    scp -q -o LogLevel=ERROR "$B:$REL/sessoes-enlace/$stem.*" "$dest/"
    scp -q -o LogLevel=ERROR "$B:$REL/saudacao.log" "$dest/" 2>/dev/null || true
    ls -t "$dest" | head ;;
  *) sed -n '2,14p' "$0"; exit 2 ;;
esac

# Telas do capítulo 5

Provisória: as telas ainda mudam em 2026-10-30. Refazer no fim dos testes, com uma sessão real no ar.

1. Com a sessão rodando, `adb exec-out screencap -p > tela-celular.png` (tela no topo).
2. `google-chrome --headless=new --force-device-scale-factor=1.5 --window-size=1400,900 --virtual-time-budget=4000 --screenshot=tela-computador.png http://127.0.0.1:<porta do visor>/`
3. `python figura_telas.py` e copiar `telas-visor-celular.png` para `artigo/figuras/`.

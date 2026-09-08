@echo off
rem Monta o artigo no Windows. A logica esta em monta.py, o mesmo arquivo que
rem o monta.sh do Linux chama; aqui so' se escolhe o interpretador.
rem Uso, a partir de qualquer pasta:  artigo\monta.cmd --sem-figuras
rem
rem O nome nao basta para escolher: o atalho da Microsoft Store se chama
rem python.exe, esta no PATH e nao e' interpretador nenhum, sai com 9009 depois
rem de convidar a instalar. Por isso cada candidato roda um -c antes de receber
rem o trabalho, o que de quebra recusa um Python mais velho que o 3.11 exigido
rem pelo conversor.
setlocal
set "AQUI=%~dp0"
set "TESTE=import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)"

py -3 -c "%TESTE%" >nul 2>&1
if errorlevel 1 goto tenta_python
py -3 "%AQUI%monta.py" %*
exit /b %ERRORLEVEL%

:tenta_python
python -c "%TESTE%" >nul 2>&1
if errorlevel 1 goto sem_python
python "%AQUI%monta.py" %*
exit /b %ERRORLEVEL%

:sem_python
echo Nenhum Python 3.11 ou mais novo encontrado (tentados: py -3 e python).>&2
echo Instale pela Microsoft Store ou em python.org e rode de novo.>&2
exit /b 1

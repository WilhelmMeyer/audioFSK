@echo off
rem Monta o artigo no Windows. A logica esta em monta.py, o mesmo arquivo que
rem o monta.sh do Linux chama; aqui so' se escolhe o interpretador.
rem Uso, a partir da pasta do projeto:  artigo\monta.cmd --sem-figuras
setlocal
py -3 "%~dp0monta.py" %*
if %ERRORLEVEL% NEQ 9009 exit /b %ERRORLEVEL%
python "%~dp0monta.py" %*
exit /b %ERRORLEVEL%

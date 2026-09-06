"""Geracao de PDF a partir do docx montado, via LibreOffice ou Word."""

import os
import shutil
import subprocess
import sys
import tempfile
import urllib.parse

MOTOR_LIBREOFFICE = "libreoffice"
MOTOR_WORD = "word"

CAMINHOS_WINDOWS_SOFFICE = (
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
)

TIMEOUT_LIBREOFFICE = 180

# O padrao do LibreOffice reamostra imagem para 300 dpi e reencoda em JPEG, o
# que poe halo em torno de traco fino de grafico e de texto de eixo. O filtro
# abaixo desliga as duas coisas e mantem no PDF o pixel que veio do docx.
FILTRO_PDF = (
    "pdf:writer_pdf_Export:"
    '{"UseLosslessCompression":{"type":"boolean","value":true},'
    '"ReduceImageResolution":{"type":"boolean","value":false}}'
)

INSTALACAO = {
    "linux": "sudo apt install libreoffice",
    "win32": "winget install --id TheDocumentFoundation.LibreOffice",
    "darwin": "brew install --cask libreoffice",
}


def _no_windows():
    return sys.platform == "win32"


def _executavel_libreoffice():
    """Devolve o caminho do soffice, ou None se nao houver."""
    for nome in ("soffice", "libreoffice"):
        caminho = shutil.which(nome)
        if caminho:
            return caminho
    if _no_windows():
        for caminho in CAMINHOS_WINDOWS_SOFFICE:
            if os.path.isfile(caminho):
                return caminho
    return None


def _tem_word():
    """Word por COM so existe no Windows e so com o pywin32 instalado."""
    if not _no_windows():
        return False
    try:
        import win32com.client  # noqa: F401
    except Exception:
        return False
    return True


def motores_disponiveis():
    """Lista os motores de conversao presentes, em ordem de preferencia.

    No Windows o Word vem primeiro por reproduzir o layout do modelo com
    mais fidelidade; nos demais sistemas so ha LibreOffice.
    """
    motores = []
    if _tem_word():
        motores.append(MOTOR_WORD)
    if _executavel_libreoffice():
        motores.append(MOTOR_LIBREOFFICE)
    return motores


def _caminho_lock(caminho):
    """Lock que o soffice cria ao gravar: .~lock.<nome>#, ao lado do arquivo."""
    pasta, nome = os.path.split(os.path.abspath(caminho))
    return os.path.join(pasta, f".~lock.{nome}#")


def _limpa_lock_orfao(caminho):
    """Remove o lock do soffice deixado por uma conversao interrompida.

    O lock guarda a URI do perfil que o criou. Se esse perfil ainda existe, o
    arquivo esta mesmo aberto por alguem e o lock fica; se nao existe, o dono
    era um perfil temporario de uma conversao que morreu no meio, e sem
    remove-lo toda gravacao seguinte falha com Io Class:Abort Code:27.
    """
    lock = _caminho_lock(caminho)
    if not os.path.isfile(lock):
        return
    try:
        campos = open(lock, encoding="utf-8", errors="replace").read().split(",")
    except OSError:
        return
    campos = [c.strip().rstrip(";") for c in campos]
    perfil = next((c for c in campos if c.startswith("file://")), "")
    if perfil:
        local = urllib.parse.unquote(urllib.parse.urlparse(perfil).path)
        if os.path.exists(local):
            return
    try:
        os.remove(lock)
    except OSError:
        pass


def _pdf_padrao(docx_path):
    raiz, _ = os.path.splitext(docx_path)
    return raiz + ".pdf"


def _converte_libreoffice(docx_path, pdf_path):
    """Converte com o soffice headless e devolve o caminho do PDF."""
    soffice = _executavel_libreoffice()
    destino = os.path.dirname(os.path.abspath(pdf_path)) or "."
    saida_nativa = os.path.join(
        destino, os.path.splitext(os.path.basename(docx_path))[0] + ".pdf"
    )
    _limpa_lock_orfao(saida_nativa)
    _limpa_lock_orfao(pdf_path)
    with tempfile.TemporaryDirectory() as perfil:
        # Perfil proprio evita conflito com uma instancia do LibreOffice ja
        # aberta pelo usuario, que faz a conversao falhar em silencio.
        uri_perfil = "file:///" + os.path.abspath(perfil).lstrip("/").replace("\\", "/")
        comando = [
            soffice,
            "-env:UserInstallation=" + uri_perfil,
            "--headless",
            "--convert-to",
            FILTRO_PDF,
            "--outdir",
            destino,
            os.path.abspath(docx_path),
        ]
        proc = subprocess.run(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=TIMEOUT_LIBREOFFICE,
        )
    if proc.returncode != 0:
        erro = proc.stderr.decode("utf-8", "replace").strip()
        saida = proc.stdout.decode("utf-8", "replace").strip()
        recado = "Falha na conversao pelo LibreOffice: " + (erro or saida)
        if os.path.isfile(_caminho_lock(saida_nativa)):
            recado += (
                f"\nO PDF esta travado por {_caminho_lock(saida_nativa)}, "
                "provavelmente aberto no LibreOffice. Feche e rode de novo."
            )
        raise RuntimeError(recado)
    if not os.path.isfile(saida_nativa):
        raise RuntimeError("LibreOffice nao gerou o PDF em " + saida_nativa)
    # O soffice so escreve com o mesmo nome base do docx.
    if os.path.abspath(saida_nativa) != os.path.abspath(pdf_path):
        shutil.move(saida_nativa, pdf_path)
    return pdf_path


def _converte_word(docx_path, pdf_path):
    """Converte com o Word por COM e devolve o caminho do PDF."""
    import win32com.client

    origem = os.path.abspath(docx_path)
    destino = os.path.abspath(pdf_path)
    aplicacao = win32com.client.Dispatch("Word.Application")
    aplicacao.Visible = False
    documento = None
    try:
        documento = aplicacao.Documents.Open(origem)
        # FileFormat 17 e wdFormatPDF.
        documento.SaveAs2(destino, FileFormat=17)
    finally:
        if documento is not None:
            try:
                documento.Close(False)
            except Exception:
                pass
        try:
            aplicacao.Quit()
        except Exception:
            pass
    return destino


def gera_pdf(docx_path, pdf_path=None):
    """Converte o docx em PDF e devolve o caminho, ou None sem motor."""
    motores = motores_disponiveis()
    if not motores:
        return None
    if pdf_path is None:
        pdf_path = _pdf_padrao(docx_path)
    motor = motores[0]
    if motor == MOTOR_WORD:
        return _converte_word(docx_path, pdf_path)
    return _converte_libreoffice(docx_path, pdf_path)


def mensagem_sem_motor():
    """Texto de aviso quando nao ha motor de layout na maquina."""
    if sys.platform.startswith("win"):
        chave = "win32"
    elif sys.platform == "darwin":
        chave = "darwin"
    else:
        chave = "linux"
    return (
        "Nenhum motor de layout encontrado para gerar o PDF. "
        "O docx foi gerado normalmente e pode ser aberto no Word.\n"
        "Para gerar o PDF, instale o LibreOffice:\n"
        "  " + INSTALACAO[chave]
    )

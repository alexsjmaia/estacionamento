import os
import time
import unicodedata

try:
    import win32print
except ImportError:  # pragma: no cover - depende do Windows com pywin32
    win32print = None


PRINTER_NAME = os.getenv("PRINTER_NAME", "Elgin")
TICKET_WIDTH = 34
EXTRA_FEED_LINES = 10
AUTO_CUT = os.getenv("AUTO_CUT", "False").strip().lower() in {"1", "true", "sim", "yes"}


class PrinterError(Exception):
    pass


def _normalizar(texto):
    texto = (texto or "").upper()
    texto = unicodedata.normalize("NFKD", texto)
    texto = texto.encode("ascii", "ignore").decode("ascii")
    return texto


def _centralizar(texto):
    return _normalizar(texto).center(TICKET_WIDTH)


def _justificar(texto):
    return _normalizar(texto).ljust(TICKET_WIDTH)


def _quebrar_linhas(texto, largura=TICKET_WIDTH):
    palavras = _normalizar(texto).split()
    if not palavras:
        return [""]

    linhas = []
    linha_atual = palavras[0]

    for palavra in palavras[1:]:
        candidata = f"{linha_atual} {palavra}"
        if len(candidata) <= largura:
            linha_atual = candidata
        else:
            linhas.append(linha_atual)
            linha_atual = palavra

    linhas.append(linha_atual)
    return linhas


def _formatar_linha_tabela_compra(coluna_esquerda, coluna_direita):
    esquerda = _normalizar(coluna_esquerda)
    direita = _normalizar(coluna_direita)
    largura_esquerda = 19
    return f"{esquerda:<{largura_esquerda}}{direita}"


def _adicionar_linhas_bloco(buffer, linhas, alinhamento="left", negrito=False):
    for linha in linhas:
        if alinhamento == "center":
            buffer.extend(align_center())
            conteudo = _centralizar(linha)
        else:
            buffer.extend(align_left())
            conteudo = _justificar(linha)

        buffer.extend(bold_on() if negrito else bold_off())
        buffer.extend(text_line(conteudo))


def esc_init():
    return b"\x1b@"


def align_left():
    return b"\x1ba\x00"


def align_center():
    return b"\x1ba\x01"


def bold_on():
    return b"\x1bE\x01"


def bold_off():
    return b"\x1bE\x00"


def normal_size():
    return b"\x1d!\x00"


def medium_size():
    return b"\x1d!\x01"


def double_size():
    return b"\x1d!\x11"


def large_size():
    return b"\x1d!\x22"


def font_a():
    return b"\x1bM\x00"


def font_b():
    return b"\x1bM\x01"


def text_line(texto):
    return _normalizar(texto).encode("cp860", errors="ignore") + b"\n"


def cut():
    return b"\x1dV\x00"


def feed(lines=1):
    return b"\n" * max(lines, 0)


def build_receipt_bytes(comprovante):
    buffer = bytearray()
    buffer.extend(esc_init())
    buffer.extend(normal_size())

    linhas_cabecalho = [
        comprovante["empresa"]["nome"],
        comprovante["empresa"]["destaque"],
        comprovante["cliente"],
        comprovante["empresa"]["endereco"],
        comprovante["empresa"]["cep"],
        "",
        f"ENTRADA : {comprovante['entrada_id']}",
        comprovante["data_hora"],
        f"COMPROVANTE : {comprovante['comprovante_id']}",
        "",
    ]

    if comprovante.get("cabecalho_extra"):
        linhas_cabecalho.insert(0, comprovante["cabecalho_extra"])

    _adicionar_linhas_bloco(
        buffer,
        linhas_cabecalho,
        alinhamento="center",
    )

    buffer.extend(align_center())
    buffer.extend(bold_on())
    buffer.extend(double_size())
    buffer.extend(text_line(f"{comprovante['placa']} - {comprovante['modelo']}"))
    buffer.extend(normal_size())
    buffer.extend(bold_off())
    if comprovante.get("numero_prisma"):
        buffer.extend(align_center())
        buffer.extend(bold_on())
        buffer.extend(medium_size())
        buffer.extend(text_line(f"PRISMA: {comprovante['numero_prisma']}"))
        buffer.extend(normal_size())
        buffer.extend(bold_off())
    buffer.extend(feed(1))

    _adicionar_linhas_bloco(buffer, comprovante["aviso"], alinhamento="center")

    _adicionar_linhas_bloco(
        buffer,
        [
            "----------------------------------",
            "COMUNICADO",
            "AOS",
            "CLIENTES",
            "----------------------------------",
        ],
        alinhamento="center",
    )

    for linha in comprovante["comunicado"]:
        if linha:
            linha_normalizada = _normalizar(linha)
            tabela_beneficios = {
                "VALOR DA COMPRA  TEMPO EM BONUS": ("VALOR DA COMPRA", "TEMPO EM BONUS"),
                "R$ 30,00         1 H": ("R$ 30,00", "1 H"),
                "R$ 50,00         2 H": ("R$ 50,00", "2 H"),
                "R$ 100,00        3 H": ("R$ 100,00", "3 H"),
                "R$ 200,00        4 H": ("R$ 200,00", "4 H"),
            }

            if linha_normalizada in tabela_beneficios:
                esquerda, direita = tabela_beneficios[linha_normalizada]
                _adicionar_linhas_bloco(
                    buffer,
                    [_formatar_linha_tabela_compra(esquerda, direita)],
                    alinhamento="left",
                )
                continue

            _adicionar_linhas_bloco(
                buffer,
                _quebrar_linhas(linha, largura=TICKET_WIDTH),
                alinhamento="left",
            )
        else:
            buffer.extend(feed(1))

    buffer.extend(feed(EXTRA_FEED_LINES))
    if AUTO_CUT:
        buffer.extend(cut())
    return bytes(buffer)


def build_single_exit_receipt_bytes(comprovante, descricao_via):
    buffer = bytearray()
    buffer.extend(esc_init())
    buffer.extend(normal_size())

    prestador_nfse = comprovante.get("prestador_nfse", {})
    discriminacao = comprovante.get("discriminacao_nfse") or ""
    _adicionar_linhas_bloco(
        buffer,
        [
            descricao_via,
            "",
            "COMPROVANTE PROVISORIO",
            f"PRESTADOR: {prestador_nfse.get('razao_social', '')}" if prestador_nfse.get("razao_social") else "",
            f"CNPJ: {prestador_nfse.get('cnpj', '')}" if prestador_nfse.get("cnpj") else "",
            f"CCM: {prestador_nfse.get('ccm', '')}" if prestador_nfse.get("ccm") else "",
            "",
            comprovante.get("empresa", {}).get("endereco", ""),
            comprovante.get("empresa", {}).get("cep", ""),
            "",
            f"RPS: {comprovante['numero_rps']}" if comprovante.get("numero_rps") else "",
            f"STATUS NFS-E: {comprovante['mensagem_nfse']}" if comprovante.get("mensagem_nfse") else "",
            f"CODIGO VERIFICACAO: {comprovante['codigo_verificacao']}" if comprovante.get("codigo_verificacao") else "",
            "",
            "DISCRIMINACAO:" if discriminacao else "",
            "",
            "ESTACIONAMENTO VEICULO" if discriminacao else "",
            f"PLACA {comprovante['placa']} - NUMERO DA ENTRADA {comprovante['numero_entrada']}" if discriminacao else "",
            f"MARCA: {comprovante['marca']}" if comprovante.get("marca") else "",
            "",
            f"ENTRADA EM: {comprovante['data_hora_entrada']}",
            f"SAIDA EM: {comprovante['data_hora_saida']}",
            f"TEMPO: {comprovante['tempo_permanencia']}",
            "",
            f"VALOR COBRADO : R$ {comprovante['valor_cobrado']}",
            f"VALOR ISS: R$ {comprovante['valor_iss']}" if comprovante.get("valor_iss") else "",
        ],
        alinhamento="left",
    )

    buffer.extend(feed(EXTRA_FEED_LINES))
    if AUTO_CUT:
        buffer.extend(cut())
    return bytes(buffer)


def build_exit_receipt_bytes(comprovante):
    return build_single_exit_receipt_bytes(comprovante, "")


def build_nfse_avulsa_receipt_bytes(comprovante):
    buffer = bytearray()
    buffer.extend(esc_init())
    buffer.extend(normal_size())

    prestador_nfse = comprovante.get("prestador_nfse", {})
    linhas = [
        "ESTACIONAMENTO - SE MEGA PARK",
        "NFS-E AVULSA",
        "",
        f"RPS: {comprovante['numero_rps']}",
        f"NFS-E: {comprovante['numero_nfse']}" if comprovante.get("numero_nfse") else "",
        f"CODIGO VERIFICACAO: {comprovante['codigo_verificacao']}" if comprovante.get("codigo_verificacao") else "",
        f"DATA: {comprovante['data_emissao']}",
        f"PRESTADOR: {prestador_nfse.get('razao_social', '')}" if prestador_nfse.get("razao_social") else "",
        f"E-MAIL: {prestador_nfse.get('email', '')}" if prestador_nfse.get("email") else "",
        f"CNPJ: {prestador_nfse.get('cnpj', '')}" if prestador_nfse.get("cnpj") else "",
        f"CCM: {prestador_nfse.get('ccm', '')}" if prestador_nfse.get("ccm") else "",
        f"CPF/CNPJ TOMADOR: {comprovante['documento_tomador']}",
        "DISCRIMINACAO:",
        f"VALOR TOTAL: R$ {comprovante['valor_servicos']}",
        f"VALOR ISS: R$ {comprovante['valor_iss']}" if comprovante.get("valor_iss") else "",
    ]

    _adicionar_linhas_bloco(buffer, linhas, alinhamento="left")
    _adicionar_linhas_bloco(
        buffer,
        _quebrar_linhas(comprovante.get("discriminacao_nfse") or comprovante.get("observacao", ""), largura=TICKET_WIDTH),
        alinhamento="left",
    )
    if comprovante.get("mensagem_nfse"):
        buffer.extend(feed(1))
        _adicionar_linhas_bloco(
            buffer,
            _quebrar_linhas(f"STATUS NFS-E: {comprovante['mensagem_nfse']}", largura=TICKET_WIDTH),
            alinhamento="left",
        )

    buffer.extend(feed(EXTRA_FEED_LINES))
    if AUTO_CUT:
        buffer.extend(cut())
    return bytes(buffer)


def _send_raw_to_printer(data, document_name, printer_name=None):
    if win32print is None:
        raise PrinterError("PYWIN32 NAO ESTA INSTALADO. INSTALE COM: PIP INSTALL PYWIN32")

    printer_name = printer_name or PRINTER_NAME

    try:
        handle = win32print.OpenPrinter(printer_name)
    except Exception as exc:  # pragma: no cover - acesso real ao spooler
        raise PrinterError(f"NAO FOI POSSIVEL ABRIR A IMPRESSORA '{printer_name}': {exc}") from exc

    try:
        job = win32print.StartDocPrinter(handle, 1, (document_name, None, "RAW"))
        try:
            win32print.StartPagePrinter(handle)
            win32print.WritePrinter(handle, data)
            win32print.EndPagePrinter(handle)
        finally:
            win32print.EndDocPrinter(handle)
    except Exception as exc:  # pragma: no cover - acesso real ao spooler
        raise PrinterError(f"FALHA AO ENVIAR A IMPRESSAO PARA '{printer_name}': {exc}") from exc
    finally:
        win32print.ClosePrinter(handle)

    return job


def print_receipt(comprovante, printer_name=None):
    data = build_receipt_bytes(comprovante)
    return _send_raw_to_printer(data, "COMPROVANTE ESTACIONAMENTO", printer_name)


def print_exit_receipt(comprovante, printer_name=None):
    data = build_single_exit_receipt_bytes(comprovante, "")
    return _send_raw_to_printer(data, "COMPROVANTE SAIDA", printer_name)

import base64
import json
import os
import shutil
import subprocess
from wsgiref.simple_server import make_server, WSGIRequestHandler


HOST = "127.0.0.1"
PORT = int(os.getenv("PRINT_AGENT_PORT", "8951"))
DEFAULT_PRINTER = os.getenv("PRINT_AGENT_PRINTER", "Elgin")
DEFAULT_ENCODING = os.getenv("PRINT_AGENT_ENCODING", "cp860")


class PrintAgentError(Exception):
    pass


def _run_command(command, input_data=None):
    result = subprocess.run(
        command,
        input=input_data,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=isinstance(input_data, str),
    )
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        raise PrintAgentError(stderr or f"FALHA AO EXECUTAR: {' '.join(command)}")
    return result.stdout


def listar_impressoras():
    if shutil.which("lpstat"):
        output = _run_command(["lpstat", "-p"])
        printers = []
        for line in output.splitlines():
            line = line.strip()
            if line.startswith("printer "):
                parts = line.split()
                if len(parts) >= 2:
                    printers.append(parts[1])
        return sorted(printers)
    return []


def enviar_para_impressora(data, document_name, printer_name=None):
    printer_name = printer_name or DEFAULT_PRINTER
    if not shutil.which("lp"):
        raise PrintAgentError("COMANDO 'lp' NAO ENCONTRADO. INSTALE E CONFIGURE O CUPS.")

    result = subprocess.run(
        ["lp", "-d", printer_name, "-t", document_name, "-o", "raw"],
        input=data,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="ignore").strip() if result.stderr else ""
        raise PrintAgentError(stderr or f"NAO FOI POSSIVEL IMPRIMIR NA FILA {printer_name}.")

    stdout = result.stdout.decode("utf-8", errors="ignore").strip() if result.stdout else ""
    return stdout or "IMPRESSAO ENVIADA"


def responder_json(start_response, status_code, payload):
    body = json.dumps(payload).encode("utf-8")
    status_text = {
        200: "200 OK",
        400: "400 BAD REQUEST",
        404: "404 NOT FOUND",
        500: "500 INTERNAL SERVER ERROR",
    }.get(status_code, f"{status_code} OK")
    headers = [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(body))),
        ("Access-Control-Allow-Origin", "*"),
        ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
        ("Access-Control-Allow-Headers", "Content-Type"),
    ]
    start_response(status_text, headers)
    return [body]


def ler_json(environ):
    try:
        tamanho = int(environ.get("CONTENT_LENGTH", "0") or "0")
    except ValueError:
        tamanho = 0

    body = environ["wsgi.input"].read(tamanho) if tamanho > 0 else b"{}"
    if not body:
        return {}
    return json.loads(body.decode("utf-8"))


def app(environ, start_response):
    method = environ.get("REQUEST_METHOD", "GET").upper()
    path = environ.get("PATH_INFO", "/")

    try:
        if method == "OPTIONS":
            return responder_json(start_response, 200, {"ok": True})

        if method == "GET" and path == "/health":
            return responder_json(
                start_response,
                200,
                {
                    "ok": True,
                    "printer_default": DEFAULT_PRINTER,
                    "port": PORT,
                },
            )

        if method == "GET" and path == "/printers":
            return responder_json(start_response, 200, {"ok": True, "printers": listar_impressoras()})

        if method == "POST" and path == "/print-text":
            payload = ler_json(environ)
            content = payload.get("content", "")
            if not content:
                return responder_json(start_response, 400, {"ok": False, "message": "CONTENT OBRIGATORIO."})

            encoding = payload.get("encoding", DEFAULT_ENCODING)
            printer_name = payload.get("printer_name", DEFAULT_PRINTER)
            document_name = payload.get("document_name", "COMPROVANTE")
            data = content.encode(encoding, errors="ignore")
            job = enviar_para_impressora(data, document_name, printer_name)
            return responder_json(
                start_response,
                200,
                {"ok": True, "message": f"IMPRESSAO ENVIADA PARA {printer_name}.", "job": job},
            )

        if method == "POST" and path == "/print-base64":
            payload = ler_json(environ)
            data_base64 = payload.get("data_base64", "")
            if not data_base64:
                return responder_json(start_response, 400, {"ok": False, "message": "DATA_BASE64 OBRIGATORIO."})

            printer_name = payload.get("printer_name", DEFAULT_PRINTER)
            document_name = payload.get("document_name", "COMPROVANTE")
            data = base64.b64decode(data_base64)
            job = enviar_para_impressora(data, document_name, printer_name)
            return responder_json(
                start_response,
                200,
                {"ok": True, "message": f"IMPRESSAO ENVIADA PARA {printer_name}.", "job": job},
            )

        return responder_json(start_response, 404, {"ok": False, "message": "ROTA NAO ENCONTRADA."})
    except Exception as exc:
        return responder_json(start_response, 500, {"ok": False, "message": str(exc)})


class QuietRequestHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        return


def main():
    print(f"AGENTE DE IMPRESSAO LOCAL LINUX EM http://{HOST}:{PORT}")
    print(f"IMPRESSORA PADRAO: {DEFAULT_PRINTER}")
    print("ROTAS:")
    print("  GET  /health")
    print("  GET  /printers")
    print("  POST /print-text")
    print("  POST /print-base64")

    with make_server(HOST, PORT, app, handler_class=QuietRequestHandler) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()

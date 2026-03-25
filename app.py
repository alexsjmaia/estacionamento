import base64
import os
from pathlib import Path
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, jsonify, redirect, render_template, request, send_file, session, url_for

from backup_utils import BACKUP_DIR, BackupError, criar_backup_completo, restaurar_backup_completo
from nfse_signer import NfseSignerError

from database import (
    autenticar_usuario,
    atualizar_dados_nfse_veiculo,
    atualizar_cadastro_veiculo,
    buscar_codigo_marca,
    buscar_veiculo_por_placa,
    buscar_conciliacao_caixa,
    buscar_forma_pagamento,
    buscar_movimento_aberto_por_placa,
    buscar_movimento_aberto_por_numero_entrada,
    buscar_movimento_aberto_por_placa_e_numero,
    buscar_ultima_entrada_no_patio,
    buscar_ultima_entrada_no_patio_por_patio,
    cancelar_ultima_entrada,
    cadastrar_placa,
    cadastrar_usuario,
    consultar_estacionamento,
    consultar_fechamento_por_data,
    excluir_usuario,
    gerar_numero_entrada_diario,
    listar_formas_pagamento,
    listar_precos,
    listar_veiculos_no_patio,
    listar_usuarios,
    listar_codigos_marcas,
    listar_cadastros_veiculos,
    listar_fechamentos_caixa,
    obter_fechamento_caixa_por_data,
    obter_empresa_fiscal_ativa,
    obter_proximo_numero_rps,
    registrar_log_nfse,
    registrar_log_nfse_avulsa,
    registrar_saida_lote,
    salvar_fechamento_caixa_manual,
    atualizar_usuario,
    atualizar_preco,
    obter_resumo_sistema_fechamento,
    registrar_saida_veiculo,
    registrar_entrada_veiculo,
    salvar_fechamento_e_conciliacao_caixa,
    test_connection,
    veiculo_esta_no_patio,
)
from nfse import (
    NfseError,
    enviar_rps_sao_paulo,
    gerar_xml_rps,
    montar_dados_servico_avulso,
    montar_dados_servico_para_nfse,
)
from printer import (
    PRINTER_NAME,
    PrinterError,
    build_exit_receipt_bytes,
    build_nfse_avulsa_receipt_bytes,
    build_single_exit_receipt_bytes,
    build_receipt_bytes,
    print_exit_receipt,
    print_receipt,
)


app = Flask(__name__)
app.config["SECRET_KEY"] = "trocar-esta-chave-em-producao"
app.config["PRINTER_NAME"] = os.getenv("PRINTER_NAME", PRINTER_NAME)

MENU_OPCOES = [
    {"id": "entrada", "titulo": "Entrada de Veiculos"},
    {"id": "reimprime", "titulo": "Reimprime a ultima Entrada"},
    {"id": "cancela", "titulo": "Cancela ultima Entrada"},
    {"id": "saida", "titulo": "Saida de veiculos"},
    {"id": "consulta", "titulo": "Consulta Estacionamento"},
    {"id": "fechamento-caixa", "titulo": "Fechamento de caixa"},
    {"id": "lancamento-fechamento-caixa", "titulo": "Lanca fechamento caixa"},
    {"id": "saida-lote", "titulo": "Saida geral do patio"},
    {"id": "edita-veiculos", "titulo": "Edita Veiculos"},
    {"id": "nfse-avulsa", "titulo": "Nfs-e Avulsa"},
]

EMPRESA = {
    "nome": "ESTACIONAMENTO -",
    "destaque": "SE MEGA PARK",
    "convenio": "CONVENIO TEXTIL ABRIL",
    "endereco": "RUA RIO BONITO, 845",
    "cep": "CEP 03023-000",
}

AVISO_COMPROVANTE = [
    "INFORME O CUPOM FISCAL DA TEXTIL ABRIL",
    "AO CAIXA DO ESTACIONAMENTO.",
    "CASO NAO TENHA EFETUADO COMPRA NA TEXTIL ABRIL",
    "SERA COBRADO O ESTACIONAMENTO NORMALMENTE",
]

COMUNICADO_CLIENTES = [
    "TABELA DE BENEFICIOS",
    "CONVENIO COM A TEXTIL ABRIL",
    "",
    "NAS COMPRAS REALIZADAS NA TEXTIL ABRIL,",
    "O CLIENTE TERA DIREITO A SEGUINTE BONIFICACAO:",
    "",
    "VALOR DA COMPRA  TEMPO EM BONUS",
    "R$ 30,00         1 H",
    "R$ 50,00         2 H",
    "R$ 100,00        3 H",
    "R$ 200,00        4 H",
    "ACIMA DE R$ 300,00 ISENTO",
    "",
    "IMPORTANTE:",
    "COMPRAS ABAIXO DE R$ 30,00",
    "NAO DAO DIREITO A BONIFICACAO.",
    "NAO HA TRANSFERENCIA DE BONUS",
    "PARA OUTRO PERIODO.",
    "",
]


def login_obrigatorio(view):
    @wraps(view)
    def view_protegida(*args, **kwargs):
        if not session.get("usuario_logado"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return view_protegida


def usuario_eh_root():
    return (session.get("usuario_logado") or "").strip().lower() == "root"


def usuario_eh_admin():
    return (session.get("usuario_logado") or "").strip().lower() in {"root", "admin"}


def obter_empresa_usuario():
    return {
        "nome": EMPRESA["nome"],
        "destaque": EMPRESA["destaque"],
        "convenio": EMPRESA["convenio"],
        "endereco": (session.get("usuario_endereco") or EMPRESA["endereco"]).upper(),
        "cep": (session.get("usuario_cep") or EMPRESA["cep"]).upper(),
    }


@app.route("/", methods=["GET", "POST"])
def login():
    if session.get("usuario_logado"):
        return redirect(url_for("painel"))

    erro = None

    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "").strip()

        if not test_connection():
            erro = "NAO FOI POSSIVEL CONECTAR AO BANCO DE DADOS."
        else:
            usuario_autenticado = autenticar_usuario(usuario, senha)
            if usuario_autenticado:
                session["usuario_logado"] = usuario_autenticado["usuario"]
                session["usuario_endereco"] = usuario_autenticado.get("endereco") or EMPRESA["endereco"]
                session["usuario_cep"] = usuario_autenticado.get("cep") or EMPRESA["cep"]
                session["usuario_patio"] = usuario_autenticado.get("patio")
                return redirect(url_for("painel"))
            erro = "USUARIO OU SENHA INVALIDOS."

    return render_template("login.html", erro=erro)


@app.route("/painel")
@login_obrigatorio
def painel():
    opcoes_disponiveis = MENU_OPCOES
    if (session.get("usuario_logado") or "").strip().lower() == "admin":
        opcoes_disponiveis = [
            item
            for item in MENU_OPCOES
            if item["id"] not in {"entrada", "reimprime", "cancela", "saida", "lancamento-fechamento-caixa"}
        ]

    return render_template(
        "painel.html",
        usuario=session.get("usuario_logado"),
        opcoes=opcoes_disponiveis,
        banco_ok=test_connection(),
        exibir_acoes_admin=usuario_eh_admin(),
    )


def gerar_numero_comprovante():
    ultimo = session.get("sequencia_comprovante", 0) + 1
    session["sequencia_comprovante"] = ultimo
    return ultimo


def gerar_payload_impressao(data_bytes):
    return base64.b64encode(data_bytes).decode("ascii")


def obter_patio_usuario():
    patio = session.get("usuario_patio")
    return int(patio) if patio not in (None, "") else None


def forma_pagamento_eh_maquininha(descricao):
    return (descricao or "").strip().upper() in {"CARTAO", "CARTÃO", "MAQUININHA"}


def montar_dados_prestador_nfse():
    empresa_fiscal = obter_empresa_fiscal_ativa() or {}
    empresa_usuario = obter_empresa_usuario()
    aliquota_iss = float(empresa_fiscal.get("aliquota_iss") or 0)
    return {
        "razao_social": (empresa_fiscal.get("razao_social") or empresa_usuario.get("destaque") or "").upper(),
        "endereco": empresa_usuario.get("endereco", ""),
        "cep": empresa_usuario.get("cep", ""),
        "email": (empresa_fiscal.get("email") or "").upper(),
        "cnpj": formatar_documento_tomador(empresa_fiscal.get("cnpj") or ""),
        "ccm": (empresa_fiscal.get("ccm") or "").upper(),
        "aliquota_iss": aliquota_iss,
    }


def emitir_nfse_para_saida(movimento_saida):
    empresa_fiscal = obter_empresa_fiscal_ativa()
    if not empresa_fiscal:
        raise NfseError("PARAMETRIZACAO FISCAL DA EMPRESA NAO ENCONTRADA.")

    if not empresa_fiscal.get("codigo_servico"):
        raise NfseError("CODIGO DE SERVICO NAO CONFIGURADO NA TABELA EMPRESA_FISCAL.")

    if not empresa_fiscal.get("senha_web"):
        raise NfseError("SENHA WEB NAO CONFIGURADA NA TABELA EMPRESA_FISCAL.")

    dados_servico = montar_dados_servico_para_nfse(movimento_saida)
    xml_rps = gerar_xml_rps(empresa_fiscal, dados_servico)
    retorno = enviar_rps_sao_paulo(empresa_fiscal, xml_rps)
    xml_efetivo = retorno.get("xml_enviado") or xml_rps

    status_nfse = "EMITIDA" if retorno.get("numero_nfse") else "ERRO"
    atualizar_dados_nfse_veiculo(
        movimento_saida["id"],
        numero_nfse=retorno.get("numero_nfse"),
        codigo_verificacao=retorno.get("codigo_verificacao"),
        status_nfse=status_nfse,
        xml_rps=xml_efetivo,
        resposta_nfse=retorno.get("raw_response"),
    )
    registrar_log_nfse(
        movimento_saida["id"],
        movimento_saida["numero_rps"],
        xml_efetivo,
        retorno.get("raw_response"),
        status_nfse,
        retorno.get("erro"),
        retorno.get("numero_nfse"),
    )
    return retorno


def emitir_nfse_avulsa(documento_tomador, valor_servico, observacao_nf):
    empresa_fiscal = obter_empresa_fiscal_ativa()
    if not empresa_fiscal:
        raise NfseError("PARAMETRIZACAO FISCAL DA EMPRESA NAO ENCONTRADA.")

    if not empresa_fiscal.get("codigo_servico"):
        raise NfseError("CODIGO DE SERVICO NAO CONFIGURADO NA TABELA EMPRESA_FISCAL.")

    numero_rps = obter_proximo_numero_rps(empresa_fiscal.get("serie_rps") or "RPS")
    if not numero_rps:
        raise NfseError("NAO FOI POSSIVEL GERAR O PROXIMO NUMERO DO RPS.")

    dados_servico = montar_dados_servico_avulso(
        numero_rps,
        datetime.now(),
        documento_tomador,
        valor_servico,
        observacao_nf,
    )
    xml_rps = gerar_xml_rps(empresa_fiscal, dados_servico)
    try:
        retorno = enviar_rps_sao_paulo(empresa_fiscal, xml_rps)
    except Exception as exc:
        registrar_log_nfse_avulsa(
            numero_rps,
            documento_tomador,
            valor_servico,
            observacao_nf,
            xml_rps,
            str(exc),
            "ERRO",
            str(exc),
            None,
        )
        raise

    xml_efetivo = retorno.get("xml_enviado") or xml_rps
    status_nfse = "EMITIDA" if retorno.get("numero_nfse") else "ERRO"
    registrar_log_nfse_avulsa(
        numero_rps,
        documento_tomador,
        valor_servico,
        observacao_nf,
        xml_efetivo,
        retorno.get("raw_response"),
        status_nfse,
        retorno.get("erro"),
        retorno.get("numero_nfse"),
    )
    return {
        "numero_rps": numero_rps,
        "numero_nfse": retorno.get("numero_nfse"),
        "codigo_verificacao": retorno.get("codigo_verificacao"),
        "mensagem_nfse": retorno.get("erro") or (
            "NFS-E EMITIDA COM SUCESSO." if retorno.get("numero_nfse") else "NAO FOI POSSIVEL EMITIR A NFS-E."
        ),
        "xml_rps": xml_efetivo,
        "resposta_nfse": retorno.get("raw_response"),
    }


def formatar_data_hora_extenso(data_hora):
    dias_semana = {
        0: "SEGUNDA-FEIRA",
        1: "TERCA-FEIRA",
        2: "QUARTA-FEIRA",
        3: "QUINTA-FEIRA",
        4: "SEXTA-FEIRA",
        5: "SABADO",
        6: "DOMINGO",
    }
    meses = {
        1: "JANEIRO",
        2: "FEVEREIRO",
        3: "MARCO",
        4: "ABRIL",
        5: "MAIO",
        6: "JUNHO",
        7: "JULHO",
        8: "AGOSTO",
        9: "SETEMBRO",
        10: "OUTUBRO",
        11: "NOVEMBRO",
        12: "DEZEMBRO",
    }
    return (
        f"{dias_semana[data_hora.weekday()]}, "
        f"{data_hora.day:02d} DE {meses[data_hora.month]} DE {data_hora.year} "
        f"{data_hora.strftime('%H:%M:%S')}"
    )


def montar_comprovante(cadastro, agora, numero_prisma=""):
    numero_entrada = gerar_numero_entrada_diario(agora)
    if not numero_entrada:
        return None

    modelo_exibicao = cadastro.get("modelo") or cadastro.get("marca") or "NAO INFORMADO"

    return {
        "empresa": obter_empresa_usuario(),
        "entrada_id": numero_entrada,
        "data_hora": formatar_data_hora_extenso(agora),
        "comprovante_id": gerar_numero_comprovante(),
        "placa": cadastro["placa"].upper(),
        "modelo": modelo_exibicao.upper(),
        "numero_prisma": numero_prisma,
        "cliente": EMPRESA["convenio"].upper(),
        "aviso": AVISO_COMPROVANTE,
        "comunicado": COMUNICADO_CLIENTES,
    }


def processar_entrada(cadastro, numero_prisma=""):
    agora = datetime.now()
    comprovante = montar_comprovante(cadastro, agora, numero_prisma)
    if not comprovante:
        return None

    entrada_id = registrar_entrada_veiculo(
        cadastro["placa"],
        comprovante["entrada_id"],
        agora,
        obter_patio_usuario(),
    )
    if not entrada_id:
        return None

    comprovante["registro_id"] = entrada_id
    session["ultima_entrada"] = comprovante
    return comprovante


def montar_reimpressao_entrada(movimento):
    return {
        "empresa": obter_empresa_usuario(),
        "cabecalho_extra": "R E I M P R E S S A O",
        "entrada_id": movimento["numero_entrada"],
        "data_hora": formatar_data_hora_extenso(movimento["data_hora_entrada"]),
        "comprovante_id": movimento["id"],
        "placa": movimento["placa"],
        "modelo": movimento["marca"],
        "cliente": EMPRESA["convenio"].upper(),
        "aviso": AVISO_COMPROVANTE,
        "comunicado": COMUNICADO_CLIENTES,
    }


def formatar_tempo_permanencia(delta):
    total_segundos = int(delta.total_seconds())
    horas = total_segundos // 3600
    minutos = (total_segundos % 3600) // 60
    segundos = total_segundos % 60
    return f"{horas:02d}:{minutos:02d}:{segundos:02d}"


def aplicar_bonus_compra(delta, valor_compra):
    if valor_compra is None or valor_compra <= 0:
        return delta, 0, False

    if valor_compra > 200:
        return timedelta(0), 0, True

    bonus_horas = 0
    if valor_compra >= 200:
        bonus_horas = 4
    elif valor_compra >= 100:
        bonus_horas = 3
    elif valor_compra >= 50:
        bonus_horas = 2
    elif valor_compra >= 30:
        bonus_horas = 1

    delta_ajustado = max(delta - timedelta(hours=bonus_horas), timedelta(0))
    return delta_ajustado, bonus_horas, False


def calcular_valor_saida(delta):
    precos = listar_precos()
    if not precos:
        return None

    if delta.total_seconds() <= 0:
        return 0.0

    if delta < timedelta(minutes=16):
        return 0.0

    # Desconta a tolerancia geral de 15 minutos antes de aplicar a tabela.
    delta_cobranca = max(delta - timedelta(minutes=15), timedelta(0))
    if delta_cobranca.total_seconds() <= 0:
        return 0.0

    horas = delta_cobranca.total_seconds() / 3600
    acumulado = 0.0

    for item in precos:
        tipo = (item.get("tipo_valor") or "").upper()
        valor = float(item.get("valor") or 0)
        hora_final = item.get("hora_final")
        hora_final_float = float(hora_final) if hora_final is not None else None
        hora_inicial_float = float(item.get("hora_inicial") or 0)

        if tipo == "FIXO" and hora_final_float == 1.0 and horas <= 1:
            return round(valor, 2)

        if tipo == "ADICIONAL":
            acumulado += valor
            if hora_final_float is not None and horas <= hora_final_float:
                return round(10.0 + acumulado, 2)

        if tipo == "FIXO" and hora_final_float is None and horas > hora_inicial_float:
            return round(valor, 2)

    return 10.0


def formatar_moeda(valor):
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def normalizar_documento_tomador(documento):
    return "".join(ch for ch in (documento or "") if ch.isdigit())


def formatar_documento_tomador(documento):
    numeros = normalizar_documento_tomador(documento)
    if len(numeros) == 11:
        return f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:]}"
    if len(numeros) == 14:
        return f"{numeros[:2]}.{numeros[2:5]}.{numeros[5:8]}/{numeros[8:12]}-{numeros[12:]}"
    return documento or ""


def cpf_valido(cpf):
    cpf = normalizar_documento_tomador(cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = (soma * 10) % 11
    digito_1 = 0 if resto == 10 else resto
    if digito_1 != int(cpf[9]):
        return False

    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = (soma * 10) % 11
    digito_2 = 0 if resto == 10 else resto
    return digito_2 == int(cpf[10])


def cnpj_valido(cnpj):
    cnpj = normalizar_documento_tomador(cnpj)
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False

    pesos_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * pesos_1[i] for i in range(12))
    resto = soma % 11
    digito_1 = 0 if resto < 2 else 11 - resto
    if digito_1 != int(cnpj[12]):
        return False

    pesos_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * pesos_2[i] for i in range(13))
    resto = soma % 11
    digito_2 = 0 if resto < 2 else 11 - resto
    return digito_2 == int(cnpj[13])


def documento_tomador_valido(documento):
    numeros = normalizar_documento_tomador(documento)
    if not numeros:
        return True
    if len(numeros) == 11:
        return cpf_valido(numeros)
    if len(numeros) == 14:
        return cnpj_valido(numeros)
    return False


def parse_valor_monetario(texto):
    texto = (texto or "").strip()
    if not texto:
        return 0.0
    return float(texto.replace(".", "").replace(",", "."))


def normalizar_codigo_marca_digitado(texto):
    texto = (texto or "").strip()
    if not texto:
        return ""

    inicio = []
    for caractere in texto:
        if caractere.isdigit():
            inicio.append(caractere)
            continue
        break

    if inicio:
        return "".join(inicio)

    somente_numeros = "".join(ch for ch in texto if ch.isdigit())
    return somente_numeros[:3]


@app.route("/entrada", methods=["GET", "POST"])
@login_obrigatorio
def entrada_veiculo():
    erro = None
    placa = ""
    numero_prisma = ""
    cadastro = None
    exibir_cadastro = False
    codigos_marcas = []
    codigo_selecionado = ""
    patio_usuario = obter_patio_usuario()
    exibir_numero_prisma = patio_usuario == 1
    permitir_entrada = patio_usuario is not None
    codigos_marcas = listar_codigos_marcas() if permitir_entrada else []

    if not permitir_entrada:
        erro = "USUARIO SEM PATIO CADASTRADO. NAO E POSSIVEL DAR ENTRADA EM VEICULOS."

    if request.method == "POST" and permitir_entrada:
        placa = request.form.get("placa", "").strip().upper()
        numero_prisma = request.form.get("numero_prisma", "").strip()
        codigo_selecionado = normalizar_codigo_marca_digitado(request.form.get("codigo", ""))
        modo_cadastro = request.form.get("modo_cadastro", "") == "1"
        movimento_aberto = veiculo_esta_no_patio(placa)

        if exibir_numero_prisma and numero_prisma and not numero_prisma.isdigit():
            erro = "O NUMERO DO PRISMA DEVE CONTER APENAS NUMEROS."
            return render_template(
                "entrada.html",
                erro=erro,
                placa=placa,
                numero_prisma=numero_prisma,
                cadastro=cadastro,
                exibir_cadastro=exibir_cadastro,
                codigos_marcas=codigos_marcas,
                codigo_selecionado=codigo_selecionado,
                exibir_numero_prisma=exibir_numero_prisma,
                permitir_entrada=permitir_entrada,
            )

        if movimento_aberto:
            erro = "ESTE VEICULO AINDA ESTA NO PATIO E NAO POSSUI SAIDA REGISTRADA."
            return render_template(
                "entrada.html",
                erro=erro,
                placa=placa,
                numero_prisma=numero_prisma,
                cadastro=cadastro,
                exibir_cadastro=exibir_cadastro,
                codigos_marcas=codigos_marcas,
                codigo_selecionado=codigo_selecionado,
                exibir_numero_prisma=exibir_numero_prisma,
                permitir_entrada=permitir_entrada,
            )

        cadastro = buscar_veiculo_por_placa(placa)

        if cadastro:
            comprovante = processar_entrada(cadastro, numero_prisma)
            if not comprovante:
                erro = "NAO FOI POSSIVEL GRAVAR A ENTRADA DO VEICULO."
                return render_template(
                    "entrada.html",
                    erro=erro,
                    placa=placa,
                    numero_prisma=numero_prisma,
                    cadastro=cadastro,
                    exibir_cadastro=exibir_cadastro,
                    codigos_marcas=codigos_marcas,
                    codigo_selecionado=codigo_selecionado,
                    exibir_numero_prisma=exibir_numero_prisma,
                    permitir_entrada=permitir_entrada,
                )
            return render_template(
                "comprovante.html",
                comprovante=comprovante,
                printer_name=app.config["PRINTER_NAME"],
                print_payload=gerar_payload_impressao(build_receipt_bytes(comprovante)),
            )

        if modo_cadastro:
            if not codigo_selecionado:
                erro = "INFORME O CODIGO DA MARCA PARA CADASTRAR A PLACA."
                exibir_cadastro = True
            elif not codigo_selecionado.isdigit():
                erro = "O CODIGO DA MARCA DEVE CONTER APENAS NUMEROS."
                exibir_cadastro = True
            elif not buscar_codigo_marca(codigo_selecionado):
                erro = "CODIGO DA MARCA NAO ENCONTRADO."
                exibir_cadastro = True
            else:
                cadastro = cadastrar_placa(placa, codigo_selecionado)
                if cadastro:
                    comprovante = processar_entrada(cadastro, numero_prisma)
                    if not comprovante:
                        erro = "NAO FOI POSSIVEL GRAVAR A ENTRADA DO VEICULO."
                        exibir_cadastro = True
                        return render_template(
                            "entrada.html",
                            erro=erro,
                            placa=placa,
                            numero_prisma=numero_prisma,
                            cadastro=cadastro,
                            exibir_cadastro=exibir_cadastro,
                            codigos_marcas=codigos_marcas,
                            codigo_selecionado=codigo_selecionado,
                            exibir_numero_prisma=exibir_numero_prisma,
                            permitir_entrada=permitir_entrada,
                        )
                    return render_template(
                        "comprovante.html",
                        comprovante=comprovante,
                        printer_name=app.config["PRINTER_NAME"],
                        print_payload=gerar_payload_impressao(build_receipt_bytes(comprovante)),
                    )

                erro = "NAO FOI POSSIVEL CADASTRAR A PLACA INFORMADA."
                exibir_cadastro = True
        else:
            erro = "PLACA NAO CADASTRADA. INFORME O CODIGO DA MARCA ABAIXO PARA CADASTRAR E IMPRIMIR."
            exibir_cadastro = True

    return render_template(
        "entrada.html",
        erro=erro,
        placa=placa,
        numero_prisma=numero_prisma,
        cadastro=cadastro,
        exibir_cadastro=exibir_cadastro,
        codigos_marcas=codigos_marcas,
        codigo_selecionado=codigo_selecionado,
        exibir_numero_prisma=exibir_numero_prisma,
        permitir_entrada=permitir_entrada,
    )


@app.route("/saida", methods=["GET", "POST"])
@login_obrigatorio
def saida_veiculo():
    erro = None
    placa = ""
    numero_entrada = ""
    tipo_busca = "numero_entrada"
    movimento = None
    formas_pagamento = []
    forma_pagamento_id = ""
    dados_saida = None
    valor_recebido = ""
    valor_compra = ""
    cpf = ""
    troco = None
    exibir_valor_recebido = False

    if request.method == "POST":
        placa = request.form.get("placa", "").strip().upper()
        numero_entrada = request.form.get("numero_entrada", "").strip()
        tipo_busca = request.form.get("tipo_busca", "placa").strip().lower()
        forma_pagamento_id = request.form.get("forma_pagamento_id", "").strip()
        confirmar_saida = request.form.get("confirmar_saida", "") == "1"
        valor_recebido = request.form.get("valor_recebido", "").strip().replace(",", ".")
        valor_compra = request.form.get("valor_compra", "").strip().replace(",", ".")
        cpf = request.form.get("cpf", "").strip()

        if tipo_busca == "numero_entrada":
            if not numero_entrada:
                erro = "INFORME O NUMERO DA ENTRADA."
            else:
                movimento = buscar_movimento_aberto_por_numero_entrada(numero_entrada)
        else:
            if not placa:
                erro = "INFORME A PLACA."
            else:
                movimento = buscar_movimento_aberto_por_placa(placa)

        if not erro and not movimento:
            erro = "VEICULO NAO ENCONTRADO NO PATIO."
        elif not erro:
            placa = movimento["placa"]
            numero_entrada = movimento["numero_entrada"]
            agora = datetime.now()
            delta = agora - movimento["data_hora_entrada"]
            valor_compra_float = None
            if valor_compra:
                try:
                    valor_compra_float = float(valor_compra)
                except ValueError:
                    erro = "VALOR DA COMPRA INVALIDO."

            delta_cobranca = delta
            bonus_horas = 0
            isento = False
            if not erro:
                delta_cobranca, bonus_horas, isento = aplicar_bonus_compra(delta, valor_compra_float)

            valor_cobrado = 0.0 if isento else calcular_valor_saida(delta_cobranca) if not erro else None
            dados_saida = {
                "data_hora_saida": agora.strftime("%d/%m/%Y %H:%M:%S"),
                "tempo_permanencia": formatar_tempo_permanencia(delta),
                "valor_cobrado": f"{valor_cobrado:.2f}".replace(".", ",") if valor_cobrado is not None else None,
                "valor_compra": request.form.get("valor_compra", "").strip(),
                "bonus_horas": bonus_horas,
                "isento": isento,
            }

            if erro:
                formas_pagamento = listar_formas_pagamento() if confirmar_saida else []
            elif confirmar_saida:
                forma_pagamento = buscar_forma_pagamento(forma_pagamento_id)
                if valor_cobrado is None:
                    erro = "NAO FOI POSSIVEL CALCULAR O VALOR DA SAIDA."
                elif valor_cobrado > 0 and not forma_pagamento:
                    erro = "SELECIONE A FORMA DE PAGAMENTO."
                    formas_pagamento = listar_formas_pagamento()
                else:
                    if cpf and not documento_tomador_valido(cpf):
                        erro = "CPF OU CNPJ INVALIDO."
                        formas_pagamento = listar_formas_pagamento()

                    descricao_pagamento = forma_pagamento["descricao"] if forma_pagamento else None
                    exibir_valor_recebido = descricao_pagamento == "DINHEIRO"
                    if descricao_pagamento == "DINHEIRO" and valor_recebido:
                        try:
                            valor_recebido_float = float(valor_recebido)
                            troco = round(valor_recebido_float - valor_cobrado, 2)
                        except ValueError:
                            erro = "VALOR RECEBIDO INVALIDO."
                            formas_pagamento = listar_formas_pagamento()

                    if erro:
                        return render_template(
                            "saida.html",
                            erro=erro,
                            placa=placa,
                            numero_entrada=numero_entrada,
                            tipo_busca=tipo_busca,
                            movimento=movimento,
                            formas_pagamento=formas_pagamento,
                            forma_pagamento_id=forma_pagamento_id,
                            dados_saida=dados_saida,
                            mensagem_sucesso=None,
                            valor_recebido=request.form.get("valor_recebido", "").strip(),
                            valor_compra=request.form.get("valor_compra", "").strip(),
                            cpf=request.form.get("cpf", "").strip(),
                            troco=None,
                            exibir_valor_recebido=exibir_valor_recebido,
                            formatar_documento_tomador=formatar_documento_tomador,
                        )

                    resultado_saida = registrar_saida_veiculo(
                        movimento["id"],
                        agora,
                        dados_saida["tempo_permanencia"],
                        valor_cobrado,
                        descricao_pagamento,
                        normalizar_documento_tomador(cpf) or None,
                    )
                    if resultado_saida and resultado_saida is not False:
                        numero_rps = resultado_saida.get("numero_rps")
                        retorno_nfse = None
                        mensagem_nfse = None
                        status_nfse = None

                        emitir_nfse = valor_cobrado > 0 and (bool(cpf) or forma_pagamento_eh_maquininha(descricao_pagamento))

                        if emitir_nfse:
                            try:
                                retorno_nfse = emitir_nfse_para_saida(
                                    {
                                        "id": movimento["id"],
                                        "numero_entrada": movimento["numero_entrada"],
                                        "numero_rps": numero_rps,
                                        "placa": movimento["placa"],
                                        "tempo_permanencia": dados_saida["tempo_permanencia"],
                                        "valor_cobrado": valor_cobrado,
                                        "cpf": normalizar_documento_tomador(cpf),
                                        "forma_pagamento": descricao_pagamento,
                                        "data_hora_saida": agora,
                                    }
                                )
                                status_nfse = "EMITIDA" if retorno_nfse.get("numero_nfse") else "ERRO"
                                mensagem_nfse = (
                                    f"NFS-E EMITIDA COM NUMERO {retorno_nfse['numero_nfse']}."
                                    if retorno_nfse.get("numero_nfse")
                                    else (retorno_nfse.get("erro") or "NAO FOI POSSIVEL EMITIR A NFS-E.")
                                )
                            except Exception as exc:
                                status_nfse = "ERRO"
                                mensagem_nfse = str(exc)
                                atualizar_dados_nfse_veiculo(
                                    movimento["id"],
                                    status_nfse=status_nfse,
                                    resposta_nfse=mensagem_nfse,
                                )
                                registrar_log_nfse(
                                    movimento["id"],
                                    numero_rps,
                                    None,
                                    mensagem_nfse,
                                    status_nfse,
                                    mensagem_nfse,
                                    None,
                                )

                        if valor_cobrado > 0:
                            prestador_nfse = montar_dados_prestador_nfse()
                            valor_iss = valor_cobrado * (prestador_nfse.get("aliquota_iss", 0) / 100)
                            discriminacao_nfse = (
                                f"ESTACIONAMENTO VEICULO PLACA {movimento['placa']} - "
                                f"ENTRADA {movimento['numero_entrada']} - "
                                f"TEMPO {dados_saida['tempo_permanencia']}"
                            )
                            session["ultima_saida"] = {
                                "empresa": obter_empresa_usuario(),
                                "numero_entrada": movimento["numero_entrada"],
                                "numero_rps": numero_rps,
                                "placa": movimento["placa"],
                                "marca": movimento["marca"],
                                "data_hora_entrada": movimento["data_hora_entrada"].strftime("%d/%m/%Y %H:%M:%S"),
                                "data_hora_saida": dados_saida["data_hora_saida"],
                                "tempo_permanencia": dados_saida["tempo_permanencia"],
                                "valor_cobrado": dados_saida["valor_cobrado"],
                                "cpf": formatar_documento_tomador(cpf) if cpf else "",
                                "status_nfse": status_nfse,
                                "mensagem_nfse": mensagem_nfse,
                                "numero_nfse": retorno_nfse.get("numero_nfse") if retorno_nfse else None,
                                "codigo_verificacao": retorno_nfse.get("codigo_verificacao") if retorno_nfse else None,
                                "prestador_nfse": prestador_nfse,
                                "documento_tomador": formatar_documento_tomador(cpf) if cpf else "",
                                "discriminacao_nfse": discriminacao_nfse,
                                "valor_iss": formatar_moeda(valor_iss),
                            }
                            return render_template(
                                "saida_comprovante.html",
                                printer_name=app.config["PRINTER_NAME"],
                                comprovante=session["ultima_saida"],
                                print_payload_saida=gerar_payload_impressao(
                                    build_single_exit_receipt_bytes(session["ultima_saida"], "CLIENTE - 1A VIA")
                                ),
                                print_payload_saida_estabelecimento=gerar_payload_impressao(
                                    build_single_exit_receipt_bytes(session["ultima_saida"], "ESTABELECIMENTO - 2A VIA")
                                ),
                            )

                        return render_template(
                            "saida.html",
                            erro=None,
                            placa="",
                            numero_entrada="",
                            tipo_busca="placa",
                            movimento=None,
                            formas_pagamento=[],
                            forma_pagamento_id="",
                            dados_saida=None,
                            mensagem_sucesso="SAIDA REGISTRADA COM SUCESSO.",
                            valor_recebido="",
                            valor_compra="",
                            cpf="",
                            troco=None,
                            exibir_valor_recebido=False,
                            formatar_documento_tomador=formatar_documento_tomador,
                        )

                    erro = "NAO FOI POSSIVEL REGISTRAR A SAIDA DO VEICULO."
                    formas_pagamento = listar_formas_pagamento()
            else:
                formas_pagamento = listar_formas_pagamento()
                forma_pagamento = buscar_forma_pagamento(forma_pagamento_id) if forma_pagamento_id else None
                exibir_valor_recebido = bool(forma_pagamento and forma_pagamento["descricao"] == "DINHEIRO")

    return render_template(
        "saida.html",
        erro=erro,
        placa=placa,
        numero_entrada=numero_entrada,
        tipo_busca=tipo_busca,
        movimento=movimento,
        formas_pagamento=formas_pagamento,
        forma_pagamento_id=forma_pagamento_id,
        dados_saida=dados_saida,
        mensagem_sucesso=None,
        valor_recebido=request.form.get("valor_recebido", "").strip() if request.method == "POST" else "",
        valor_compra=request.form.get("valor_compra", "").strip() if request.method == "POST" else "",
        cpf=request.form.get("cpf", "").strip() if request.method == "POST" else "",
        troco=troco,
        exibir_valor_recebido=exibir_valor_recebido,
        formatar_documento_tomador=formatar_documento_tomador,
    )


@app.route("/imprimir/ultima-entrada", methods=["POST"])
@login_obrigatorio
def imprimir_ultima_entrada():
    comprovante = session.get("ultima_entrada")
    if not comprovante:
        return jsonify({"ok": False, "mensagem": "NAO EXISTE ULTIMA ENTRADA PARA IMPRIMIR."}), 404

    try:
        print_receipt(comprovante, app.config["PRINTER_NAME"])
    except PrinterError as erro:
        return jsonify({"ok": False, "mensagem": str(erro)}), 500

    return jsonify(
        {
            "ok": True,
            "mensagem": f"IMPRESSAO ENVIADA PARA {app.config['PRINTER_NAME']}.",
            "redirect_url": url_for("entrada_veiculo"),
        }
    )


@app.route("/reimpressao-ultima-entrada")
@login_obrigatorio
def reimpressao_ultima_entrada():
    movimento = buscar_ultima_entrada_no_patio_por_patio(obter_patio_usuario())
    if not movimento:
        return render_template(
            "acao.html",
            opcao={"titulo": "REIMPRIME A ULTIMA ENTRADA"},
            mensagem_erro="NAO EXISTE ULTIMA ENTRADA DO SEU PATIO PARA REIMPRIMIR OU O VEICULO JA SAIU DO PATIO.",
        )

    comprovante = montar_reimpressao_entrada(movimento)
    session["ultima_entrada"] = comprovante
    return render_template(
        "reimpressao.html",
        printer_name=app.config["PRINTER_NAME"],
        comprovante=comprovante,
        print_payload=gerar_payload_impressao(build_receipt_bytes(comprovante)),
    )


@app.route("/cancelar-ultima-entrada", methods=["GET", "POST"])
@login_obrigatorio
def cancelar_ultima_entrada_view():
    movimento = buscar_ultima_entrada_no_patio()
    if not movimento:
        return render_template(
            "cancelamento.html",
            sucesso=False,
            mensagem="NAO EXISTE ULTIMA ENTRADA EM ABERTO PARA CANCELAR.",
            movimento=None,
            exigir_confirmacao=False,
        )

    agora = datetime.now()
    limite_cancelamento = movimento["data_hora_entrada"] + timedelta(minutes=15)
    if agora > limite_cancelamento:
        return render_template(
            "cancelamento.html",
            sucesso=False,
            mensagem="A ULTIMA ENTRADA NAO PODE MAIS SER CANCELADA. O LIMITE DE 15 MINUTOS FOI ULTRAPASSADO.",
            movimento=movimento,
            exigir_confirmacao=False,
        )

    if request.method == "GET":
        return render_template(
            "cancelamento.html",
            sucesso=False,
            mensagem="CONFIRME O CANCELAMENTO DA ULTIMA ENTRADA.",
            movimento=movimento,
            exigir_confirmacao=True,
        )

    confirmacao = (request.form.get("confirmacao") or "").strip().upper()
    if confirmacao == "NAO":
        return redirect(url_for("painel"))

    if confirmacao != "SIM":
        return render_template(
            "cancelamento.html",
            sucesso=False,
            mensagem="SELECIONE SIM OU NAO PARA CONTINUAR.",
            movimento=movimento,
            exigir_confirmacao=True,
        )

    sucesso = cancelar_ultima_entrada(movimento["id"])
    if not sucesso:
        return render_template(
            "cancelamento.html",
            sucesso=False,
            mensagem="NAO FOI POSSIVEL CANCELAR A ULTIMA ENTRADA.",
            movimento=movimento,
            exigir_confirmacao=False,
        )

    return render_template(
        "cancelamento.html",
        sucesso=True,
        mensagem="A ULTIMA ENTRADA FOI CANCELADA COM SUCESSO.",
        movimento=movimento,
        exigir_confirmacao=False,
    )


@app.route("/consulta", methods=["GET", "POST"])
@login_obrigatorio
def consulta_estacionamento():
    agora = datetime.now()
    data_inicial = agora.strftime("%Y-%m-%d")
    data_final = agora.strftime("%Y-%m-%d")
    erro = None
    resultado = None
    veiculos_no_patio = []
    patio_usuario = session.get("usuario_patio")
    try:
        patio_usuario = int(patio_usuario) if patio_usuario not in (None, "") else None
    except (TypeError, ValueError):
        patio_usuario = None

    if request.method == "POST":
        data_inicial = request.form.get("data_inicial", "").strip()
        data_final = request.form.get("data_final", "").strip()

        if not data_inicial or not data_final:
            erro = "INFORME A DATA INICIAL E A DATA FINAL."
        else:
            inicio = datetime.strptime(data_inicial, "%Y-%m-%d")
            fim = datetime.strptime(data_final, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            consulta = consultar_estacionamento(inicio, fim)
            if consulta is None:
                erro = "NAO FOI POSSIVEL CONSULTAR O ESTACIONAMENTO."
            else:
                patios = consulta.get("patios", {})
                resultado = {
                    "total_entradas": consulta["total_entradas"],
                    "total_no_patio": consulta["total_no_patio"],
                    "faturamento_total": formatar_moeda(consulta["faturamento_total"]),
                    "patio_1": {
                        "total_entradas": patios.get(1, {}).get("total_entradas", 0),
                        "total_no_patio": patios.get(1, {}).get("total_no_patio", 0),
                        "faturamento_total": formatar_moeda(patios.get(1, {}).get("faturamento_total", 0)),
                    },
                    "patio_2": {
                        "total_entradas": patios.get(2, {}).get("total_entradas", 0),
                        "total_no_patio": patios.get(2, {}).get("total_no_patio", 0),
                        "faturamento_total": formatar_moeda(patios.get(2, {}).get("faturamento_total", 0)),
                    },
                }
                if patio_usuario in (1, 2):
                    veiculos_no_patio = [
                        {
                            "numero_entrada": item["numero_entrada"],
                            "placa": item["placa"],
                            "patio": int(item.get("patio") or 0),
                            "marca": item["marca"],
                            "data_hora_entrada": item["data_hora_entrada"].strftime("%d/%m/%Y %H:%M:%S"),
                        }
                        for item in listar_veiculos_no_patio()
                        if int(item.get("patio") or 0) == patio_usuario
                    ]

    return render_template(
        "consulta.html",
        data_inicial=data_inicial,
        data_final=data_final,
        erro=erro,
        resultado=resultado,
        patio_usuario=patio_usuario,
        veiculos_no_patio=veiculos_no_patio,
    )


@app.route("/fechamento-caixa", methods=["GET", "POST"])
@login_obrigatorio
def fechamento_caixa():
    data_referencia = datetime.now().strftime("%Y-%m-%d")
    erro = None
    resultado = None
    patio_usuario = obter_patio_usuario()
    patio = str(patio_usuario or "")

    if request.method == "POST":
        data_referencia = request.form.get("data_referencia", "").strip() or data_referencia
        patio = request.form.get("patio", "").strip() or patio

        if not data_referencia or not patio:
            erro = "INFORME A DATA DO FECHAMENTO E O PATIO."
        else:
            consulta = consultar_fechamento_por_data(data_referencia, int(patio))
            if consulta is None:
                erro = "NAO FOI POSSIVEL CONSULTAR OS LANCAMENTOS DA DATA INFORMADA."
            else:
                totais_consulta = {"CARTAO": 0.0, "DINHEIRO": 0.0}
                totais = []
                for item in consulta["totais"]:
                    forma_pagamento = item["forma_pagamento"]
                    bucket_pagamento = "CARTAO" if forma_pagamento_eh_maquininha(forma_pagamento) else forma_pagamento
                    total_item = float(item["total"] or 0)
                    if bucket_pagamento in totais_consulta:
                        totais_consulta[bucket_pagamento] += total_item
                    totais.append(
                        {
                            "forma_pagamento": "MAQUININHA" if forma_pagamento_eh_maquininha(forma_pagamento) else forma_pagamento,
                            "total": formatar_moeda(total_item),
                        }
                    )

                fechamento_salvo = obter_fechamento_caixa_por_data(data_referencia, int(patio))
                if fechamento_salvo:
                    fechamento_salvo = dict(fechamento_salvo)
                diferencas = None
                if fechamento_salvo:
                    fechamento_troco_inicial = float(fechamento_salvo["troco_inicial"] or 0)
                    fechamento_maquininha = float(fechamento_salvo["maquininha"] or 0)
                    fechamento_dinheiro = float(fechamento_salvo["dinheiro"] or 0)
                    totais_troco_inicial = float((fechamento_salvo or {}).get("troco_inicial") or 0)
                    diferencas = {
                        "troco_inicial": formatar_moeda(fechamento_troco_inicial - totais_troco_inicial),
                        "maquininha": formatar_moeda(fechamento_maquininha - totais_consulta["CARTAO"]),
                        "dinheiro": formatar_moeda(fechamento_dinheiro - totais_consulta["DINHEIRO"]),
                        "troco_inicial_negativo": (fechamento_troco_inicial - totais_troco_inicial) < 0,
                        "maquininha_negativo": (fechamento_maquininha - totais_consulta["CARTAO"]) < 0,
                        "dinheiro_negativo": (fechamento_dinheiro - totais_consulta["DINHEIRO"]) < 0,
                    }
                    total_diferenca_caixa = (
                        (fechamento_troco_inicial - totais_troco_inicial)
                        + (fechamento_maquininha - totais_consulta["CARTAO"])
                        + (fechamento_dinheiro - totais_consulta["DINHEIRO"])
                    )
                    diferencas["total_caixa"] = formatar_moeda(total_diferenca_caixa)
                    diferencas["total_caixa_negativo"] = total_diferenca_caixa < 0

                resultado = {
                    "totais": totais,
                    "total_geral": formatar_moeda(float(consulta["total_geral"] or 0)),
                    "totais_layout": {
                        "troco_inicial": formatar_moeda(float((fechamento_salvo or {}).get("troco_inicial") or 0)),
                        "maquininha": formatar_moeda(totais_consulta["CARTAO"]),
                        "dinheiro": formatar_moeda(totais_consulta["DINHEIRO"]),
                        "total_geral": formatar_moeda(float(consulta["total_geral"] or 0)),
                    },
                    "fechamento_salvo": fechamento_salvo,
                    "diferencas": diferencas,
                }

    return render_template(
        "fechamento_caixa.html",
        erro=erro,
        data_referencia=data_referencia,
        resultado=resultado,
        patio=patio,
        patio_usuario=patio_usuario,
    )


@app.route("/lancamento-fechamento-caixa", methods=["GET", "POST"])
@login_obrigatorio
def lancamento_fechamento_caixa():
    data_referencia = datetime.now().strftime("%Y-%m-%d")
    erro = None
    mensagem_sucesso = None
    patio_usuario = obter_patio_usuario()
    patio = str(patio_usuario or "")
    valores = {
        "troco_inicial": "",
        "maquininha": "",
        "dinheiro": "",
    }

    registro_atual = obter_fechamento_caixa_por_data(data_referencia, int(patio)) if patio else None
    if registro_atual:
        valores = {
            "troco_inicial": formatar_moeda(float(registro_atual["troco_inicial"] or 0)),
            "maquininha": formatar_moeda(float(registro_atual["maquininha"] or 0)),
            "dinheiro": formatar_moeda(float(registro_atual["dinheiro"] or 0)),
        }

    if request.method == "POST":
        if patio_usuario in (1, 2):
            patio = str(patio_usuario)
        else:
            patio = request.form.get("patio", "").strip() or patio
        valores = {
            "troco_inicial": request.form.get("troco_inicial", "").strip(),
            "maquininha": request.form.get("maquininha", "").strip(),
            "dinheiro": request.form.get("dinheiro", "").strip(),
        }

        try:
            patio_int = int(patio)
            troco_inicial = parse_valor_monetario(valores["troco_inicial"])
            maquininha = parse_valor_monetario(valores["maquininha"])
            dinheiro = parse_valor_monetario(valores["dinheiro"])
        except ValueError:
            erro = "PREENCHA O PATIO E TODOS OS VALORES COM NUMEROS VALIDOS."
        else:
            if salvar_fechamento_caixa_manual(
                data_referencia,
                patio_int,
                troco_inicial,
                maquininha,
                dinheiro,
            ):
                mensagem_sucesso = "LANCAMENTO DO FECHAMENTO DE CAIXA GRAVADO COM SUCESSO."
            else:
                erro = "NAO FOI POSSIVEL GRAVAR O LANCAMENTO DO FECHAMENTO DE CAIXA."

    return render_template(
        "lancamento_fechamento_caixa.html",
        data_referencia=datetime.strptime(data_referencia, "%Y-%m-%d").strftime("%d/%m/%Y"),
        erro=erro,
        mensagem_sucesso=mensagem_sucesso,
        valores=valores,
        patio=patio,
        patio_usuario=patio_usuario,
    )


@app.route("/lista-fechamento-caixa", methods=["GET", "POST"])
@login_obrigatorio
def lista_fechamento_caixa():
    hoje = datetime.now().strftime("%Y-%m-%d")
    patio_usuario = obter_patio_usuario()
    data_inicial = hoje
    data_final = hoje
    patio = str(patio_usuario or "")
    erro = None
    lancamentos = []

    if request.method == "POST":
        data_inicial = request.form.get("data_inicial", "").strip() or hoje
        data_final = request.form.get("data_final", "").strip() or hoje
        patio = request.form.get("patio", "").strip() or patio

    if not patio:
        erro = "INFORME O NUMERO DO PATIO."
    else:
        registros = listar_fechamentos_caixa(data_inicial, data_final, int(patio))
        for item in registros:
            sis_troco_inicial = float(item["sis_troco_inicial"] or 0)
            troco_inicial = float(item["troco_inicial"] or 0)
            retirada_dinheiro = float(item["retirada_de_dinheiro"] or 0)
            sis_dinheiro = float(item["sis_pagamentos_dinheiro"] or 0)
            sis_pix = float(item["sis_pagamentos_pix"] or 0)
            sis_cartao = float(item["sis_pagamentos_cartao"] or 0)
            sis_troco_final = sis_troco_inicial + sis_dinheiro - retirada_dinheiro
            pdv_dinheiro = float(item["pdv_pagamentos_dinheiro"] or 0)
            pdv_pix = float(item["pdv_pagamentos_pix"] or 0)
            pdv_cartao = float(item["pdv_pagamentos_cartao"] or 0)
            pdv_troco_final = float(item["pdv_troco_final"] or 0)
            lancamentos.append(
                {
                    "data_referencia": item["data_referencia"].strftime("%d/%m/%Y"),
                    "patio": item["pdv_numero_do_patio"],
                    "sis_troco_inicial": formatar_moeda(sis_troco_inicial),
                    "troco_inicial": formatar_moeda(troco_inicial),
                    "retirada_de_dinheiro": formatar_moeda(retirada_dinheiro),
                    "sis_retirada_de_dinheiro": formatar_moeda(retirada_dinheiro),
                    "sis_pagamentos_dinheiro": formatar_moeda(sis_dinheiro),
                    "sis_pagamentos_pix": formatar_moeda(sis_pix),
                    "sis_pagamentos_cartao": formatar_moeda(sis_cartao),
                    "sis_troco_final": formatar_moeda(sis_troco_final),
                    "pdv_retirada_de_dinheiro": formatar_moeda(retirada_dinheiro),
                    "pdv_pagamentos_dinheiro": formatar_moeda(pdv_dinheiro),
                    "pdv_pagamentos_pix": formatar_moeda(pdv_pix),
                    "pdv_pagamentos_cartao": formatar_moeda(pdv_cartao),
                    "pdv_troco_final": formatar_moeda(pdv_troco_final),
                    "dif_troco_inicial": formatar_moeda(troco_inicial - sis_troco_inicial),
                    "dif_retirada_de_dinheiro": formatar_moeda(0),
                    "dif_dinheiro": formatar_moeda(pdv_dinheiro - sis_dinheiro),
                    "dif_pix": formatar_moeda(pdv_pix - sis_pix),
                    "dif_cartao": formatar_moeda(pdv_cartao - sis_cartao),
                    "dif_troco_final": formatar_moeda(pdv_troco_final - sis_troco_final),
                    "sis_troco_inicial_negativo": sis_troco_inicial < 0,
                    "sis_retirada_de_dinheiro_negativo": retirada_dinheiro < 0,
                    "sis_pagamentos_dinheiro_negativo": sis_dinheiro < 0,
                    "sis_pagamentos_pix_negativo": sis_pix < 0,
                    "sis_pagamentos_cartao_negativo": sis_cartao < 0,
                    "sis_troco_final_negativo": sis_troco_final < 0,
                    "pdv_troco_inicial_negativo": troco_inicial < 0,
                    "pdv_retirada_de_dinheiro_negativo": retirada_dinheiro < 0,
                    "pdv_pagamentos_dinheiro_negativo": pdv_dinheiro < 0,
                    "pdv_pagamentos_pix_negativo": pdv_pix < 0,
                    "pdv_pagamentos_cartao_negativo": pdv_cartao < 0,
                    "pdv_troco_final_negativo": pdv_troco_final < 0,
                    "dif_troco_inicial_negativo": (troco_inicial - sis_troco_inicial) < 0,
                    "dif_retirada_de_dinheiro_negativo": False,
                    "dif_dinheiro_negativo": (pdv_dinheiro - sis_dinheiro) < 0,
                    "dif_pix_negativo": (pdv_pix - sis_pix) < 0,
                    "dif_cartao_negativo": (pdv_cartao - sis_cartao) < 0,
                    "dif_troco_final_negativo": (pdv_troco_final - sis_troco_final) < 0,
                    "atualizado_em": item["atualizado_em"].strftime("%d/%m/%Y %H:%M:%S"),
                }
            )

    return render_template(
        "lista_fechamento_caixa.html",
        erro=erro,
        data_inicial=data_inicial,
        data_final=data_final,
        patio=patio,
        patio_usuario=patio_usuario,
        usuario_eh_root=usuario_eh_root(),
        lancamentos=lancamentos,
    )


@app.route("/precos", methods=["GET", "POST"])
@login_obrigatorio
def cadastra_precos():
    if not usuario_eh_root():
        return render_template(
            "acao.html",
            opcao={"titulo": "CADASTRA PRECOS"},
            mensagem_erro="SOMENTE O USUARIO ROOT PODE ACESSAR ESTE MODULO.",
        )

    erro = None
    mensagem_sucesso = None

    if request.method == "POST":
        preco_id = request.form.get("preco_id", "").strip()
        valor = request.form.get("valor", "").strip().replace(".", "").replace(",", ".")

        try:
            valor_float = float(valor)
        except ValueError:
            valor_float = None

        if not preco_id or valor_float is None:
            erro = "INFORME UM VALOR VALIDO PARA ATUALIZAR O PRECO."
        elif atualizar_preco(preco_id, valor_float):
            mensagem_sucesso = "PRECO ATUALIZADO COM SUCESSO."
        else:
            erro = "NAO FOI POSSIVEL ATUALIZAR O PRECO."

    precos = listar_precos()
    for item in precos:
        item["valor_formatado"] = formatar_moeda(float(item["valor"]))
        item["hora_final_exibicao"] = item["hora_final"] if item["hora_final"] is not None else "LIVRE"

    return render_template(
        "precos.html",
        precos=precos,
        erro=erro,
        mensagem_sucesso=mensagem_sucesso,
    )


@app.route("/usuarios", methods=["GET", "POST"])
@login_obrigatorio
def cadastra_usuarios():
    if not usuario_eh_root():
        return render_template(
            "acao.html",
            opcao={"titulo": "CADASTRA USUARIOS"},
            mensagem_erro="SOMENTE O USUARIO ROOT PODE ACESSAR ESTE MODULO.",
        )

    erro = None
    mensagem_sucesso = None

    if request.method == "POST":
        acao_usuario = request.form.get("acao_usuario", "cadastrar").strip().lower()
        usuario = request.form.get("usuario", "").strip()
        usuario_original = request.form.get("usuario_original", "").strip()
        senha = request.form.get("senha", "").strip()
        endereco = request.form.get("endereco", "").strip().upper()
        cep = request.form.get("cep", "").strip().upper()
        patio = request.form.get("patio", "").strip() or None

        if acao_usuario == "deletar":
            if not usuario_original:
                erro = "INFORME O USUARIO A SER EXCLUIDO."
            elif usuario_original.lower() == "root":
                erro = "O USUARIO ROOT NAO PODE SER EXCLUIDO."
            elif excluir_usuario(usuario_original):
                mensagem_sucesso = "USUARIO EXCLUIDO COM SUCESSO."
            else:
                erro = "NAO FOI POSSIVEL EXCLUIR O USUARIO."
        elif acao_usuario == "editar":
            if not usuario_original or not usuario or not senha or not endereco or not cep:
                erro = "PREENCHA USUARIO, SENHA, ENDERECO E CEP PARA EDITAR."
            elif usuario_original.lower() == "root" and usuario.lower() != "root":
                erro = "O NOME DO USUARIO ROOT NAO PODE SER ALTERADO."
            elif atualizar_usuario(usuario_original, usuario, senha, endereco, cep, patio):
                mensagem_sucesso = "USUARIO ATUALIZADO COM SUCESSO."
            else:
                erro = "NAO FOI POSSIVEL ATUALIZAR O USUARIO."
        else:
            if not usuario or not senha or not endereco or not cep:
                erro = "PREENCHA USUARIO, SENHA, ENDERECO E CEP."
            elif cadastrar_usuario(usuario, senha, endereco, cep, patio):
                mensagem_sucesso = "USUARIO CADASTRADO COM SUCESSO."
            else:
                erro = "NAO FOI POSSIVEL CADASTRAR O USUARIO. VERIFIQUE SE ELE JA EXISTE."

    return render_template(
        "usuarios.html",
        erro=erro,
        mensagem_sucesso=mensagem_sucesso,
        usuarios=listar_usuarios(),
    )


@app.route("/backup", methods=["GET", "POST"])
@login_obrigatorio
def backup_completo():
    if not usuario_eh_admin():
        return render_template(
            "acao.html",
            opcao={"titulo": "BACKUP COMPLETO"},
            mensagem_erro="SOMENTE OS USUARIOS ROOT E ADMIN PODEM ACESSAR ESTE MODULO.",
        )

    if request.method == "GET":
        return render_template(
            "backup.html",
            erro=None,
            mensagem_sucesso=None,
            arquivo_backup=None,
            auto_iniciar=request.args.get("auto") == "1",
        )

    try:
        backup_path = criar_backup_completo()
    except BackupError as exc:
        return render_template(
            "backup.html",
            erro=str(exc),
            mensagem_sucesso=None,
            arquivo_backup=None,
            auto_iniciar=False,
        )

    return render_template(
        "backup.html",
        erro=None,
        mensagem_sucesso="BACKUP GERADO COM SUCESSO.",
        arquivo_backup=backup_path.name,
        auto_iniciar=False,
    )


@app.route("/backup/download/<arquivo>")
@login_obrigatorio
def download_backup(arquivo):
    if not usuario_eh_admin():
        return redirect(url_for("painel"))

    backup_path = BACKUP_DIR / arquivo
    if not backup_path.exists():
        return redirect(url_for("painel"))

    return send_file(backup_path, as_attachment=True)


@app.route("/restaurar-backup", methods=["GET", "POST"])
@login_obrigatorio
def restaurar_backup():
    if not usuario_eh_root():
        return render_template(
            "acao.html",
            opcao={"titulo": "RESTAURAR BACKUP"},
            mensagem_erro="SOMENTE O USUARIO ROOT PODE ACESSAR ESTE MODULO.",
        )

    erro = None
    mensagem_sucesso = None

    if request.method == "POST":
        arquivo = request.files.get("arquivo_backup")
        confirmacao = request.form.get("confirmacao_restauracao", "").strip()
        if confirmacao != "SIM":
            erro = "DIGITE SIM EM MAIUSCULO PARA CONFIRMAR A RESTAURACAO."
        elif not arquivo or not arquivo.filename:
            erro = "SELECIONE UM ARQUIVO DE BACKUP."
        else:
            upload_path = BACKUP_DIR / Path(arquivo.filename).name
            arquivo.save(upload_path)
            try:
                restaurar_backup_completo(upload_path)
                mensagem_sucesso = "BACKUP RESTAURADO COM SUCESSO. REINICIE O SISTEMA PARA GARANTIR O RECARREGAMENTO COMPLETO."
            except BackupError as exc:
                erro = str(exc)

    return render_template(
        "restaurar_backup.html",
        erro=erro,
        mensagem_sucesso=mensagem_sucesso,
    )


@app.route("/saida-geral", methods=["GET", "POST"])
@login_obrigatorio
def saida_geral_patio():
    erro = None
    mensagem_sucesso = None
    encerrados = []
    opcao_patio = "todos"
    patio_filtro = None
    veiculos_no_patio = listar_veiculos_no_patio()
    senha_confirmacao = ""

    if request.method == "POST":
        opcao_patio = request.form.get("opcao_patio", "todos").strip().lower() or "todos"
        if opcao_patio == "patio1":
            patio_filtro = 1
        elif opcao_patio == "patio2":
            patio_filtro = 2
        else:
            patio_filtro = None

        senha_confirmacao = request.form.get("senha_saida_lote", "").strip()
        veiculos_no_patio = listar_veiculos_no_patio(patio_filtro)
        if senha_confirmacao != "801973":
            erro = "SENHA INVALIDA."
        else:
            agora = datetime.now()
            encerrados = registrar_saida_lote(agora, patio_filtro)
            if encerrados:
                mensagem_sucesso = f"{len(encerrados)} VEICULO(S) FORAM ENCERRADOS COM VALOR R$ 0,00."
                veiculos_no_patio = []
            else:
                erro = "NAO EXISTEM VEICULOS NO PATIO PARA ENCERRAR OU NAO FOI POSSIVEL CONCLUIR A OPERACAO."

    return render_template(
        "saida_lote.html",
        erro=erro,
        mensagem_sucesso=mensagem_sucesso,
        veiculos_no_patio=veiculos_no_patio,
        encerrados=encerrados,
        senha_confirmacao=senha_confirmacao,
        opcao_patio=opcao_patio,
    )


@app.route("/imprimir/ultima-saida", methods=["POST"])
@login_obrigatorio
def imprimir_ultima_saida():
    comprovante = session.get("ultima_saida")
    if not comprovante:
        return jsonify({"ok": False, "mensagem": "NAO EXISTE ULTIMA SAIDA PARA IMPRIMIR."}), 404

    try:
        print_exit_receipt(comprovante, app.config["PRINTER_NAME"])
    except PrinterError as erro:
        return jsonify({"ok": False, "mensagem": str(erro)}), 500

    return jsonify(
        {
            "ok": True,
            "mensagem": f"IMPRESSAO ENVIADA PARA {app.config['PRINTER_NAME']}.",
            "redirect_url": url_for("saida_veiculo"),
        }
    )


@app.route("/api/placa/<placa>")
@login_obrigatorio
def api_buscar_placa(placa):
    cadastro = buscar_veiculo_por_placa(placa)
    if not cadastro:
        return jsonify({"ok": False}), 404

    return jsonify(
        {
            "ok": True,
            "placa": cadastro.get("placa", ""),
            "codigo": cadastro.get("codigo", ""),
            "marca": cadastro.get("marca", ""),
        }
    )


@app.route("/editar-cadastro-veiculos", methods=["GET", "POST"])
@login_obrigatorio
def editar_cadastro_veiculos():
    erro = None
    mensagem_sucesso = None

    if request.method == "POST":
        placa_original = request.form.get("placa_original", "").strip().upper()
        placa_nova = request.form.get("placa", "").strip().upper()
        codigo = normalizar_codigo_marca_digitado(request.form.get("codigo", ""))

        if not placa_original or not placa_nova or not codigo:
            erro = "INFORME PLACA E CODIGO DA MARCA PARA SALVAR."
        elif not atualizar_cadastro_veiculo(placa_original, placa_nova, codigo):
            erro = "NAO FOI POSSIVEL ATUALIZAR O CADASTRO DO VEICULO."
        else:
            mensagem_sucesso = "CADASTRO DO VEICULO ATUALIZADO COM SUCESSO."

    cadastros = listar_cadastros_veiculos()
    codigos_marcas = listar_codigos_marcas()
    return render_template(
        "editar_cadastro_veiculos.html",
        erro=erro,
        mensagem_sucesso=mensagem_sucesso,
        cadastros=cadastros,
        codigos_marcas=codigos_marcas,
    )


@app.route("/nfse-avulsa", methods=["GET", "POST"])
@login_obrigatorio
def nfse_avulsa():
    erro = None
    documento_tomador = ""
    valor_servico = ""
    observacao_nf = ""
    acesso_liberado = session.get("nfse_avulsa_liberada") is True

    if request.method == "POST":
        if not acesso_liberado:
            senha_acesso = request.form.get("senha_acesso", "").strip()
            if senha_acesso != "801973":
                erro = "SENHA INVALIDA."
            else:
                session["nfse_avulsa_liberada"] = True
                acesso_liberado = True
        else:
            documento_tomador = request.form.get("documento_tomador", "").strip()
            valor_servico = request.form.get("valor_servico", "").strip()
            observacao_nf = request.form.get("observacao_nf", "").strip().upper()

            documento_normalizado = normalizar_documento_tomador(documento_tomador)
            if not documento_normalizado:
                erro = "INFORME O CPF OU CNPJ DO CLIENTE."
            elif not documento_tomador_valido(documento_normalizado):
                erro = "CPF OU CNPJ INVALIDO."
            elif not valor_servico:
                erro = "INFORME O VALOR DO SERVICO."
            elif not observacao_nf:
                erro = "INFORME A OBSERVACAO DA NFS-E."
            else:
                try:
                    valor_servico_float = parse_valor_monetario(valor_servico)
                except ValueError:
                    erro = "VALOR DO SERVICO INVALIDO."
                else:
                    if valor_servico_float <= 0:
                        erro = "O VALOR DO SERVICO DEVE SER MAIOR QUE ZERO."
                    else:
                        try:
                            retorno_nfse = emitir_nfse_avulsa(
                                documento_normalizado,
                                valor_servico_float,
                                observacao_nf,
                            )
                        except (NfseError, NfseSignerError) as exc:
                            erro = str(exc)
                        else:
                            prestador_nfse = montar_dados_prestador_nfse()
                            valor_iss = valor_servico_float * (prestador_nfse.get("aliquota_iss", 0) / 100)
                            comprovante = {
                                "numero_rps": retorno_nfse.get("numero_rps"),
                                "numero_nfse": retorno_nfse.get("numero_nfse"),
                                "codigo_verificacao": retorno_nfse.get("codigo_verificacao"),
                                "mensagem_nfse": retorno_nfse.get("mensagem_nfse"),
                                "data_emissao": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                                "documento_tomador": formatar_documento_tomador(documento_normalizado),
                                "valor_servicos": formatar_moeda(valor_servico_float),
                                "observacao": observacao_nf,
                                "prestador_nfse": prestador_nfse,
                                "discriminacao_nfse": observacao_nf,
                                "valor_iss": formatar_moeda(valor_iss),
                            }
                            session["ultima_nfse_avulsa"] = comprovante
                            return render_template(
                                "nfse_avulsa_comprovante.html",
                                comprovante=comprovante,
                                printer_name=app.config["PRINTER_NAME"],
                                print_payload=gerar_payload_impressao(build_nfse_avulsa_receipt_bytes(comprovante)),
                            )

    return render_template(
        "nfse_avulsa.html",
        erro=erro,
        documento_tomador=documento_tomador,
        valor_servico=valor_servico,
        observacao_nf=observacao_nf,
        acesso_liberado=acesso_liberado,
    )


@app.route("/acao/<acao_id>")
@login_obrigatorio
def acao(acao_id):
    opcao = next((item for item in MENU_OPCOES if item["id"] == acao_id), None)
    if not opcao:
        return redirect(url_for("painel"))

    if acao_id == "precos" and not usuario_eh_root():
        return redirect(url_for("painel"))

    if acao_id == "usuarios" and not usuario_eh_root():
        return redirect(url_for("painel"))

    if acao_id == "entrada":
        return redirect(url_for("entrada_veiculo"))

    if acao_id == "reimprime":
        return redirect(url_for("reimpressao_ultima_entrada"))

    if acao_id == "cancela":
        return redirect(url_for("cancelar_ultima_entrada_view"))

    if acao_id == "saida":
        return redirect(url_for("saida_veiculo"))

    if acao_id == "consulta":
        return redirect(url_for("consulta_estacionamento"))

    if acao_id == "fechamento-caixa":
        return redirect(url_for("fechamento_caixa"))

    if acao_id == "lancamento-fechamento-caixa":
        return redirect(url_for("lancamento_fechamento_caixa"))

    if acao_id == "precos":
        return redirect(url_for("cadastra_precos"))

    if acao_id == "usuarios":
        return redirect(url_for("cadastra_usuarios"))

    if acao_id == "saida-lote":
        return redirect(url_for("saida_geral_patio"))

    if acao_id == "edita-veiculos":
        return redirect(url_for("editar_cadastro_veiculos"))

    if acao_id == "nfse-avulsa":
        return redirect(url_for("nfse_avulsa"))

    if acao_id == "backup":
        return redirect(url_for("backup_completo"))

    if acao_id == "restaura-backup":
        return redirect(url_for("restaurar_backup"))

    return render_template("acao.html", opcao=opcao)


@app.route("/logout")
@login_obrigatorio
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

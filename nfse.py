import html
import os
from datetime import datetime
from decimal import Decimal
import re

import requests

from nfse_signer import (
    NfseSignerError,
    assinar_xml_nfse,
    assinar_rps_nfse,
    carregar_certificado_a1,
    salvar_certificado_temporario_para_requests,
)


DEFAULT_NFSE_ENDPOINT = "https://nfews.prefeitura.sp.gov.br/lotenfe.asmx"
DEFAULT_NFSE_ACTION = "http://www.prefeitura.sp.gov.br/nfe/ws/envioLoteRPS"


class NfseError(Exception):
    pass


def somente_numeros(valor):
    return "".join(ch for ch in str(valor or "") if ch.isdigit())


def xml_escape(valor):
    return html.escape(str(valor or ""), quote=True)


def formatar_decimal(valor):
    return f"{Decimal(str(valor or 0)).quantize(Decimal('0.01'))}"


def formatar_decimal_sem_separador(valor, tamanho):
    decimal_formatado = formatar_decimal(valor).replace(".", "")
    return decimal_formatado.zfill(tamanho)


def montar_numero_rps(numero_rps):
    return str(int(numero_rps))


def gerar_assinatura_rps(dados_empresa, dados_servico):
    cert_path = dados_empresa.get("certificado_caminho")
    if not cert_path:
        return ""

    inscricao_prestador = somente_numeros(dados_empresa.get("ccm")).zfill(8)[-8:]
    serie_rps_xml = str(dados_empresa.get("serie_rps") or "RPS")
    serie_rps_assinatura = serie_rps_xml[:5].ljust(5)
    numero_rps = montar_numero_rps(dados_servico["numero_rps"]).zfill(12)
    data_emissao = dados_servico["data_emissao"].strftime("%Y%m%d")
    tributacao_rps = "T"
    status_rps = "N"
    iss_retido = "N"
    valor_servicos = formatar_decimal_sem_separador(dados_servico.get("valor_servicos"), 15)
    valor_deducoes = formatar_decimal_sem_separador(0, 15)
    codigo_servico = somente_numeros(dados_empresa.get("codigo_servico")).zfill(5)[-5:]

    cpf_tomador = somente_numeros(dados_servico.get("cpf"))
    cnpj_tomador = somente_numeros(dados_servico.get("cnpj_tomador"))
    if cnpj_tomador:
        tipo_documento_tomador = "2"
        documento_tomador = cnpj_tomador.zfill(14)[-14:]
    elif cpf_tomador:
        tipo_documento_tomador = "1"
        documento_tomador = cpf_tomador.zfill(14)[-14:]
    else:
        tipo_documento_tomador = "3"
        documento_tomador = "00000000000000"

    assinatura_string = (
        f"{inscricao_prestador}"
        f"{serie_rps_assinatura}"
        f"{numero_rps}"
        f"{data_emissao}"
        f"{tributacao_rps}"
        f"{status_rps}"
        f"{iss_retido}"
        f"{valor_servicos}"
        f"{valor_deducoes}"
        f"{codigo_servico}"
        f"{tipo_documento_tomador}"
        f"{documento_tomador}"
    )

    if len(assinatura_string) != 86:
        raise NfseError(
            f"STRING DE ASSINATURA DO RPS INVALIDA. TAMANHO GERADO: {len(assinatura_string)}. ESPERADO: 86."
        )

    return assinar_rps_nfse(
        cert_path,
        assinatura_string,
        dados_empresa.get("certificado_chave_caminho"),
        dados_empresa.get("certificado_senha"),
    )


def gerar_xml_rps(dados_empresa, dados_servico):
    serie_rps = dados_empresa.get("serie_rps") or "RPS"
    numero_rps = montar_numero_rps(dados_servico["numero_rps"])
    data_emissao = dados_servico["data_emissao"].strftime("%Y-%m-%d")
    data_emissao_cabecalho = dados_servico["data_emissao"].strftime("%Y-%m-%d")
    cnpj_prestador = somente_numeros(dados_empresa.get("cnpj"))
    inscricao_municipal = somente_numeros(dados_empresa.get("ccm"))
    cpf_tomador = somente_numeros(dados_servico.get("cpf"))
    cnpj_tomador = somente_numeros(dados_servico.get("cnpj_tomador"))
    valor_servicos = formatar_decimal(dados_servico.get("valor_servicos"))
    aliquota = formatar_decimal(dados_empresa.get("aliquota_iss") or 0)
    codigo_servico = somente_numeros(dados_empresa.get("codigo_servico"))
    discriminacao = xml_escape(dados_servico.get("discriminacao"))
    razao_social = xml_escape(dados_empresa.get("razao_social"))
    assinatura_rps = gerar_assinatura_rps(dados_empresa, dados_servico)
    if cnpj_tomador:
        bloco_tomador = f"""    <CPFCNPJTomador>
      <CNPJ>{cnpj_tomador}</CNPJ>
    </CPFCNPJTomador>
"""
    elif cpf_tomador:
        bloco_tomador = f"""    <CPFCNPJTomador>
      <CPF>{cpf_tomador}</CPF>
    </CPFCNPJTomador>
"""
    else:
        bloco_tomador = ""

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<PedidoEnvioLoteRPS xmlns="http://www.prefeitura.sp.gov.br/nfe">
  <Cabecalho xmlns="" Versao="1">
    <CPFCNPJRemetente>
      <CNPJ>{cnpj_prestador}</CNPJ>
    </CPFCNPJRemetente>
    <transacao>true</transacao>
    <dtInicio>{data_emissao_cabecalho}</dtInicio>
    <dtFim>{data_emissao_cabecalho}</dtFim>
    <QtdRPS>1</QtdRPS>
    <ValorTotalServicos>{valor_servicos}</ValorTotalServicos>
    <ValorTotalDeducoes>0.00</ValorTotalDeducoes>
  </Cabecalho>
  <RPS xmlns="">
    <Assinatura>{assinatura_rps}</Assinatura>
    <ChaveRPS>
      <InscricaoPrestador>{inscricao_municipal}</InscricaoPrestador>
      <SerieRPS>{xml_escape(serie_rps)}</SerieRPS>
      <NumeroRPS>{numero_rps}</NumeroRPS>
    </ChaveRPS>
    <TipoRPS>RPS</TipoRPS>
    <DataEmissao>{data_emissao}</DataEmissao>
    <StatusRPS>N</StatusRPS>
    <TributacaoRPS>T</TributacaoRPS>
    <ValorServicos>{valor_servicos}</ValorServicos>
    <ValorDeducoes>0.00</ValorDeducoes>
    <CodigoServico>{codigo_servico}</CodigoServico>
    <AliquotaServicos>{aliquota}</AliquotaServicos>
    <ISSRetido>false</ISSRetido>
{bloco_tomador}    <RazaoSocialTomador>CONSUMIDOR FINAL</RazaoSocialTomador>
    <Discriminacao>{discriminacao}</Discriminacao>
  </RPS>
</PedidoEnvioLoteRPS>"""


def assinar_xml_rps_se_configurado(dados_empresa, xml_rps):
    cert_path = dados_empresa.get("certificado_caminho")
    key_path = dados_empresa.get("certificado_chave_caminho")
    cert_password = dados_empresa.get("certificado_senha")
    if not cert_path:
        return xml_rps

    cert_data, key_data = carregar_certificado_a1(cert_path, key_path, cert_password)
    return assinar_xml_nfse(xml_rps, cert_data, key_data)


def montar_soap_envio(xml_rps):
    return f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <EnvioLoteRPSRequest xmlns="http://www.prefeitura.sp.gov.br/nfe">
      <VersaoSchema>1</VersaoSchema>
      <MensagemXML><![CDATA[{xml_rps}]]></MensagemXML>
    </EnvioLoteRPSRequest>
  </soap:Body>
</soap:Envelope>"""


def extrair_numero_nfse(resposta_texto):
    match = re.search(r"<NumeroNFe>(\d+)</NumeroNFe>", resposta_texto)
    return match.group(1) if match else None


def extrair_codigo_verificacao(resposta_texto):
    match = re.search(r"<CodigoVerificacao>([^<]+)</CodigoVerificacao>", resposta_texto)
    return match.group(1) if match else None


def extrair_retorno_xml(resposta_texto):
    match = re.search(r"<RetornoXML>(.*?)</RetornoXML>", resposta_texto, flags=re.DOTALL)
    if not match:
        return None
    return html.unescape(match.group(1) or "").strip()


def extrair_erro(resposta_texto):
    retorno_xml = extrair_retorno_xml(resposta_texto or "")
    if retorno_xml:
        match_descricao = re.search(r"<Descricao>(.*?)</Descricao>", retorno_xml, flags=re.DOTALL)
        if match_descricao:
            return html.unescape(match_descricao.group(1) or "").strip()
        match_mensagem = re.search(r"<Mensagem>(.*?)</Mensagem>", retorno_xml, flags=re.DOTALL)
        if match_mensagem:
            return html.unescape(match_mensagem.group(1) or "").strip()

    match = re.search(r"<Mensagem>([^<]+)</Mensagem>", resposta_texto)
    return match.group(1) if match else None


def enviar_rps_sao_paulo(dados_empresa, xml_rps):
    endpoint = dados_empresa.get("ws_endpoint") or DEFAULT_NFSE_ENDPOINT
    soap_action = dados_empresa.get("ws_soap_action") or DEFAULT_NFSE_ACTION
    xml_assinado = assinar_xml_rps_se_configurado(dados_empresa, xml_rps)
    envelope = montar_soap_envio(xml_assinado)

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": soap_action,
    }

    cert = None
    cert_temp_files = []
    cert_path = dados_empresa.get("certificado_caminho")
    if cert_path:
        cert_data, key_data = carregar_certificado_a1(
            cert_path,
            dados_empresa.get("certificado_chave_caminho"),
            dados_empresa.get("certificado_senha"),
        )
        if key_data:
            cert = salvar_certificado_temporario_para_requests(cert_data, key_data)
            cert_temp_files = list(cert)

    try:
        response = requests.post(
            endpoint,
            data=envelope.encode("utf-8"),
            headers=headers,
            timeout=45,
            cert=cert,
        )
        retorno = response.text
        if not response.ok:
            mensagem_http = extrair_erro(retorno) or retorno or f"HTTP {response.status_code}"
            raise NfseError(
                f"WEBSERVICE NFS-E RETORNOU HTTP {response.status_code}: {mensagem_http}"
            )
    except requests.RequestException as exc:
        resposta = getattr(exc, "response", None)
        if resposta is not None:
            retorno = resposta.text
            mensagem_http = extrair_erro(retorno) or retorno or str(exc)
            raise NfseError(
                f"WEBSERVICE NFS-E RETORNOU HTTP {resposta.status_code}: {mensagem_http}"
            ) from exc
        raise NfseError(f"FALHA AO ENVIAR RPS PARA O WEBSERVICE DA NFS-E: {exc}") from exc
    finally:
        for temp_path in cert_temp_files:
            try:
                os.unlink(temp_path)
            except OSError:
                pass

    retorno_processado = extrair_retorno_xml(retorno) or retorno
    return {
        "http_status": response.status_code,
        "raw_response": retorno_processado,
        "xml_enviado": xml_assinado,
        "numero_nfse": extrair_numero_nfse(retorno_processado),
        "codigo_verificacao": extrair_codigo_verificacao(retorno_processado),
        "erro": extrair_erro(retorno_processado),
    }


def montar_dados_servico_para_nfse(movimento_saida):
    descricao = (
        f"ESTACIONAMENTO VEICULO PLACA {movimento_saida['placa']} - "
        f"ENTRADA {movimento_saida['numero_entrada']} - "
        f"TEMPO {movimento_saida['tempo_permanencia']}"
    )
    documento = somente_numeros(movimento_saida.get("cpf"))
    return {
        "numero_rps": movimento_saida["numero_rps"],
        "data_emissao": movimento_saida["data_hora_saida"],
        "cpf": documento if len(documento) == 11 else "",
        "cnpj_tomador": documento if len(documento) == 14 else "",
        "forma_pagamento": movimento_saida.get("forma_pagamento"),
        "valor_servicos": movimento_saida["valor_cobrado"],
        "discriminacao": descricao,
    }


def montar_dados_servico_avulso(numero_rps, data_emissao, documento_tomador, valor_servicos, observacao):
    documento = somente_numeros(documento_tomador)
    return {
        "numero_rps": numero_rps,
        "data_emissao": data_emissao,
        "cpf": documento if len(documento) == 11 else "",
        "cnpj_tomador": documento if len(documento) == 14 else "",
        "forma_pagamento": "CARTAO",
        "valor_servicos": valor_servicos,
        "discriminacao": observacao,
    }

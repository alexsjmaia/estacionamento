import base64
import tempfile
from pathlib import Path


class NfseSignerError(Exception):
    pass


def carregar_certificado_a1(cert_path, key_path=None, password=None):
    cert_path = Path(cert_path)
    if not cert_path.exists():
        raise NfseSignerError(f"CERTIFICADO NAO ENCONTRADO: {cert_path}")

    extensao = cert_path.suffix.lower()
    cert_data = cert_path.read_bytes()
    key_data = None

    if extensao in {".pfx", ".p12"}:
        try:
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.serialization import pkcs12
        except ImportError as exc:
            raise NfseSignerError(
                "SUPORTE A CERTIFICADO PFX NAO DISPONIVEL. INSTALE A DEPENDENCIA OPCIONAL: PIP INSTALL cryptography"
            ) from exc

        try:
            private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
                cert_data,
                password.encode("utf-8") if password else None,
            )
        except Exception as exc:
            raise NfseSignerError(f"NAO FOI POSSIVEL LER O CERTIFICADO PFX: {exc}") from exc

        if private_key is None or certificate is None:
            raise NfseSignerError("O CERTIFICADO PFX NAO CONTEM CERTIFICADO E CHAVE PRIVADA VALIDOS.")

        cert_chain = [
            certificate.public_bytes(serialization.Encoding.PEM),
        ]
        for extra in additional_certificates or []:
            cert_chain.append(extra.public_bytes(serialization.Encoding.PEM))

        cert_data = b"".join(cert_chain)
        key_data = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
        return cert_data, key_data

    if key_path:
        key_path = Path(key_path)
        if not key_path.exists():
            raise NfseSignerError(f"CHAVE PRIVADA NAO ENCONTRADA: {key_path}")
        key_data = key_path.read_bytes()

    return cert_data, key_data


def assinar_rps_nfse(cert_path, assinatura_string, key_path=None, password=None):
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
    except ImportError as exc:
        raise NfseSignerError(
            "ASSINATURA DO RPS NAO DISPONIVEL. INSTALE A DEPENDENCIA OPCIONAL: PIP INSTALL cryptography"
        ) from exc

    _, key_data = carregar_certificado_a1(cert_path, key_path, password)
    if not key_data:
        raise NfseSignerError("CHAVE PRIVADA NAO DISPONIVEL PARA ASSINATURA DO RPS.")

    try:
        private_key = serialization.load_pem_private_key(key_data, password=None)
        assinatura = private_key.sign(
            assinatura_string.encode("ascii"),
            padding.PKCS1v15(),
            hashes.SHA1(),
        )
        return base64.b64encode(assinatura).decode("ascii")
    except Exception as exc:
        raise NfseSignerError(f"NAO FOI POSSIVEL ASSINAR O RPS: {exc}") from exc


def salvar_certificado_temporario_para_requests(cert_data, key_data):
    if not cert_data or not key_data:
        raise NfseSignerError("CERTIFICADO E CHAVE PRIVADA SAO OBRIGATORIOS PARA AUTENTICACAO HTTPS.")

    cert_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pem")
    key_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pem")
    try:
        cert_temp.write(cert_data)
        key_temp.write(key_data)
    finally:
        cert_temp.close()
        key_temp.close()

    return cert_temp.name, key_temp.name


def assinar_xml_nfse(xml_texto, cert_data, key_data, reference_uri=None):
    try:
        from lxml import etree
        from signxml import XMLSigner, methods

        class LegacyXMLSigner(XMLSigner):
            def check_deprecated_methods(self):
                return None

        root = etree.fromstring(xml_texto.encode("utf-8"))
        signer = LegacyXMLSigner(
            method=methods.enveloped,
            signature_algorithm="rsa-sha1",
            digest_algorithm="sha1",
            c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315",
        )
        signed_root = signer.sign(
            root,
            key=key_data,
            cert=cert_data,
            reference_uri=reference_uri,
        )
        return etree.tostring(signed_root, encoding="utf-8", xml_declaration=True).decode("utf-8")
    except ImportError as exc:
        raise NfseSignerError(
            "ASSINATURA XML NAO DISPONIVEL. INSTALE AS DEPENDENCIAS OPCIONAIS: PIP INSTALL lxml signxml"
        ) from exc
    except Exception as exc:
        raise NfseSignerError(f"NAO FOI POSSIVEL ASSINAR O XML DA NFS-E: {exc}") from exc

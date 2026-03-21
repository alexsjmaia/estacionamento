import os
from pathlib import Path
from datetime import datetime

import mysql.connector
from mysql.connector import Error


BASE_DIR = Path(__file__).resolve().parent


def carregar_arquivo_env():
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return

    for linha in env_path.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue

        chave, valor = linha.split("=", 1)
        chave = chave.strip()
        valor = valor.strip().strip('"').strip("'")
        if chave and chave not in os.environ:
            os.environ[chave] = valor


carregar_arquivo_env()


def get_db_config():
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "estacionamento"),
    }


def test_connection():
    connection = None
    try:
        connection = mysql.connector.connect(**get_db_config())
        if connection.is_connected():
            return True
    except Error:
        return False
    finally:
        if connection is not None and connection.is_connected():
            connection.close()

    return False


def autenticar_usuario(usuario, senha):
    usuario = (usuario or "").strip()
    senha = (senha or "").strip()
    if not usuario or not senha:
        return False

    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**get_db_config())
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    usuario,
                    senha,
                    endereco,
                    cep,
                    patio
                FROM usuarios
                WHERE usuario = %s AND senha = %s
                LIMIT 1
                """,
                (usuario, senha),
            )
            registro = cursor.fetchone()
            return registro
    except Error:
        return None
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

    return None


def listar_usuarios():
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**get_db_config())
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    id,
                    usuario,
                    endereco,
                    cep,
                    patio
                FROM usuarios
                ORDER BY usuario
                """
            )
            return cursor.fetchall()
    except Error:
        return []
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

    return []


def cadastrar_usuario(usuario, senha, endereco, cep, patio=None):
    usuario = (usuario or "").strip()
    senha = (senha or "").strip()
    endereco = (endereco or "").strip()
    cep = (cep or "").strip()

    if not usuario or not senha or not endereco or not cep:
        return False

    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**get_db_config())
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO usuarios (usuario, senha, endereco, cep, patio)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (usuario, senha, endereco, cep, patio),
            )
            connection.commit()
            return True
    except Error:
        return False
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

    return False


def atualizar_usuario(usuario_original, usuario_novo, senha, endereco, cep, patio=None):
    usuario_original = (usuario_original or "").strip()
    usuario_novo = (usuario_novo or "").strip()
    senha = (senha or "").strip()
    endereco = (endereco or "").strip()
    cep = (cep or "").strip()

    if not usuario_original or not usuario_novo or not senha or not endereco or not cep:
        return False

    if usuario_original.lower() == "root" and usuario_novo.lower() != "root":
        return False

    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**get_db_config())
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE usuarios
                SET
                    usuario = %s,
                    senha = %s,
                    endereco = %s,
                    cep = %s,
                    patio = %s
                WHERE usuario = %s
                """,
                (usuario_novo, senha, endereco, cep, patio, usuario_original),
            )
            connection.commit()
            return cursor.rowcount > 0
    except Error:
        return False
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

    return False


def excluir_usuario(usuario):
    usuario = (usuario or "").strip()
    if not usuario or usuario.lower() == "root":
        return False

    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**get_db_config())
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute(
                """
                DELETE FROM usuarios
                WHERE usuario = %s
                """,
                (usuario,),
            )
            connection.commit()
            return cursor.rowcount > 0
    except Error:
        return False
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

    return False


def buscar_veiculo_por_placa(placa):
    placa = (placa or "").strip().upper()
    if not placa:
        return None

    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**get_db_config())
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    UPPER(placa) AS placa,
                    UPPER(codigo) AS codigo,
                    UPPER(marca) AS marca
                FROM placas
                WHERE UPPER(placa) = %s
                LIMIT 1
                """,
                (placa,),
            )
            registro = cursor.fetchone()
            if registro:
                return registro
    except Error:
        return None
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

    return None


def listar_codigos_marcas():
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**get_db_config())
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    codigo,
                    UPPER(marca) AS marca
                FROM codigos_marcas
                ORDER BY marca, codigo
                """
            )
            return cursor.fetchall()
    except Error:
        return []
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

    return []


def buscar_codigo_marca(codigo):
    codigo = (codigo or "").strip().zfill(3)
    if not codigo:
        return None

    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**get_db_config())
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    codigo,
                    UPPER(marca) AS marca
                FROM codigos_marcas
                WHERE codigo = %s
                LIMIT 1
                """,
                (codigo,),
            )
            return cursor.fetchone()
    except Error:
        return None
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

    return None


def cadastrar_placa(placa, codigo):
    placa = (placa or "").strip().upper()
    codigo_info = buscar_codigo_marca(codigo)
    if not placa or not codigo_info:
        return None

    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**get_db_config())
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO placas (placa, codigo, marca)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    codigo = VALUES(codigo),
                    marca = VALUES(marca)
                """,
                (placa, codigo_info["codigo"], codigo_info["marca"]),
            )
            connection.commit()
            return {
                "placa": placa,
                "codigo": codigo_info["codigo"],
                "marca": codigo_info["marca"],
            }
    except Error:
        return None
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

    return None


def gerar_numero_entrada_diario(data_referencia=None):
    data_referencia = data_referencia or datetime.now()
    prefixo = data_referencia.strftime("%d%m%y")

    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**get_db_config())
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT numero_entrada
                FROM veiculos
                WHERE numero_entrada LIKE %s
                ORDER BY numero_entrada DESC
                LIMIT 1
                """,
                (f"{prefixo}%",),
            )
            registro = cursor.fetchone()
            if registro and registro.get("numero_entrada"):
                ultimo = registro["numero_entrada"]
                sequencial = int(ultimo[len(prefixo):] or "0") + 1
            else:
                sequencial = 1

            return f"{prefixo}{sequencial}"
    except Error:
        return None
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

    return None


def registrar_entrada_veiculo(placa, numero_entrada, data_hora_entrada, patio=None):
    placa = (placa or "").strip().upper()
    numero_entrada = (numero_entrada or "").strip()
    if not placa or not numero_entrada or data_hora_entrada is None:
        return None

    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**get_db_config())
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO veiculos (
                    numero_entrada,
                    placa,
                    patio,
                    data_hora_entrada,
                    data_hora_saida,
                    tempo_permanencia,
                    valor_cobrado,
                    forma_pagamento
                )
                VALUES (%s, %s, %s, %s, NULL, NULL, NULL, NULL)
                """,
                (numero_entrada, placa, patio, data_hora_entrada),
            )
            connection.commit()
            return cursor.lastrowid
    except Error:
        return None
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

    return None


def veiculo_esta_no_patio(placa):
    placa = (placa or "").strip().upper()
    if not placa:
        return False

    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**get_db_config())
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    id,
                    placa,
                    data_hora_entrada
                FROM veiculos
                WHERE placa = %s
                  AND data_hora_saida IS NULL
                ORDER BY data_hora_entrada DESC
                LIMIT 1
                """,
                (placa,),
            )
            return cursor.fetchone()
    except Error:
        return None
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

    return None


def buscar_movimento_aberto_por_placa(placa):
    placa = (placa or "").strip().upper()
    if not placa:
        return None

    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**get_db_config())
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    v.id,
                    v.numero_entrada,
                    UPPER(v.placa) AS placa,
                    v.data_hora_entrada,
                    UPPER(p.marca) AS marca
                FROM veiculos v
                INNER JOIN placas p ON p.placa = v.placa
                WHERE v.placa = %s
                  AND v.data_hora_saida IS NULL
                ORDER BY v.data_hora_entrada DESC
                LIMIT 1
                """,
                (placa,),
            )
            return cursor.fetchone()
    except Error:
        return None
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

    return None


def buscar_movimento_aberto_por_numero_entrada(numero_entrada):
    numero_entrada = (numero_entrada or "").strip()
    if not numero_entrada:
        return None

    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**get_db_config())
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    v.id,
                    v.numero_entrada,
                    UPPER(v.placa) AS placa,
                    v.data_hora_entrada,
                    UPPER(p.marca) AS marca
                FROM veiculos v
                INNER JOIN placas p ON p.placa = v.placa
                WHERE v.numero_entrada = %s
                  AND v.data_hora_saida IS NULL
                ORDER BY v.data_hora_entrada DESC
                LIMIT 1
                """,
                (numero_entrada,),
            )
            return cursor.fetchone()
    except Error:
        return None
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

    return None


def buscar_movimento_aberto_por_placa_e_numero(placa, numero_entrada):
    placa = (placa or "").strip().upper()
    numero_entrada = (numero_entrada or "").strip()
    if not placa or not numero_entrada:
        return None

    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**get_db_config())
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    v.id,
                    v.numero_entrada,
                    UPPER(v.placa) AS placa,
                    v.data_hora_entrada,
                    UPPER(p.marca) AS marca
                FROM veiculos v
                INNER JOIN placas p ON p.placa = v.placa
                WHERE UPPER(v.placa) = %s
                  AND v.numero_entrada = %s
                  AND v.data_hora_saida IS NULL
                ORDER BY v.data_hora_entrada DESC
                LIMIT 1
                """,
                (placa, numero_entrada),
            )
            return cursor.fetchone()
    except Error:
        return None
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

    return None


def listar_precos():
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**get_db_config())
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    id,
                    descricao,
                    hora_inicial,
                    hora_final,
                    valor,
                    tipo_valor
                FROM precos
                ORDER BY hora_inicial, id
                """
            )
            return cursor.fetchall()
    except Error:
        return []
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

    return []


def listar_formas_pagamento():
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**get_db_config())
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    id,
                    UPPER(descricao) AS descricao
                FROM formas_pagamento
                ORDER BY id
                """
            )
            return cursor.fetchall()
    except Error:
        return []
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

    return []


def buscar_forma_pagamento(forma_pagamento_id):
    if not forma_pagamento_id:
        return None

    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**get_db_config())
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    id,
                    UPPER(descricao) AS descricao
                FROM formas_pagamento
                WHERE id = %s
                LIMIT 1
                """,
                (forma_pagamento_id,),
            )
            return cursor.fetchone()
    except Error:
        return None
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

    return None


def registrar_saida_veiculo(
    registro_id,
    data_hora_saida,
    tempo_permanencia,
    valor_cobrado,
    forma_pagamento,
    cpf=None,
    serie_rps="RPS",
):
    if not registro_id or data_hora_saida is None:
        return None

    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**get_db_config())
        if connection.is_connected():
            cursor = connection.cursor(buffered=True)
            numero_rps = None

            cursor.execute(
                """
                SELECT ultimo_numero_rps
                FROM controle_rps
                WHERE serie_rps = %s
                FOR UPDATE
                """,
                (serie_rps,),
            )
            controle = cursor.fetchone()
            if controle:
                numero_rps = int(controle[0] or 0) + 1
                cursor.execute(
                    """
                    UPDATE controle_rps
                    SET ultimo_numero_rps = %s
                    WHERE serie_rps = %s
                    """,
                    (numero_rps, serie_rps),
                )
            else:
                numero_rps = 1
                cursor.execute(
                    """
                    INSERT INTO controle_rps (serie_rps, ultimo_numero_rps)
                    VALUES (%s, %s)
                    """,
                    (serie_rps, numero_rps),
                )

            cursor.execute(
                """
                UPDATE veiculos
                SET
                    data_hora_saida = %s,
                    tempo_permanencia = %s,
                    valor_cobrado = %s,
                    forma_pagamento = %s,
                    cpf = %s,
                    numero_rps = %s
                WHERE id = %s
                """,
                (data_hora_saida, tempo_permanencia, valor_cobrado, forma_pagamento, cpf, numero_rps, registro_id),
            )
            connection.commit()
            return numero_rps if cursor.rowcount > 0 else None
    except Error:
        if connection is not None and connection.is_connected():
            connection.rollback()
        return False
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

    return None


def buscar_ultima_entrada_no_patio():
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**get_db_config())
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    v.id,
                    v.numero_entrada,
                    v.data_hora_entrada,
                    UPPER(v.placa) AS placa,
                    UPPER(p.marca) AS marca
                FROM veiculos v
                INNER JOIN placas p ON p.placa = v.placa
                WHERE v.data_hora_saida IS NULL
                ORDER BY v.data_hora_entrada DESC
                LIMIT 1
                """
            )
            return cursor.fetchone()
    except Error:
        return None
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

    return None


def buscar_ultima_entrada_no_patio_por_patio(patio):
    if patio in (None, ""):
        return buscar_ultima_entrada_no_patio()

    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**get_db_config())
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    v.id,
                    v.numero_entrada,
                    v.data_hora_entrada,
                    UPPER(v.placa) AS placa,
                    UPPER(p.marca) AS marca,
                    v.patio
                FROM veiculos v
                INNER JOIN placas p ON p.placa = v.placa
                WHERE v.data_hora_saida IS NULL
                  AND v.patio = %s
                ORDER BY v.data_hora_entrada DESC
                LIMIT 1
                """,
                (patio,),
            )
            return cursor.fetchone()
    except Error:
        return None
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

    return None


def listar_veiculos_no_patio():
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**get_db_config())
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    v.id,
                    v.numero_entrada,
                    v.data_hora_entrada,
                    UPPER(v.placa) AS placa,
                    UPPER(p.marca) AS marca
                FROM veiculos v
                INNER JOIN placas p ON p.placa = v.placa
                WHERE v.data_hora_saida IS NULL
                ORDER BY v.data_hora_entrada
                """
            )
            return cursor.fetchall()
    except Error:
        return []
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

    return []


def registrar_saida_lote(data_hora_saida):
    if data_hora_saida is None:
        return []

    veiculos_no_patio = listar_veiculos_no_patio()
    if not veiculos_no_patio:
        return []

    connection = None
    cursor = None
    atualizados = []
    try:
        connection = mysql.connector.connect(**get_db_config())
        if connection.is_connected():
            cursor = connection.cursor()
            for veiculo in veiculos_no_patio:
                delta = data_hora_saida - veiculo["data_hora_entrada"]
                total_segundos = max(int(delta.total_seconds()), 0)
                horas = total_segundos // 3600
                minutos = (total_segundos % 3600) // 60
                segundos = total_segundos % 60
                tempo_permanencia = f"{horas:02d}:{minutos:02d}:{segundos:02d}"

                cursor.execute(
                    """
                    UPDATE veiculos
                    SET
                        data_hora_saida = %s,
                        tempo_permanencia = %s,
                        valor_cobrado = 0.00,
                        forma_pagamento = NULL
                    WHERE id = %s
                      AND data_hora_saida IS NULL
                    """,
                    (data_hora_saida, tempo_permanencia, veiculo["id"]),
                )

                if cursor.rowcount > 0:
                    atualizados.append(
                        {
                            "numero_entrada": veiculo["numero_entrada"],
                            "placa": veiculo["placa"],
                            "marca": veiculo["marca"],
                            "data_hora_entrada": veiculo["data_hora_entrada"],
                            "data_hora_saida": data_hora_saida,
                            "tempo_permanencia": tempo_permanencia,
                        }
                    )

            connection.commit()
            return atualizados
    except Error:
        if connection is not None and connection.is_connected():
            connection.rollback()
        return []
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

    return []


def cancelar_ultima_entrada(registro_id):
    if not registro_id:
        return False

    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**get_db_config())
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE veiculos
                SET
                    data_hora_saida = data_hora_entrada,
                    tempo_permanencia = '00:00',
                    valor_cobrado = 0.00,
                    forma_pagamento = NULL
                WHERE id = %s
                  AND data_hora_saida IS NULL
                """,
                (registro_id,),
            )
            connection.commit()
            return cursor.rowcount > 0
    except Error:
        return False
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

    return False


def consultar_estacionamento(data_inicial, data_final):
    if not data_inicial or not data_final:
        return None

    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**get_db_config())
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT COUNT(*) AS total_entradas
                FROM veiculos
                WHERE data_hora_entrada BETWEEN %s AND %s
                """,
                (data_inicial, data_final),
            )
            total_entradas = cursor.fetchone()["total_entradas"]

            cursor.execute(
                """
                SELECT COUNT(*) AS total_no_patio
                FROM veiculos
                WHERE data_hora_saida IS NULL
                """
            )
            total_no_patio = cursor.fetchone()["total_no_patio"]

            cursor.execute(
                """
                SELECT COALESCE(SUM(valor_cobrado), 0) AS faturamento_total
                FROM veiculos
                WHERE data_hora_entrada BETWEEN %s AND %s
                """,
                (data_inicial, data_final),
            )
            faturamento_total = float(cursor.fetchone()["faturamento_total"] or 0)

            ticket_medio = faturamento_total / total_entradas if total_entradas else 0

            cursor.execute(
                """
                SELECT
                    COALESCE(patio, 0) AS patio,
                    COUNT(*) AS total_entradas,
                    SUM(CASE WHEN data_hora_saida IS NULL THEN 1 ELSE 0 END) AS total_no_patio,
                    COALESCE(SUM(valor_cobrado), 0) AS faturamento_total
                FROM veiculos
                WHERE data_hora_entrada BETWEEN %s AND %s
                GROUP BY patio
                ORDER BY patio
                """,
                (data_inicial, data_final),
            )
            patios = {}
            for item in cursor.fetchall():
                patios[int(item["patio"] or 0)] = {
                    "total_entradas": int(item["total_entradas"] or 0),
                    "total_no_patio": int(item["total_no_patio"] or 0),
                    "faturamento_total": float(item["faturamento_total"] or 0),
                }

            return {
                "total_entradas": total_entradas,
                "total_no_patio": total_no_patio,
                "faturamento_total": faturamento_total,
                "ticket_medio": ticket_medio,
                "patios": patios,
            }
    except Error:
        return None
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

    return None


def atualizar_preco(preco_id, valor):
    if not preco_id:
        return False

    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**get_db_config())
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE precos
                SET valor = %s
                WHERE id = %s
                """,
                (valor, preco_id),
            )
            connection.commit()
            return cursor.rowcount > 0
    except Error:
        return False
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

    return False


def obter_empresa_fiscal_ativa():
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**get_db_config())
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    id,
                    razao_social,
                    nome_fantasia,
                    cnpj,
                    ccm,
                    inscricao_municipal,
                    regime_tributario,
                    optante_simples_nacional,
                    data_inicio_simples,
                    email,
                    telefone,
                    codigo_servico,
                    aliquota_iss,
                    serie_rps,
                    senha_web,
                    usuario_emissor,
                    ambiente,
                    ativo,
                    ws_endpoint,
                    ws_soap_action,
                    certificado_caminho,
                    certificado_chave_caminho,
                    certificado_senha
                FROM empresa_fiscal
                WHERE ativo = 1
                ORDER BY id DESC
                LIMIT 1
                """
            )
            return cursor.fetchone()
    except Error:
        return None
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

    return None


def atualizar_dados_nfse_veiculo(
    registro_id,
    numero_nfse=None,
    codigo_verificacao=None,
    status_nfse=None,
    xml_rps=None,
    resposta_nfse=None,
):
    if not registro_id:
        return False

    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**get_db_config())
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE veiculos
                SET
                    numero_nfse = %s,
                    codigo_verificacao_nfse = %s,
                    status_nfse = %s,
                    xml_rps = %s,
                    resposta_nfse = %s
                WHERE id = %s
                """,
                (numero_nfse, codigo_verificacao, status_nfse, xml_rps, resposta_nfse, registro_id),
            )
            connection.commit()
            return cursor.rowcount > 0
    except Error:
        return False
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

    return False


def registrar_log_nfse(
    veiculo_id,
    numero_rps,
    xml_rps,
    resposta_nfse,
    status_envio,
    mensagem_retorno=None,
    numero_nfse=None,
):
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**get_db_config())
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO nfse_envios (
                    veiculo_id,
                    numero_rps,
                    xml_rps,
                    resposta_nfse,
                    status_envio,
                    mensagem_retorno,
                    numero_nfse
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (veiculo_id, numero_rps, xml_rps, resposta_nfse, status_envio, mensagem_retorno, numero_nfse),
            )
            connection.commit()
            return cursor.lastrowid
    except Error:
        return None
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

    return None

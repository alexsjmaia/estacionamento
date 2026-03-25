import csv
from pathlib import Path

import mysql.connector
from mysql.connector import Error


BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "data" / "codigos_marcas.csv"

DB_SERVER_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "260803",
}

DB_NAME = "estacionamento"
TABLE_NAME = "codigos_marcas"
USERS_TABLE_NAME = "usuarios"
PAYMENT_TABLE_NAME = "formas_pagamento"


def carregar_registros():
    with CSV_PATH.open("r", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        return [
            (linha["codigo"].strip().zfill(3), linha["marca"].strip().upper())
            for linha in leitor
            if linha["codigo"].strip() and linha["marca"].strip()
        ]


def criar_banco_e_tabela():
    conexao = mysql.connector.connect(**DB_SERVER_CONFIG)
    cursor = conexao.cursor()

    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    cursor.execute(f"USE {DB_NAME}")
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {USERS_TABLE_NAME} (
            id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            usuario VARCHAR(50) NOT NULL UNIQUE,
            senha VARCHAR(100) NOT NULL,
            endereco VARCHAR(150) NOT NULL DEFAULT 'RUA RIO BONITO, 845',
            cep VARCHAR(20) NOT NULL DEFAULT 'CEP 03023-000'
        )
        """
    )
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            codigo CHAR(3) NOT NULL PRIMARY KEY,
            marca VARCHAR(120) NOT NULL
        )
        """
    )
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {PAYMENT_TABLE_NAME} (
            id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            descricao VARCHAR(30) NOT NULL UNIQUE
        )
        """
    )

    conexao.commit()
    cursor.close()
    conexao.close()


def popular_usuarios():
    conexao = mysql.connector.connect(**DB_SERVER_CONFIG, database=DB_NAME)
    cursor = conexao.cursor()
    cursor.execute(
        f"""
        INSERT INTO {USERS_TABLE_NAME} (usuario, senha, endereco, cep)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            senha = VALUES(senha),
            endereco = VALUES(endereco),
            cep = VALUES(cep)
        """,
        ("ROOT", "ROOT", "RUA RIO BONITO, 845", "CEP 03023-000"),
    )
    conexao.commit()
    cursor.close()
    conexao.close()


def popular_tabela():
    registros = carregar_registros()
    conexao = mysql.connector.connect(**DB_SERVER_CONFIG, database=DB_NAME)
    cursor = conexao.cursor()
    cursor.executemany(
        f"""
        INSERT INTO {TABLE_NAME} (codigo, marca)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE marca = VALUES(marca)
        """,
        registros,
    )
    conexao.commit()
    total = cursor.rowcount
    cursor.close()
    conexao.close()
    return total, len(registros)


def popular_formas_pagamento():
    conexao = mysql.connector.connect(**DB_SERVER_CONFIG, database=DB_NAME)
    cursor = conexao.cursor()
    cursor.executemany(
        f"""
        INSERT INTO {PAYMENT_TABLE_NAME} (descricao)
        VALUES (%s)
        ON DUPLICATE KEY UPDATE descricao = VALUES(descricao)
        """,
        [("PIX",), ("DINHEIRO",), ("CARTAO",)],
    )
    conexao.commit()
    cursor.close()
    conexao.close()


def main():
    try:
        criar_banco_e_tabela()
        popular_usuarios()
        popular_formas_pagamento()
        _, quantidade = popular_tabela()
        print(
            f"BANCO '{DB_NAME}' INICIALIZADO COM TABELAS '{USERS_TABLE_NAME}', '{TABLE_NAME}' E '{PAYMENT_TABLE_NAME}', "
            f"E {quantidade} REGISTROS DE MARCAS."
        )
    except Error as erro:
        print(f"ERRO AO INICIALIZAR O BANCO: {erro}")


if __name__ == "__main__":
    main()

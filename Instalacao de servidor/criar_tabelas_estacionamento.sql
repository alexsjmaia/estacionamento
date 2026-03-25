CREATE DATABASE IF NOT EXISTS estacionamento;
USE estacionamento;

CREATE TABLE IF NOT EXISTS usuarios (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    usuario VARCHAR(50) NOT NULL UNIQUE,
    senha VARCHAR(100) NOT NULL,
    endereco VARCHAR(150) NOT NULL DEFAULT 'RUA RIO BONITO, 845',
    cep VARCHAR(20) NOT NULL DEFAULT 'CEP 03023-000',
    patio INT NULL
);

CREATE TABLE IF NOT EXISTS codigos_marcas (
    codigo CHAR(3) NOT NULL PRIMARY KEY,
    marca VARCHAR(120) NOT NULL
);

CREATE TABLE IF NOT EXISTS formas_pagamento (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    descricao VARCHAR(30) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS placas (
    placa VARCHAR(10) NOT NULL PRIMARY KEY,
    codigo CHAR(3) NOT NULL,
    marca VARCHAR(120) NOT NULL,
    CONSTRAINT fk_placas_codigos_marcas
        FOREIGN KEY (codigo) REFERENCES codigos_marcas(codigo)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS veiculos (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    numero_entrada VARCHAR(20) NOT NULL,
    placa VARCHAR(10) NOT NULL,
    patio INT NULL,
    data_hora_entrada DATETIME NOT NULL,
    data_hora_saida DATETIME NULL,
    tempo_permanencia VARCHAR(20) NULL,
    valor_cobrado DECIMAL(10,2) NULL,
    forma_pagamento VARCHAR(30) NULL,
    cpf VARCHAR(20) NULL,
    numero_rps INT NULL,
    numero_nfse VARCHAR(30) NULL,
    codigo_verificacao_nfse VARCHAR(60) NULL,
    status_nfse VARCHAR(30) NULL,
    xml_rps LONGTEXT NULL,
    resposta_nfse LONGTEXT NULL,
    CONSTRAINT fk_veiculos_placas
        FOREIGN KEY (placa) REFERENCES placas(placa)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    INDEX idx_veiculos_placa (placa),
    INDEX idx_veiculos_entrada (data_hora_entrada),
    UNIQUE KEY uk_veiculos_numero_entrada (numero_entrada)
);

CREATE TABLE IF NOT EXISTS precos (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    descricao VARCHAR(100) NOT NULL,
    hora_inicial INT NOT NULL,
    hora_final INT NULL,
    valor DECIMAL(10,2) NOT NULL,
    tipo_valor VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS fechamento_caixa (
    data DATE NOT NULL,
    patio INT NOT NULL DEFAULT 1,
    troco_inicial DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    maquininha DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    dinheiro DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    PRIMARY KEY (data, patio)
);

CREATE TABLE IF NOT EXISTS controle_rps (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    serie_rps VARCHAR(10) NOT NULL UNIQUE,
    ultimo_numero_rps INT NOT NULL DEFAULT 0,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS empresa_fiscal (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    razao_social VARCHAR(150) NOT NULL,
    nome_fantasia VARCHAR(150) NULL,
    cnpj VARCHAR(18) NOT NULL,
    ccm VARCHAR(20) NOT NULL,
    inscricao_municipal VARCHAR(30) NULL,
    regime_tributario VARCHAR(50) NOT NULL,
    optante_simples_nacional TINYINT(1) NOT NULL DEFAULT 0,
    data_inicio_simples DATE NULL,
    email VARCHAR(150) NULL,
    telefone VARCHAR(30) NULL,
    codigo_servico VARCHAR(20) NULL,
    aliquota_iss DECIMAL(6,2) NULL,
    serie_rps VARCHAR(10) NULL,
    senha_web VARCHAR(100) NULL,
    usuario_emissor VARCHAR(60) NULL,
    ambiente VARCHAR(20) NOT NULL DEFAULT 'PRODUCAO',
    ativo TINYINT(1) NOT NULL DEFAULT 1,
    ws_endpoint VARCHAR(255) NULL,
    ws_soap_action VARCHAR(255) NULL,
    certificado_caminho VARCHAR(255) NULL,
    certificado_chave_caminho VARCHAR(255) NULL,
    certificado_senha VARCHAR(255) NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS nfse_envios (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    veiculo_id INT NOT NULL,
    numero_rps INT NOT NULL,
    numero_nfse VARCHAR(30) NULL,
    status_envio VARCHAR(30) NOT NULL,
    mensagem_retorno TEXT NULL,
    xml_rps LONGTEXT NULL,
    resposta_nfse LONGTEXT NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_nfse_envios_veiculos
        FOREIGN KEY (veiculo_id) REFERENCES veiculos(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS nfse_avulsa_envios (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    numero_rps INT NOT NULL,
    documento_tomador VARCHAR(20) NOT NULL,
    valor_servico DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    observacao_nf TEXT NULL,
    numero_nfse VARCHAR(30) NULL,
    status_envio VARCHAR(30) NOT NULL,
    mensagem_retorno TEXT NULL,
    xml_rps LONGTEXT NULL,
    resposta_nfse LONGTEXT NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO formas_pagamento (descricao) VALUES
('PIX'),
('DINHEIRO'),
('CARTAO')
ON DUPLICATE KEY UPDATE descricao = VALUES(descricao);

INSERT INTO controle_rps (serie_rps, ultimo_numero_rps)
VALUES ('RPS', 0)
ON DUPLICATE KEY UPDATE ultimo_numero_rps = ultimo_numero_rps;

INSERT INTO precos (descricao, hora_inicial, hora_final, valor, tipo_valor) VALUES
('ATE 1 HORA', 0, 1, 10.00, 'FIXO'),
('ACIMA DE 1 HORA', 1, 2, 5.00, 'ADICIONAL'),
('ACIMA DE 2 HORAS', 2, 3, 5.00, 'ADICIONAL'),
('ACIMA DE 3 HORAS', 3, 4, 5.00, 'ADICIONAL'),
('ACIMA DE 4 HORAS', 4, 5, 5.00, 'ADICIONAL'),
('ACIMA DE 5 HORAS', 5, 6, 5.00, 'ADICIONAL'),
('ACIMA DE 6 HORAS', 6, NULL, 35.00, 'FIXO')
ON DUPLICATE KEY UPDATE
    descricao = VALUES(descricao),
    hora_inicial = VALUES(hora_inicial),
    hora_final = VALUES(hora_final),
    valor = VALUES(valor),
    tipo_valor = VALUES(tipo_valor);

INSERT INTO usuarios (usuario, senha, endereco, cep, patio)
VALUES ('ROOT', 'ROOT', 'RUA RIO BONITO, 845', 'CEP 03023-000', NULL)
ON DUPLICATE KEY UPDATE
    senha = VALUES(senha),
    endereco = VALUES(endereco),
    cep = VALUES(cep),
    patio = VALUES(patio);

INSERT INTO empresa_fiscal (
    razao_social,
    nome_fantasia,
    cnpj,
    ccm,
    inscricao_municipal,
    regime_tributario,
    optante_simples_nacional,
    data_inicio_simples,
    ambiente,
    ativo,
    ws_endpoint,
    ws_soap_action
) VALUES (
    'SE MEGA PARK TRANSPORTES LTDA',
    'SE MEGA PARK',
    '10.809.969/0001-61',
    '3.913.775-9',
    '3.913.775-9',
    'SIMPLES NACIONAL',
    1,
    '2009-04-30',
    'PRODUCAO',
    1,
    'https://nfews.prefeitura.sp.gov.br/lotenfe.asmx',
    'http://www.prefeitura.sp.gov.br/nfe/ws/envioLoteRPS'
)
ON DUPLICATE KEY UPDATE
    razao_social = VALUES(razao_social),
    nome_fantasia = VALUES(nome_fantasia),
    ccm = VALUES(ccm),
    inscricao_municipal = VALUES(inscricao_municipal),
    regime_tributario = VALUES(regime_tributario),
    optante_simples_nacional = VALUES(optante_simples_nacional),
    data_inicio_simples = VALUES(data_inicio_simples),
    ambiente = VALUES(ambiente),
    ativo = VALUES(ativo),
    ws_endpoint = VALUES(ws_endpoint),
    ws_soap_action = VALUES(ws_soap_action);

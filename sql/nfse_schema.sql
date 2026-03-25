USE estacionamento;

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

CREATE TABLE IF NOT EXISTS controle_rps (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    serie_rps VARCHAR(10) NOT NULL UNIQUE,
    ultimo_numero_rps INT NOT NULL DEFAULT 0,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

ALTER TABLE veiculos
ADD COLUMN IF NOT EXISTS cpf VARCHAR(20) NULL AFTER forma_pagamento;

ALTER TABLE veiculos
ADD COLUMN IF NOT EXISTS numero_rps INT NULL AFTER cpf;

ALTER TABLE veiculos
ADD COLUMN IF NOT EXISTS numero_nfse VARCHAR(30) NULL AFTER numero_rps;

ALTER TABLE veiculos
ADD COLUMN IF NOT EXISTS codigo_verificacao_nfse VARCHAR(60) NULL AFTER numero_nfse;

ALTER TABLE veiculos
ADD COLUMN IF NOT EXISTS status_nfse VARCHAR(30) NULL AFTER codigo_verificacao_nfse;

ALTER TABLE veiculos
ADD COLUMN IF NOT EXISTS xml_rps LONGTEXT NULL AFTER status_nfse;

ALTER TABLE veiculos
ADD COLUMN IF NOT EXISTS resposta_nfse LONGTEXT NULL AFTER xml_rps;

ALTER TABLE empresa_fiscal
ADD COLUMN IF NOT EXISTS certificado_caminho VARCHAR(255) NULL AFTER ws_soap_action;

ALTER TABLE empresa_fiscal
ADD COLUMN IF NOT EXISTS certificado_chave_caminho VARCHAR(255) NULL AFTER certificado_caminho;

ALTER TABLE empresa_fiscal
ADD COLUMN IF NOT EXISTS certificado_senha VARCHAR(255) NULL AFTER certificado_chave_caminho;

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

INSERT INTO controle_rps (serie_rps, ultimo_numero_rps)
VALUES ('RPS', 0)
ON DUPLICATE KEY UPDATE ultimo_numero_rps = ultimo_numero_rps;

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

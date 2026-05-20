CREATE DATABASE IF NOT EXISTS sistema_veiculos;
USE sistema_veiculos;

-- =========================
-- TABELA: USERS
-- =========================
CREATE TABLE users (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(30) NOT NULL DEFAULT 'user',
    status BOOLEAN NOT NULL DEFAULT TRUE,
    create_date DATE NOT NULL,
    hour_date DATETIME NOT NULL
);

-- =========================
-- TABELA: MODELOS
-- =========================
CREATE TABLE modelos (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    marca VARCHAR(100) NOT NULL,
    nome VARCHAR(100) NOT NULL,
    create_date DATE NOT NULL,
    hour_date DATETIME NOT NULL
);

-- =========================
-- TABELA: VERSOES
-- Relacao:
-- modelos 1:N versoes
-- =========================
CREATE TABLE versoes (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    modelo_id BIGINT UNSIGNED NOT NULL,
    nome VARCHAR(100) NOT NULL,
    create_date DATE NOT NULL,
    hour_date DATETIME NOT NULL,

    CONSTRAINT fk_versoes_modelos
        FOREIGN KEY (modelo_id)
        REFERENCES modelos(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

-- =========================
-- TABELA: VEICULOS
-- Relacao:
-- versoes 1:N veiculos
-- =========================
CREATE TABLE veiculos (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    versao_id BIGINT UNSIGNED NOT NULL,
    motorizacao VARCHAR(100) NOT NULL,
    potencia_cv INT NOT NULL,
    transmissao VARCHAR(50) NOT NULL,
    tracao VARCHAR(50) NOT NULL,
    status BOOLEAN NOT NULL DEFAULT TRUE,
    create_date DATE NOT NULL,
    hour_date DATETIME NOT NULL,

    CONSTRAINT fk_veiculos_versoes
        FOREIGN KEY (versao_id)
        REFERENCES versoes(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

-- =========================
-- TABELA: METRICAS_VEICULOS
-- Relacoes:
-- veiculos 1:N metricas_veiculos
-- users 1:N metricas_veiculos
-- =========================
CREATE TABLE metricas_veiculos (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    veiculo_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,
    preco_sugerido DECIMAL(12,2) NOT NULL,
    pacote_equipamentos JSON NULL,
    observacao VARCHAR(120) NULL,
    create_date DATE NOT NULL,
    hour_date DATETIME NOT NULL,

    CONSTRAINT fk_metricas_veiculos_veiculos
        FOREIGN KEY (veiculo_id)
        REFERENCES veiculos(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT fk_metricas_veiculos_users
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

-- =========================
-- TABELA: LOGS
-- Relacoes:
-- metricas_veiculos 1:N logs
-- users 1:N logs
-- =========================
CREATE TABLE logs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    metrica_veiculo_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,
    acao VARCHAR(50) NOT NULL,
    dados_antes JSON NULL,
    dados_depois JSON NULL,
    ip VARCHAR(45) NULL,
    user_agent VARCHAR(50) NULL,
    create_date DATE NOT NULL,
    hour_date DATETIME NOT NULL,

    CONSTRAINT fk_logs_metricas_veiculos
        FOREIGN KEY (metrica_veiculo_id)
        REFERENCES metricas_veiculos(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT fk_logs_users
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

-- =========================
-- TABELA: PASSWORD_RESET_TOKENS
-- Relacao:
-- users 1:N password_reset_tokens
-- =========================
CREATE TABLE password_reset_tokens (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    token VARCHAR(255) NOT NULL,
    expires_at DATE NOT NULL,
    create_at DATE NOT NULL,
    hour_date DATETIME NOT NULL,

    CONSTRAINT fk_password_reset_tokens_users
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

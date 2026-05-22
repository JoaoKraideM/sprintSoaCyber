CREATE DATABASE IF NOT EXISTS veiculos_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE veiculos_db;

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS logs;
DROP TABLE IF EXISTS logs_auth;
DROP TABLE IF EXISTS password_reset_tokens;
DROP TABLE IF EXISTS metricas_veiculos;
DROP TABLE IF EXISTS veiculos;
DROP TABLE IF EXISTS versoes;
DROP TABLE IF EXISTS modelos;
DROP TABLE IF EXISTS marcas;
DROP TABLE IF EXISTS users;

SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE users (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    nome VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(30) NOT NULL,
    status BOOLEAN NOT NULL DEFAULT TRUE,

    create_date DATE NOT NULL,
    hour_date TIME NOT NULL,
    update_date DATE NULL,
    update_hour TIME NULL,

    UNIQUE KEY uk_users_email (email),
    INDEX idx_users_role (role),
    INDEX idx_users_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE marcas (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    nome VARCHAR(255) NOT NULL,

    create_date DATE NOT NULL,
    hour_date TIME NOT NULL,
    update_date DATE NULL,
    update_hour TIME NULL,

    UNIQUE KEY uk_marcas_nome (nome)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE modelos (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    marca_id BIGINT UNSIGNED NOT NULL,
    nome VARCHAR(100) NOT NULL,

    create_date DATE NOT NULL,
    hour_date TIME NOT NULL,
    update_date DATE NULL,
    update_hour TIME NULL,

    CONSTRAINT fk_modelos_marcas
        FOREIGN KEY (marca_id)
        REFERENCES marcas(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    UNIQUE KEY uk_modelos_marca_nome (marca_id, nome),
    INDEX idx_modelos_marca_id (marca_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE versoes (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    modelo_id BIGINT UNSIGNED NOT NULL,
    nome VARCHAR(100) NOT NULL,

    create_date DATE NOT NULL,
    hour_date TIME NOT NULL,
    update_date DATE NULL,
    update_hour TIME NULL,

    CONSTRAINT fk_versoes_modelos
        FOREIGN KEY (modelo_id)
        REFERENCES modelos(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    UNIQUE KEY uk_versoes_modelo_nome (modelo_id, nome),
    INDEX idx_versoes_modelo_id (modelo_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE veiculos (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    versao_id BIGINT UNSIGNED NOT NULL,
    motorizacao VARCHAR(100) NOT NULL,
    potencia_cv INT NOT NULL,
    transmissao VARCHAR(50) NOT NULL,
    tracao VARCHAR(50) NOT NULL,
    status BOOLEAN NOT NULL DEFAULT TRUE,

    create_date DATE NOT NULL,
    hour_date TIME NOT NULL,
    update_date DATE NULL,
    update_hour TIME NULL,

    CONSTRAINT fk_veiculos_versoes
        FOREIGN KEY (versao_id)
        REFERENCES versoes(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    INDEX idx_veiculos_versao_id (versao_id),
    INDEX idx_veiculos_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE metricas_veiculos (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    veiculo_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,

    preco_sugerido DECIMAL(12,2) NULL,
    pacote_equipamentos JSON NULL,
    observacao VARCHAR(120) NULL,

    create_date DATE NOT NULL,
    hour_date TIME NOT NULL,
    update_date DATE NULL,
    update_hour TIME NULL,

    CONSTRAINT fk_metricas_veiculos_veiculos
        FOREIGN KEY (veiculo_id)
        REFERENCES veiculos(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT fk_metricas_veiculos_users
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    INDEX idx_metricas_veiculos_veiculo_id (veiculo_id),
    INDEX idx_metricas_veiculos_user_id (user_id),
    INDEX idx_metricas_veiculos_create_date (create_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE logs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    metrica_veiculo_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,

    acao VARCHAR(50) NOT NULL,
    dados_antes JSON NULL,
    dados_depois JSON NULL,
    ip VARCHAR(45) NULL,
    user_agent VARCHAR(255) NULL,

    create_date DATE NOT NULL,
    hour_date TIME NOT NULL,
    update_date DATE NULL,
    update_hour TIME NULL,

    CONSTRAINT fk_logs_metricas_veiculos
        FOREIGN KEY (metrica_veiculo_id)
        REFERENCES metricas_veiculos(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT fk_logs_users
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    INDEX idx_logs_metrica_veiculo_id (metrica_veiculo_id),
    INDEX idx_logs_user_id (user_id),
    INDEX idx_logs_acao (acao),
    INDEX idx_logs_create_date (create_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE logs_auth (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    user_id BIGINT UNSIGNED NULL,
    user_agent VARCHAR(255) NULL,
    address VARCHAR(100) NULL,
    ip VARCHAR(45) NULL,

    create_date DATE NOT NULL,
    hour_date TIME NOT NULL,
    expires_at DATETIME NULL,
    status BOOLEAN NOT NULL DEFAULT FALSE,

    CONSTRAINT fk_logs_auth_users
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,

    INDEX idx_logs_auth_user_id (user_id),
    INDEX idx_logs_auth_address (address),
    INDEX idx_logs_auth_ip (ip),
    INDEX idx_logs_auth_status (status),
    INDEX idx_logs_auth_create_date (create_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE password_reset_tokens (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    user_id BIGINT UNSIGNED NOT NULL,
    token VARCHAR(255) NOT NULL,
    expires_at DATETIME NOT NULL,

    create_at DATE NOT NULL,
    hour_date TIME NOT NULL,

    CONSTRAINT fk_password_reset_tokens_users
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    INDEX idx_password_reset_tokens_user_id (user_id),
    INDEX idx_password_reset_tokens_token (token),
    INDEX idx_password_reset_tokens_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

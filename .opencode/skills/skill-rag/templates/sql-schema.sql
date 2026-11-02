-- skill-rag MySQL schema
-- Database: mydb

CREATE DATABASE IF NOT EXISTS `mydb`
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE `mydb`;

CREATE TABLE IF NOT EXISTS `rag_sources` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `source_path` VARCHAR(1024) NOT NULL,
  `source_name` VARCHAR(255) NOT NULL,
  `doc_type` VARCHAR(100) NULL,
  `title` VARCHAR(512) NULL,
  `source_hash` CHAR(64) NOT NULL,
  `status` VARCHAR(32) NOT NULL DEFAULT 'active',
  `last_scanned_at` DATETIME NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_rag_sources_path` (`source_path`),
  KEY `idx_rag_sources_hash` (`source_hash`),
  KEY `idx_rag_sources_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `rag_chunks` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `source_id` BIGINT UNSIGNED NOT NULL,
  `chunk_index` INT NOT NULL,
  `chunk_title` VARCHAR(512) NULL,
  `content` LONGTEXT NOT NULL,
  `chunk_content` LONGTEXT NOT NULL,
  `summary` TEXT NULL,
  `keywords` TEXT NULL,
  `tags` TEXT NULL,
  `rag_model` VARCHAR(128) NULL,
  `embedding_model` VARCHAR(128) NULL,
  `score` DECIMAL(10,6) NULL,
  `status` VARCHAR(32) NOT NULL DEFAULT 'active',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_rag_chunks_source_index` (`source_id`, `chunk_index`),
  KEY `idx_rag_chunks_source_id` (`source_id`),
  KEY `idx_rag_chunks_status` (`status`),
  KEY `idx_rag_chunks_score` (`score`),
  FULLTEXT KEY `ft_rag_chunks_text` (`chunk_title`, `summary`, `keywords`, `tags`, `content`, `chunk_content`),
  CONSTRAINT `fk_rag_chunks_source`
    FOREIGN KEY (`source_id`) REFERENCES `rag_sources` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

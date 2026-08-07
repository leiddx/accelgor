-- Generated from Pydantic schemas:
-- - app/schemas/user.py
-- - app/schemas/token.py
-- Target database: MySQL 8+

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `tokens`;
DROP TABLE IF EXISTS `users`;

CREATE TABLE `users` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(64) NOT NULL,
  `phone` VARCHAR(20) NOT NULL,
  `email` VARCHAR(255) NOT NULL,
  `password` VARCHAR(255) NOT NULL,
  `salt` VARCHAR(255) NOT NULL,
  `scope` VARCHAR(128) NOT NULL DEFAULT 'user',
  `created` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `idx_users_username` (`username`),
  KEY `idx_users_phone` (`phone`),
  KEY `idx_users_email` (`email`),
  KEY `idx_users_password` (`password`),
  KEY `idx_users_salt` (`salt`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `tokens` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user` BIGINT UNSIGNED NOT NULL,
  `value` VARCHAR(512) NOT NULL,
  `refresh` VARCHAR(512) NOT NULL,
  `expire` DATETIME(6) NOT NULL,
  `scope` VARCHAR(128) NOT NULL,
  `created` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `idx_tokens_user` (`user`),
  KEY `idx_tokens_value` (`value`),
  KEY `idx_tokens_refresh` (`refresh`),
  CONSTRAINT `fk_tokens_user` FOREIGN KEY (`user`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

SET FOREIGN_KEY_CHECKS = 1;

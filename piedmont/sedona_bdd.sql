-- -----------------------------------------------------
-- Schema sedona
-- -----------------------------------------------------
-- Se usa utf8mb4 para soporte completo de Unicode (emojis, apellidos con caracteres especiales, etc)
CREATE SCHEMA IF NOT EXISTS `sedona` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `sedona`;

-- -----------------------------------------------------
-- Table `campus`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `campus` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(45) NOT NULL,         -- Ej: 'San Joaquín'
  PRIMARY KEY (`id`)
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `semestre`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `semestre` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `campus_id` INT UNSIGNED NOT NULL,
  `codigo` VARCHAR(20) NOT NULL,          -- Ej: '2024-1' (Aumentado a 20 por si acaso)
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uq_campus_semestre` (`campus_id` ASC, `codigo` ASC),
  CONSTRAINT `fk_semestre_campus`
    FOREIGN KEY (`campus_id`)
    REFERENCES `campus` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `asignatura`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `asignatura` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `semestre_id` INT UNSIGNED NOT NULL,
  `codigo` VARCHAR(20) NOT NULL,          -- Ej: 'INF155'
  `nombre` VARCHAR(150) NOT NULL,         -- Ej: 'Programación'
  `departamento` VARCHAR(100) NOT NULL,   -- Ej: 'Informática'
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uq_semestre_asignatura` (`semestre_id` ASC, `codigo` ASC),
  CONSTRAINT `fk_asignatura_semestre`
    FOREIGN KEY (`semestre_id`)
    REFERENCES `semestre` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `paralelo`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `paralelo` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `asignatura_id` INT UNSIGNED NOT NULL,
  `paralelo` VARCHAR(40) NOT NULL,        -- Ej: '203', '100', '200 (Modalidad Online)'
  `cupos` INT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uq_asignatura_paralelo` (`asignatura_id` ASC, `paralelo` ASC),
  CONSTRAINT `fk_paralelo_asignatura`
    FOREIGN KEY (`asignatura_id`)
    REFERENCES `asignatura` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `profesor`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `profesor` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(100) NOT NULL,          -- Ej: 'Juan Pérez'
  PRIMARY KEY (`id`),
  UNIQUE INDEX `nombre_UNIQUE` (`nombre` ASC)
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `paralelo_profesor` (Relación muchos a muchos)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `paralelo_profesor` (
  `paralelo_id` INT UNSIGNED NOT NULL,
  `profesor_id` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`paralelo_id`, `profesor_id`),
  CONSTRAINT `fk_paralelo_profesor_paralelo`
    FOREIGN KEY (`paralelo_id`)
    REFERENCES `paralelo` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_paralelo_profesor_profesor`
    FOREIGN KEY (`profesor_id`)
    REFERENCES `profesor` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `horario` (Bloques por día)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `horario` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `paralelo_id` INT UNSIGNED NOT NULL,
  `dia_semana` TINYINT UNSIGNED NOT NULL,  -- 1: Lunes, ..., 7: Domingo
  `bloque_inicio` TINYINT UNSIGNED NOT NULL, -- 1: bloque combinado 1-2; 2: bloque combinado 3-4, etc
  `sala` VARCHAR(40) NOT NULL,             -- Ej: 'A001'
  PRIMARY KEY (`id`),
  INDEX `idx_paralelo_dia_bloque` (`paralelo_id` ASC, `dia_semana` ASC, `bloque_inicio` ASC),
  CONSTRAINT `fk_horario_paralelo`
    FOREIGN KEY (`paralelo_id`)
    REFERENCES `paralelo` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB;
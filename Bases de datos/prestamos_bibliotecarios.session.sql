-- Active: 1795148538331@@127.0.0.1@3306@prestamos_bibliotecarios
SET NAMES utf8mb4;

DROP DATABASE IF EXISTS prestamos_bibliotecarios;

CREATE DATABASE prestamos_bibliotecarios
CHARACTER SET utf8mb4
COLLATE utf8mb4_general_ci;

USE prestamos_bibliotecarios;

CREATE TABLE autor(
    num_id INT PRIMARY KEY AUTO_INCREMENT,
    nombre_pila VARCHAR(50) NOT NULL,
    primer_ap VARCHAR(50) NOT NULL,
    segundo_ap VARCHAR(50)
);

CREATE TABLE categoria(
    codigo VARCHAR(5) PRIMARY KEY,
    genero VARCHAR(30) NOT NULL
);

CREATE TABLE tipo(
    id_tipo INT PRIMARY KEY AUTO_INCREMENT,
    tipo_obra VARCHAR(50) NOT NULL
);

CREATE TABLE pais(
    clave VARCHAR(5) PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL
);

CREATE TABLE proveedor(
    RFC VARCHAR(13) PRIMARY KEY,
    nombre_empresa VARCHAR(50) NOT NULL
);

CREATE TABLE usuario(
    id_usuario INT PRIMARY KEY AUTO_INCREMENT,
    nombre_pila VARCHAR(50) NOT NULL,
    primer_ap VARCHAR(50) NOT NULL,
    segundo_ap VARCHAR(50),
    dir_calle VARCHAR(30) NOT NULL,
    dir_numero VARCHAR(10) NOT NULL,
    dir_colonia VARCHAR(50) NOT NULL
);

CREATE TABLE empleado(
    id_empleado INT PRIMARY KEY AUTO_INCREMENT,
    nombre_pila VARCHAR(50) NOT NULL,
    primer_ap VARCHAR(50) NOT NULL,
    segundo_ap VARCHAR(50),
    nombre_user VARCHAR(30) NOT NULL UNIQUE,
    contraseña VARCHAR(50) NOT NULL
);

CREATE TABLE localizacion(
    id_localizacion INT PRIMARY KEY AUTO_INCREMENT,
    estante INT NOT NULL,
    seccion VARCHAR(50) NOT NULL,
    pasillo INT NOT NULL
);

CREATE TABLE obra(
    isbn VARCHAR(17) PRIMARY KEY,
    titulo VARCHAR(50) NOT NULL,
    subtitulo VARCHAR(100),
    año_publicacion INT NOT NULL,
    num_paginas INT NOT NULL,
    tipo INT NOT NULL,
    categoria VARCHAR(5) NOT NULL,
    FOREIGN KEY (tipo) REFERENCES tipo(id_tipo),
    FOREIGN KEY (categoria) REFERENCES categoria(codigo)
);

CREATE TABLE autor_obra(
    autor INT,
    obra VARCHAR(17),
    PRIMARY KEY (autor, obra),
    FOREIGN KEY (autor) REFERENCES autor(num_id),
    FOREIGN KEY (obra) REFERENCES obra(isbn)
);

CREATE TABLE editorial(
    id_editorial INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(50) NOT NULL,
    pais VARCHAR(5) NOT NULL,
    FOREIGN KEY (pais) REFERENCES pais(clave)
);

CREATE TABLE obra_editorial(
    editorial INT,
    obra VARCHAR(17),
    PRIMARY KEY (editorial, obra),
    FOREIGN KEY (editorial) REFERENCES editorial(id_editorial),
    FOREIGN KEY (obra) REFERENCES obra(isbn)
);

CREATE TABLE ejemplar(
    obra VARCHAR(17),
    ejemplar INT NOT NULL,
    localizacion INT NOT NULL,
    PRIMARY KEY (obra, ejemplar),
    FOREIGN KEY (obra) REFERENCES obra(isbn),
    FOREIGN KEY (localizacion) REFERENCES localizacion(id_localizacion)
);

CREATE TABLE prestamo(
    folio INT PRIMARY KEY AUTO_INCREMENT,
    fecha_salida DATE NOT NULL,
    fecha_limite DATE NOT NULL,
    empleado INT NOT NULL,
    usuario INT NOT NULL,
    FOREIGN KEY (empleado) REFERENCES empleado(id_empleado),
    FOREIGN KEY (usuario) REFERENCES usuario(id_usuario)
);

CREATE TABLE prestamo_ejemplar(
    obra VARCHAR(17),
    ejemplar INT,
    prestamo INT,
    PRIMARY KEY (obra, ejemplar, prestamo),
    FOREIGN KEY (obra, ejemplar) REFERENCES ejemplar(obra, ejemplar),
    FOREIGN KEY (prestamo) REFERENCES prestamo(folio)
);

CREATE TABLE devolucion(
    id_devolucion INT PRIMARY KEY AUTO_INCREMENT,
    fecha_devolucion DATE NOT NULL,
    empleado INT NOT NULL,
    obra VARCHAR(17) NOT NULL,
    ejemplar INT NOT NULL,
    prestamo INT NOT NULL,
    UNIQUE (obra, ejemplar, prestamo),
    FOREIGN KEY (empleado) REFERENCES empleado(id_empleado),
    FOREIGN KEY (obra, ejemplar, prestamo) REFERENCES prestamo_ejemplar(obra, ejemplar, prestamo)
);

CREATE TABLE multa(
    id_multa INT PRIMARY KEY AUTO_INCREMENT,
    devolucion INT NOT NULL UNIQUE,
    estado VARCHAR(15) NOT NULL,
    monto_dia DECIMAL(10,2) NOT NULL,
    dias_retraso INT NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (devolucion) REFERENCES devolucion(id_devolucion)
);

CREATE TABLE telefono_usuario(
    numero INT PRIMARY KEY AUTO_INCREMENT,
    num_tel VARCHAR(20) NOT NULL,
    usuario INT NOT NULL,
    FOREIGN KEY (usuario) REFERENCES usuario(id_usuario)
);

CREATE TABLE telefono_proveedor(
    numero INT PRIMARY KEY AUTO_INCREMENT,
    telefono VARCHAR(20) NOT NULL,
    proveedor VARCHAR(13) NOT NULL,
    FOREIGN KEY (proveedor) REFERENCES proveedor(RFC)
);

CREATE TABLE abastecimiento_obra(
    proveedor VARCHAR(13),
    obra VARCHAR(17),
    fecha_adquisicion DATE NOT NULL,
    cantidad INT NOT NULL,
    PRIMARY KEY (proveedor, obra),
    FOREIGN KEY (proveedor) REFERENCES proveedor(RFC),
    FOREIGN KEY (obra) REFERENCES obra(isbn)
);

-- Registros mínimos para operar el sistema
INSERT INTO localizacion (estante, seccion, pasillo)
VALUES (0, 'Sin asignar / Recepcion', 0);

INSERT INTO empleado (nombre_pila, primer_ap, segundo_ap, nombre_user, `contraseña`)
VALUES ('Administrador', 'Sistema', NULL, 'admin', 'admin123');

ALTER TABLE multa DROP PRIMARY KEY,
 CHANGE id_multa multa INT AUTO_INCREMENT
 , ADD PRIMARY KEY (multa, devolucion);

 SET NAMES utf8mb4;
USE prestamos_bibliotecarios;

-- ============================================================
-- 0. LIMPIEZA SOLO DE CATÁLOGOS E INVENTARIO (NO TOCA USUARIOS NI EMPLEADOS)
-- ============================================================
DELETE FROM abastecimiento_obra;
DELETE FROM ejemplar;
DELETE FROM obra_editorial;
DELETE FROM autor_obra;
DELETE FROM obra;

DELETE FROM editorial;
DELETE FROM telefono_proveedor;
DELETE FROM proveedor;
DELETE FROM autor;
DELETE FROM categoria;
DELETE FROM tipo;
DELETE FROM pais;
DELETE FROM localizacion WHERE id_localizacion > 1;
ALTER TABLE tipo AUTO_INCREMENT = 1;
ALTER TABLE autor AUTO_INCREMENT = 1;
ALTER TABLE editorial AUTO_INCREMENT = 1;
ALTER TABLE telefono_proveedor AUTO_INCREMENT = 1;
ALTER TABLE localizacion AUTO_INCREMENT = 2;

-- Asegura que exista la localización base #1
INSERT IGNORE INTO localizacion (id_localizacion, estante, seccion, pasillo)
VALUES (1, 0, 'Sin asignar / Recepcion', 0);

-- ============================================================
-- 1. PAÍSES
-- ============================================================
INSERT INTO pais (clave, nombre) VALUES
('MEX', 'México'),
('ESP', 'España'),
('USA', 'Estados Unidos'),
('ARG', 'Argentina'),
('COL', 'Colombia'),
('GBR', 'Reino Unido'),
('DEU', 'Alemania'),
('JPN', 'Japón');

-- ============================================================
-- 2. TIPOS DE OBRA
-- ============================================================
INSERT INTO tipo (id_tipo, tipo_obra) VALUES
(1, 'Libro'),
(2, 'Revista'),
(3, 'Enciclopedia'),
(4, 'Manual Técnico'),
(5, 'Tesis');

-- ============================================================
-- 3. CATEGORÍAS / GÉNEROS
-- ============================================================
INSERT INTO categoria (codigo, genero) VALUES
('INF', 'Informática y Sistemas'),
('LIT', 'Literatura Universal'),
('LHA', 'Literatura Hispanoamericana'),
('CIE', 'Divulgación Científica'),
('HIS', 'Historia y Arqueología'),
('FIC', 'Ciencia Ficción'),
('FIL', 'Filosofía y Ensayo'),
('MAT', 'Matemáticas y Física');

-- ============================================================
-- 4. LOCALIZACIONES FÍSICAS
-- ============================================================
INSERT INTO localizacion (id_localizacion, estante, seccion, pasillo) VALUES
(2, 1, 'Informática y Tecnología', 1),
(3, 2, 'Informática y Tecnología', 1),
(4, 1, 'Literatura', 2),
(5, 2, 'Literatura', 2),
(6, 1, 'Ciencias Exactas', 3),
(7, 2, 'Divulgación Científica', 3),
(8, 1, 'Historia y Humanidades', 4),
(9, 1, 'Hemeroteca y Referencia', 5);

-- ============================================================
-- 5. EDITORIALES
-- ============================================================
INSERT INTO editorial (id_editorial, nombre, pais) VALUES
(1, 'McGraw-Hill Interamericana', 'ESP'),
(2, 'Pearson Educación', 'MEX'),
(3, 'MIT Press', 'USA'),
(4, 'Editorial Planeta', 'ESP'),
(5, 'Fondo de Cultura Económica', 'MEX'),
(6, 'Penguin Random House', 'ESP'),
(7, 'Editorial Raíces', 'MEX'),
(8, 'Editorial Crítica', 'ESP'),
(9, 'O''Reilly Media', 'USA'),
(10, 'Editorial Sudamericana', 'ARG');

-- ============================================================
-- 6. PROVEEDORES Y TELÉFONOS
-- ============================================================
INSERT INTO proveedor (RFC, nombre_empresa) VALUES
('DIS890412AB1', 'Distribuidora Mexicana de Libros S.A. de C.V.'),
('PRO951023CD2', 'Proveedora Editorial del Norte S.A.'),
('COM030715EF3', 'Comercializadora Académica Baja S. de R.L.'),
('LIB110228GH4', 'Librerías y Suministros del Pacífico S.A.'),
('IMP180905JK5', 'Importadora Técnica y Científica S.A. de C.V.');

INSERT INTO telefono_proveedor (telefono, proveedor) VALUES
('664-681-1020', 'DIS890412AB1'),
('664-681-1021', 'DIS890412AB1'),
('664-634-4510', 'PRO951023CD2'),
('664-622-7890', 'COM030715EF3'),
('664-622-7891', 'COM030715EF3'),
('664-686-3300', 'LIB110228GH4'),
('55-5207-9400', 'IMP180905JK5'),
('55-5207-9401', 'IMP180905JK5');

-- ============================================================
-- 7. AUTORES
-- ============================================================
INSERT INTO autor (num_id, nombre_pila, primer_ap, segundo_ap) VALUES
(1, 'Abraham', 'Silberschatz', NULL),
(2, 'Henry F.', 'Korth', NULL),
(3, 'S.', 'Sudarshan', NULL),
(4, 'Thomas H.', 'Cormen', NULL),
(5, 'Charles E.', 'Leiserson', NULL),
(6, 'Ronald L.', 'Rivest', NULL),
(7, 'Clifford', 'Stein', NULL),
(8, 'Erich', 'Gamma', NULL),
(9, 'Richard', 'Helm', NULL),
(10, 'Ralph', 'Johnson', NULL),
(11, 'John', 'Vlissides', NULL),
(12, 'Gabriel', 'García', 'Márquez'),
(13, 'Juan', 'Rulfo', NULL),
(14, 'Octavio', 'Paz', 'Lozano'),
(15, 'Carl', 'Sagan', NULL),
(16, 'Stephen', 'Hawking', NULL),
(17, 'Miguel', 'León-Portilla', NULL),
(18, 'Isaac', 'Asimov', NULL),
(19, 'George', 'Orwell', NULL),
(20, 'Ramez', 'Elmasri', NULL),
(21, 'Shamkant B.', 'Navathe', NULL),
(22, 'Eduardo', 'Matos', 'Moctezuma'),
(23, 'Leonardo', 'López', 'Luján'),
(24, 'Jorge Luis', 'Borges', 'Acevedo');

-- ============================================================
-- 8. OBRAS (15 OBRAS REALES)
-- ============================================================
INSERT INTO obra (isbn, titulo, subtitulo, `año_publicacion`, num_paginas, tipo, categoria) VALUES
('978-84-481-9033-0', 'Fundamentos de bases de datos', 'Sexta edición: diseño relacional, SQL y arquitectura', 2014, 932, 1, 'INF'),
('978-0-262-03384-8', 'Introduction to Algorithms', 'Estructuras de datos, complejidad y diseño algorítmico', 2009, 1312, 1, 'INF'),
('978-84-7829-059-8', 'Patrones de diseño', 'Elementos de software orientado a objetos reutilizable', 2002, 392, 4, 'INF'),
('978-84-7829-085-7', 'Fundamentos de sistemas de bases de datos', 'Modelado conceptual, normalización y gestión de transacciones', 2007, 1012, 1, 'INF'),
('978-607-07-2879-2', 'Cien años de soledad', 'Edición conmemorativa de la familia Buendía en Macondo', 1967, 496, 1, 'LHA'),
('978-607-16-0011-0', 'Pedro Páramo', 'Novela fundamental de la narrativa mexicana en Comala', 1955, 132, 1, 'LHA'),
('978-968-16-0301-4', 'El laberinto de la soledad', 'Ensayo sobre la identidad y la cultura mexicana', 1950, 352, 1, 'FIL'),
('978-84-08-05304-0', 'Cosmos', 'Un viaje personal a través de la ciencia y el universo', 1980, 384, 1, 'CIE'),
('978-84-9892-197-7', 'Breve historia del tiempo', 'Del Big Bang a los agujeros negros', 1988, 256, 1, 'CIE'),
('978-968-16-0211-6', 'Visión de los vencidos', 'Relaciones indígenas de la Conquista de México', 1959, 224, 1, 'HIS'),
('978-84-9759-924-5', 'Fundación', 'Crónica galáctica de la psicohistoria y el Imperio', 1951, 264, 1, 'FIC'),
('978-607-31-1633-6', '1984', 'Novela distópica sobre vigilancia y control social', 1949, 328, 1, 'FIC'),
('977-0188-82100-1',  'Arqueología Mexicana', 'Edición especial: Templo Mayor y culturas mesoamericanas', 2024, 96, 2, 'HIS'),
('978-84-206-3312-1', 'Ficciones', 'El jardín de senderos que se bifurcan y Artificios', 1944, 218, 1, 'LHA'),
('978-607-16-4812-9', 'Enciclopedia de Historia Mesoamericana', 'Compendio arqueológico y documental del México antiguo', 2020, 640, 3, 'HIS');

-- ============================================================
-- 9. AUTOR_OBRA (INCLUYE 4 OBRAS CON 3 O 4 AUTORES)
-- ============================================================
INSERT INTO autor_obra (autor, obra) VALUES
-- Fundamentos de bases de datos (3 autores)
(1, '978-84-481-9033-0'),
(2, '978-84-481-9033-0'),
(3, '978-84-481-9033-0'),
-- Introduction to Algorithms (4 autores)
(4, '978-0-262-03384-8'),
(5, '978-0-262-03384-8'),
(6, '978-0-262-03384-8'),
(7, '978-0-262-03384-8'),
-- Patrones de diseño (4 autores)
(8, '978-84-7829-059-8'),
(9, '978-84-7829-059-8'),
(10, '978-84-7829-059-8'),
(11, '978-84-7829-059-8'),
-- Fundamentos de sistemas de bases de datos (2 autores)
(20, '978-84-7829-085-7'),
(21, '978-84-7829-085-7'),
-- Obras de 1 y 2 autores
(12, '978-607-07-2879-2'),
(13, '978-607-16-0011-0'),
(14, '978-968-16-0301-4'),
(15, '978-84-08-05304-0'),
(16, '978-84-9892-197-7'),
(17, '978-968-16-0211-6'),
(18, '978-84-9759-924-5'),
(19, '978-607-31-1633-6'),
(22, '977-0188-82100-1'),
(23, '977-0188-82100-1'),
(24, '978-84-206-3312-1'),
-- Enciclopedia de Historia Mesoamericana (3 autores)
(17, '978-607-16-4812-9'),
(22, '978-607-16-4812-9'),
(23, '978-607-16-4812-9');

-- ============================================================
-- 10. OBRA_EDITORIAL (Cien años de soledad tiene 2 editoriales)
-- ============================================================
INSERT INTO obra_editorial (editorial, obra) VALUES
(1, '978-84-481-9033-0'),
(3, '978-0-262-03384-8'),
(2, '978-84-7829-059-8'),
(2, '978-84-7829-085-7'),
(6, '978-607-07-2879-2'),
(10, '978-607-07-2879-2'),
(5, '978-607-16-0011-0'),
(5, '978-968-16-0301-4'),
(4, '978-84-08-05304-0'),
(8, '978-84-9892-197-7'),
(5, '978-968-16-0211-6'),
(6, '978-84-9759-924-5'),
(6, '978-607-31-1633-6'),
(7, '977-0188-82100-1'),
(10, '978-84-206-3312-1'),
(5, '978-607-16-4812-9');

-- ============================================================
-- 11. ABASTECIMIENTO_OBRA (4 EJEMPLARES POR OBRA = 60 TOTAL)
-- ============================================================
INSERT INTO abastecimiento_obra (proveedor, obra, fecha_adquisicion, cantidad) VALUES
('IMP180905JK5', '978-84-481-9033-0', '2026-09-10', 4),
('IMP180905JK5', '978-0-262-03384-8', '2026-09-10', 4),
('COM030715EF3', '978-84-7829-059-8', '2026-09-12', 4),
('COM030715EF3', '978-84-7829-085-7', '2026-09-12', 4),
('DIS890412AB1', '978-607-07-2879-2', '2026-09-15', 4),
('DIS890412AB1', '978-607-16-0011-0', '2026-09-15', 4),
('DIS890412AB1', '978-968-16-0301-4', '2026-09-18', 4),
('PRO951023CD2', '978-84-08-05304-0', '2026-09-20', 4),
('PRO951023CD2', '978-84-9892-197-7', '2026-09-20', 4),
('LIB110228GH4', '978-968-16-0211-6', '2026-09-25', 4),
('LIB110228GH4', '978-84-9759-924-5', '2026-09-25', 4),
('PRO951023CD2', '978-607-31-1633-6', '2026-10-01', 4),
('LIB110228GH4', '977-0188-82100-1',  '2026-10-03', 4),
('DIS890412AB1', '978-84-206-3312-1', '2026-10-05', 4),
('COM030715EF3', '978-607-16-4812-9', '2026-10-10', 4);

-- ============================================================
-- 12. EJEMPLARES (4 COPIAS CONSECUTIVAS POR OBRA = 60 TOTAL)
-- ============================================================
INSERT INTO ejemplar (obra, ejemplar, localizacion) VALUES
-- Informática y Tecnología (Loc 2 y 3)
('978-84-481-9033-0', 1, 2), ('978-84-481-9033-0', 2, 2), ('978-84-481-9033-0', 3, 2), ('978-84-481-9033-0', 4, 2),
('978-0-262-03384-8', 1, 2), ('978-0-262-03384-8', 2, 2), ('978-0-262-03384-8', 3, 2), ('978-0-262-03384-8', 4, 2),
('978-84-7829-059-8', 1, 3), ('978-84-7829-059-8', 2, 3), ('978-84-7829-059-8', 3, 3), ('978-84-7829-059-8', 4, 3),
('978-84-7829-085-7', 1, 3), ('978-84-7829-085-7', 2, 3), ('978-84-7829-085-7', 3, 3), ('978-84-7829-085-7', 4, 3),
-- Literatura (Loc 4 y 5)
('978-607-07-2879-2', 1, 4), ('978-607-07-2879-2', 2, 4), ('978-607-07-2879-2', 3, 4), ('978-607-07-2879-2', 4, 4),
('978-607-16-0011-0', 1, 4), ('978-607-16-0011-0', 2, 4), ('978-607-16-0011-0', 3, 4), ('978-607-16-0011-0', 4, 4),
('978-84-206-3312-1', 1, 4), ('978-84-206-3312-1', 2, 4), ('978-84-206-3312-1', 3, 4), ('978-84-206-3312-1', 4, 4),
('978-84-9759-924-5', 1, 5), ('978-84-9759-924-5', 2, 5), ('978-84-9759-924-5', 3, 5), ('978-84-9759-924-5', 4, 5),
('978-607-31-1633-6', 1, 5), ('978-607-31-1633-6', 2, 5), ('978-607-31-1633-6', 3, 5), ('978-607-31-1633-6', 4, 5),
-- Divulgación Científica (Loc 7)
('978-84-08-05304-0', 1, 7), ('978-84-08-05304-0', 2, 7), ('978-84-08-05304-0', 3, 7), ('978-84-08-05304-0', 4, 7),
('978-84-9892-197-7', 1, 7), ('978-84-9892-197-7', 2, 7), ('978-84-9892-197-7', 3, 7), ('978-84-9892-197-7', 4, 7),
-- Historia y Humanidades (Loc 8)
('978-968-16-0301-4', 1, 8), ('978-968-16-0301-4', 2, 8), ('978-968-16-0301-4', 3, 8), ('978-968-16-0301-4', 4, 8),
('978-968-16-0211-6', 1, 8), ('978-968-16-0211-6', 2, 8), ('978-968-16-0211-6', 3, 8), ('978-968-16-0211-6', 4, 8),
-- Hemeroteca y Referencia (Loc 9)
('977-0188-82100-1',  1, 9), ('977-0188-82100-1',  2, 9), ('977-0188-82100-1',  3, 9), ('977-0188-82100-1',  4, 9),
-- Sin asignar / Recepción (Loc 1, útil para probar Registro 2)
('978-607-16-4812-9', 1, 1), ('978-607-16-4812-9', 2, 1), ('978-607-16-4812-9', 3, 1), ('978-607-16-4812-9', 4, 1);
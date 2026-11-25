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

SET NAMES utf8mb4;
USE prestamos_bibliotecarios;

SET NAMES utf8mb4;
USE prestamos_bibliotecarios;

-- ============================================================
-- 0. LIMPIEZA COMPLETA EN ORDEN DE LLAVES FORÁNEAS
--    (Conserva empleado #1 admin y localizacion #1 base)
-- ============================================================
DELETE FROM multa;
DELETE FROM devolucion;
DELETE FROM prestamo_ejemplar;
DELETE FROM prestamo;
DELETE FROM telefono_usuario;
DELETE FROM usuario;
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

ALTER TABLE tipo AUTO_INCREMENT = 1;
ALTER TABLE autor AUTO_INCREMENT = 1;
ALTER TABLE editorial AUTO_INCREMENT = 1;

-- ============================================================
-- 1. PAÍSES (CÓDIGOS ISO 3166-1 ALPHA-3 REALES)
-- ============================================================
INSERT INTO pais (clave, nombre) VALUES
('MEX', 'México'),
('ESP', 'España'),
('GBR', 'Reino Unido'),
('USA', 'Estados Unidos');

-- ============================================================
-- 2. TIPOS DE OBRA
-- ============================================================
INSERT INTO tipo (id_tipo, tipo_obra) VALUES
(1, 'Libro'),
(2, 'Manual Técnico'),
(3, 'Revista'),
(4, 'Enciclopedia'),
(5, 'Tesis');

-- ============================================================
-- 3. CATEGORÍAS (CLASIFICACIÓN DECIMAL DEWEY REAL)
-- ============================================================
INSERT INTO categoria (codigo, genero) VALUES
('001', 'Metodología e Investigación'),
('005', 'Informática y Programación'),
('100', 'Filosofía'),
('150', 'Psicología'),
('330', 'Economía'),
('530', 'Física'),
('700', 'Arte y Arquitectura'),
('800', 'Literatura Universal'),
('860', 'Literatura en Español'),
('863', 'Cuento'),
('900', 'Historia Universal'),
('972', 'Historia de México');

-- ============================================================
-- 4. EDITORIALES REALES (CON PAÍS DE LA EDICIÓN)
-- ============================================================
INSERT INTO editorial (id_editorial, nombre, pais) VALUES
(1,  'El Colegio de México',       'MEX'),
(2,  'McGraw-Hill Interamericana', 'MEX'),
(3,  'Pearson Educación',          'MEX'),
(4,  'Addison-Wesley',             'ESP'),
(5,  'Debolsillo',                 'ESP'),
(6,  'Ediciones Cátedra',          'ESP'),
(7,  'Ediciones Era',              'MEX'),
(8,  'Ediciones Salamandra',       'ESP'),
(9,  'Editorial Planeta',          'ESP'),
(10, 'Debate',                     'ESP'),
(11, 'Herder Editorial',           'ESP'),
(12, 'Ediciones Siruela',          'ESP'),
(13, 'Phaidon Press',              'GBR'),
(14, 'Cengage Learning',           'MEX');

-- ============================================================
-- 5. AUTORES REALES (29 AUTORES)
-- ============================================================
INSERT INTO autor (num_id, nombre_pila, primer_ap, segundo_ap) VALUES
(1,  'Pablo',            'Escalante',        'Gonzalbo'),
(2,  'Bernardo',         'García',           'Martínez'),
(3,  'Luis',             'Jáuregui',         NULL),
(4,  'Josefina Zoraida', 'Vázquez',          NULL),
(5,  'Elisa',            'Speckman',         'Guerra'),
(6,  'Javier',           'Garciadiego',      NULL),
(7,  'Luis',             'Aboites',          'Aguilar'),
(8,  'Roberto',          'Hernández',        'Sampieri'),
(9,  'Carlos',           'Fernández',        'Collado'),
(10, 'María del Pilar',  'Baptista',         'Lucio'),
(11, 'Francis W.',       'Sears',            NULL),
(12, 'Mark W.',          'Zemansky',         NULL),
(13, 'Hugh D.',          'Young',            NULL),
(14, 'Roger A.',         'Freedman',         NULL),
(15, 'Erich',            'Gamma',            NULL),
(16, 'Richard',          'Helm',             NULL),
(17, 'Ralph',            'Johnson',          NULL),
(18, 'John',             'Vlissides',        NULL),
(19, 'Gabriel',          'García',           'Márquez'),
(20, 'Juan',             'Rulfo',            NULL),
(21, 'José Emilio',      'Pacheco',          NULL),
(22, 'Antoine',          'de Saint-Exupéry', NULL),
(23, 'Carlos',           'Ruiz',             'Zafón'),
(24, 'George',           'Orwell',           NULL),
(25, 'Yuval Noah',       'Harari',           NULL),
(26, 'Viktor E.',        'Frankl',           NULL),
(27, 'Jostein',          'Gaarder',          NULL),
(28, 'Ernst H.',         'Gombrich',         NULL),
(29, 'N. Gregory',       'Mankiw',           NULL),
(30, 'Julio',            'Cortázar',         NULL),
(31, 'Jorge Luis',       'Borges',           NULL);


-- ============================================================
-- 6. OBRAS REALES EN ESPAÑOL (15 EDICIONES VARIADAS)
--    Nota: NULL en subtitulo cuando la edición real no tiene subtítulo
-- ============================================================
INSERT INTO obra (isbn, titulo, subtitulo, `año_publicacion`, num_paginas, tipo, categoria) VALUES
('978-968-12-1139-4', 'Nueva historia mínima de México', NULL, 2004, 315, 1, '972'),
('978-1-4562-2396-0', 'Metodología de la investigación', NULL, 2014, 600, 1, '001'),
('978-607-442-288-7', 'Física universitaria', 'Volumen 1', 2009, 760, 1, '530'),
('978-84-7829-059-8', 'Patrones de diseño', 'Elementos de software orientado a objetos reutilizable', 2002, 392, 2, '005'),
('978-84-9759-220-8', 'Cien años de soledad', NULL, 2003, 496, 1, '860'),
('978-84-376-0418-3', 'Pedro Páramo', NULL, 1983, 192, 1, '860'),
('978-968-411-058-8', 'Las batallas en el desierto', NULL, 1981, 68, 1, '860'),
('978-84-7888-719-4', 'El principito', NULL, 2001, 96, 1, '800'),
('978-84-08-04364-5', 'La sombra del viento', NULL, 2001, 576, 1, '860'),
('978-84-9989-094-4', '1984', NULL, 2013, 352, 1, '800'),
('978-84-9992-622-3', 'Sapiens. De animales a dioses', 'Breve historia de la humanidad', 2014, 496, 1, '900'),
('978-84-254-3202-6', 'El hombre en busca de sentido', NULL, 2015, 168, 1, '150'),
('978-84-7844-815-9', 'El mundo de Sofía', 'Novela sobre la historia de la filosofía', 1994, 640, 1, '100'),
('978-0-7148-9870-4', 'La historia del arte', NULL, 2008, 688, 1, '700'),
('978-607-481-809-3', 'Principios de economía', NULL, 2012, 858, 1, '330'),
('978-84-376-3499-9', 'El Llano en llamas', NULL, 2016, 264, 1, '863'),
('978-607-31-4772-9', 'Bestiario', NULL, 2016, 136, 1, '863'),
('978-607-31-0492-0', 'Ficciones', NULL, 2011, 224, 1, '863');

-- ============================================================
-- 7. AUTOR_OBRA (4 OBRAS CON 3 A 7 AUTORES REALES)
-- ============================================================
INSERT INTO autor_obra (autor, obra) VALUES
-- Nueva historia mínima de México (7 autores)
(1, '978-968-12-1139-4'),
(2, '978-968-12-1139-4'),
(3, '978-968-12-1139-4'),
(4, '978-968-12-1139-4'),
(5, '978-968-12-1139-4'),
(6, '978-968-12-1139-4'),
(7, '978-968-12-1139-4'),
-- Metodología de la investigación (3 autores)
(8,  '978-1-4562-2396-0'),
(9,  '978-1-4562-2396-0'),
(10, '978-1-4562-2396-0'),
-- Física universitaria Vol. 1 (4 autores)
(11, '978-607-442-288-7'),
(12, '978-607-442-288-7'),
(13, '978-607-442-288-7'),
(14, '978-607-442-288-7'),
-- Patrones de diseño (4 autores)
(15, '978-84-7829-059-8'),
(16, '978-84-7829-059-8'),
(17, '978-84-7829-059-8'),
(18, '978-84-7829-059-8'),
-- Obras de 1 autor
(19, '978-84-9759-220-8'),
(20, '978-84-376-0418-3'),
(21, '978-968-411-058-8'),
(22, '978-84-7888-719-4'),
(23, '978-84-08-04364-5'),
(24, '978-84-9989-094-4'),
(25, '978-84-9992-622-3'),
(26, '978-84-254-3202-6'),
(27, '978-84-7844-815-9'),
(28, '978-0-7148-9870-4'),
(29, '978-607-481-809-3'),
(20, '978-84-376-3499-9'),
(30, '978-607-31-4772-9'),
(31, '978-607-31-0492-0'); 

-- ============================================================
-- 8. OBRA_EDITORIAL (EDITORIAL REAL DE CADA EDICIÓN)
-- ============================================================
INSERT INTO obra_editorial (editorial, obra) VALUES
(1,  '978-968-12-1139-4'),
(2,  '978-1-4562-2396-0'),
(3,  '978-607-442-288-7'),
(4,  '978-84-7829-059-8'),
(5,  '978-84-9759-220-8'),
(6,  '978-84-376-0418-3'),
(7,  '978-968-411-058-8'),
(8,  '978-84-7888-719-4'),
(9,  '978-84-08-04364-5'),
(5,  '978-84-9989-094-4'),
(10, '978-84-9992-622-3'),
(11, '978-84-254-3202-6'),
(12, '978-84-7844-815-9'),
(13, '978-0-7148-9870-4'),
(14, '978-607-481-809-3'),
(6, '978-84-376-3499-9'),
(5, '978-607-31-4772-9'),
(5, '978-607-31-0492-0');



SET NAMES utf8mb4;
USE prestamos_bibliotecarios;

-- ============================================================
-- 0. REINICIO DE TABLAS OPERATIVAS FICTICIAS
-- ============================================================
DELETE FROM multa;
DELETE FROM devolucion;
DELETE FROM prestamo_ejemplar;
DELETE FROM prestamo;
DELETE FROM telefono_usuario;
DELETE FROM usuario;
DELETE FROM empleado WHERE id_empleado > 1;
DELETE FROM abastecimiento_obra;
DELETE FROM ejemplar;
DELETE FROM telefono_proveedor;
DELETE FROM proveedor;
DELETE FROM localizacion WHERE id_localizacion > 1;

ALTER TABLE multa AUTO_INCREMENT = 1;
ALTER TABLE devolucion AUTO_INCREMENT = 1;
ALTER TABLE prestamo AUTO_INCREMENT = 1;
ALTER TABLE telefono_usuario AUTO_INCREMENT = 1;
ALTER TABLE usuario AUTO_INCREMENT = 1;
ALTER TABLE empleado AUTO_INCREMENT = 2;
ALTER TABLE telefono_proveedor AUTO_INCREMENT = 1;
ALTER TABLE localizacion AUTO_INCREMENT = 2;

INSERT IGNORE INTO localizacion (id_localizacion, estante, seccion, pasillo)
VALUES (1, 0, 'Sin asignar / Recepcion', 0);

INSERT IGNORE INTO empleado (id_empleado, nombre_pila, primer_ap, segundo_ap, nombre_user, `contraseña`)VALUES 
(1, 'Administrador', 'Sistema', NULL, 'admin', 'admin123'),

-- ============================================================
-- 1. LOCALIZACIONES DE LA BIBLIOTECA
-- ============================================================
INSERT INTO localizacion (id_localizacion, estante, seccion, pasillo) VALUES
(2, 1, 'Historia y Ciencias Sociales', 1),
(3, 2, 'Ciencias Exactas y Tecnología', 1),
(4, 1, 'Literatura en Español', 2),
(5, 2, 'Literatura Universal', 2),
(6, 1, 'Filosofía y Psicología', 3),
(7, 2, 'Arte y Economía', 3);

-- ============================================================
-- 2. PROVEEDORES Y TELÉFONOS
-- ============================================================
INSERT INTO proveedor (RFC, nombre_empresa) VALUES
('DIS890412AB1', 'Distribuidora Mexicana de Libros S.A. de C.V.'),
('PRO951023CD2', 'Proveedora Editorial del Norte S.A.'),
('COM030715EF3', 'Comercializadora Académica Baja S. de R.L.'),
('IMP180905JK5', 'Importadora Cultural y Editorial S.A. de C.V.');

INSERT INTO telefono_proveedor (telefono, proveedor) VALUES
('664-681-1020', 'DIS890412AB1'),
('664-681-1021', 'DIS890412AB1'),
('664-634-4510', 'PRO951023CD2'),
('664-622-7890', 'COM030715EF3'),
('55-5207-9400', 'IMP180905JK5'),
('55-5207-9401', 'IMP180905JK5');

-- ============================================================
-- 3. ABASTECIMIENTO_OBRA (4 EJEMPLARES POR OBRA) 
-- ============================================================
INSERT INTO abastecimiento_obra (proveedor, obra, fecha_adquisicion, cantidad) VALUES
('COM030715EF3', '978-968-12-1139-4', '2026-09-10', 4),
('COM030715EF3', '978-1-4562-2396-0', '2026-09-10', 4),
('COM030715EF3', '978-607-442-288-7', '2026-09-12', 4),
('IMP180905JK5', '978-84-7829-059-8', '2026-09-12', 4),
('DIS890412AB1', '978-84-9759-220-8', '2026-09-15', 4),
('DIS890412AB1', '978-84-376-0418-3', '2026-09-15', 4),
('DIS890412AB1', '978-968-411-058-8', '2026-09-18', 4),
('PRO951023CD2', '978-84-7888-719-4', '2026-09-20', 4),
('PRO951023CD2', '978-84-08-04364-5', '2026-09-20', 4),
('PRO951023CD2', '978-84-9989-094-4', '2026-09-25', 4),
('IMP180905JK5', '978-84-9992-622-3', '2026-09-25', 4),
('IMP180905JK5', '978-84-254-3202-6', '2026-10-01', 4),
('PRO951023CD2', '978-84-7844-815-9', '2026-10-03', 4),
('IMP180905JK5', '978-0-7148-9870-4', '2026-10-05', 4),
('COM030715EF3', '978-607-481-809-3', '2026-10-10', 4),
('DIS890412AB1', '978-84-376-3499-9', '2026-10-15', 4),
('DIS890412AB1', '978-607-31-4772-9', '2026-10-15', 4),
('DIS890412AB1', '978-607-31-0492-0', '2026-10-15', 4);

-- ============================================================
-- 4. EJEMPLARES (4 COPIAS POR OBRA)
--    La última obra queda en Loc #1 (Sin asignar) para probar Registro 2
-- ============================================================
INSERT INTO ejemplar (obra, ejemplar, localizacion) VALUES
('978-968-12-1139-4', 1, 2), ('978-968-12-1139-4', 2, 2), ('978-968-12-1139-4', 3, 2), ('978-968-12-1139-4', 4, 2),
('978-1-4562-2396-0', 1, 2), ('978-1-4562-2396-0', 2, 2), ('978-1-4562-2396-0', 3, 2), ('978-1-4562-2396-0', 4, 2),
('978-607-442-288-7', 1, 3), ('978-607-442-288-7', 2, 3), ('978-607-442-288-7', 3, 3), ('978-607-442-288-7', 4, 3),
('978-84-7829-059-8', 1, 3), ('978-84-7829-059-8', 2, 3), ('978-84-7829-059-8', 3, 3), ('978-84-7829-059-8', 4, 3),
('978-84-9759-220-8', 1, 4), ('978-84-9759-220-8', 2, 4), ('978-84-9759-220-8', 3, 4), ('978-84-9759-220-8', 4, 4),
('978-84-376-0418-3', 1, 4), ('978-84-376-0418-3', 2, 4), ('978-84-376-0418-3', 3, 4), ('978-84-376-0418-3', 4, 4),
('978-968-411-058-8', 1, 4), ('978-968-411-058-8', 2, 4), ('978-968-411-058-8', 3, 4), ('978-968-411-058-8', 4, 4),
('978-84-08-04364-5', 1, 4), ('978-84-08-04364-5', 2, 4), ('978-84-08-04364-5', 3, 4), ('978-84-08-04364-5', 4, 4),
('978-84-7888-719-4', 1, 5), ('978-84-7888-719-4', 2, 5), ('978-84-7888-719-4', 3, 5), ('978-84-7888-719-4', 4, 5),
('978-84-9989-094-4', 1, 5), ('978-84-9989-094-4', 2, 5), ('978-84-9989-094-4', 3, 5), ('978-84-9989-094-4', 4, 5),
('978-84-9992-622-3', 1, 2), ('978-84-9992-622-3', 2, 2), ('978-84-9992-622-3', 3, 2), ('978-84-9992-622-3', 4, 2),
('978-84-254-3202-6', 1, 6), ('978-84-254-3202-6', 2, 6), ('978-84-254-3202-6', 3, 6), ('978-84-254-3202-6', 4, 6),
('978-84-7844-815-9', 1, 6), ('978-84-7844-815-9', 2, 6), ('978-84-7844-815-9', 3, 6), ('978-84-7844-815-9', 4, 6),
('978-0-7148-9870-4', 1, 7), ('978-0-7148-9870-4', 2, 7), ('978-0-7148-9870-4', 3, 7), ('978-0-7148-9870-4', 4, 7),
('978-607-481-809-3', 1, 1), ('978-607-481-809-3', 2, 1), ('978-607-481-809-3', 3, 1), ('978-607-481-809-3', 4, 1),
('978-84-376-3499-9', 1, 4), ('978-84-376-3499-9', 2, 4), ('978-84-376-3499-9', 3, 4), ('978-84-376-3499-9', 4, 4),
('978-607-31-4772-9', 1, 4), ('978-607-31-4772-9', 2, 4), ('978-607-31-4772-9', 3, 4), ('978-607-31-4772-9', 4, 4),
('978-607-31-0492-0', 1, 4), ('978-607-31-0492-0', 2, 4), ('978-607-31-0492-0', 3, 4), ('978-607-31-0492-0', 4, 4);

-- ============================================================
-- 5. EMPLEADOS FICTICIOS
-- ============================================================
INSERT INTO empleado (id_empleado, nombre_pila, primer_ap, segundo_ap, nombre_user, `contraseña`) VALUES
(2, 'Isela Miranda',  'Hernandez',  'Angel', 'miranda',  'miranda123'),
(3, 'Humberto Carlos', 'Lopez',  'Camacho', 'humberto',  'humberto123'),
(4, 'Diego Aaron',  'Suarez', 'Garcia', 'diego', 'diego123'),
(5,'Angel Javier', 'Vazquez', 'Jimenez', 'angel','angel123')

USE prestamos_bibliotecarios;

UPDATE prestamo SET empleado = 5 WHERE empleado = 1;
UPDATE devolucion SET empleado = 5 WHERE empleado = 1;

USE prestamos_bibliotecarios;

-- Cambia "Administrador Sistema" (1) por Angel Javier (5) en TODOS los prestamos y devoluciones
UPDATE prestamo SET empleado = 5 WHERE empleado = 1;
UPDATE devolucion SET empleado = 5 WHERE empleado = 1;


-- ============================================================
-- 6. USUARIOS Y TELÉFONOS FICTICIOS
-- ============================================================
INSERT INTO usuario (id_usuario, nombre_pila, primer_ap, segundo_ap, dir_calle, dir_numero, dir_colonia) VALUES
(1,  'Alejandro', 'Ramírez',   'Soto',      'Av. Revolución',         '412',  'Zona Centro'),
(2,  'Valeria',   'Castillo',  'Morales',   'Blvd. Agua Caliente',    '1050', 'Aviación'),
(3,  'Mateo',     'Herrera',   'Delgado',   'Calle Segunda',          '218',  'Zona Centro'),
(4,  'Fernanda',  'López',     'Gutiérrez', 'Paseo de los Héroes',    '890',  'Zona Río'),
(5,  'Diego',     'Sánchez',   NULL,        'Av. Universidad',        '305',  'Otay Universidad'),
(6,  'Camila',    'Vargas',    'Paredes',   'Calle Benito Juárez',    '144',  'Libertad'),
(7,  'Sebastián', 'Ortiz',     'Mendoza',   'Blvd. Díaz Ordaz',       '2210', 'La Mesa'),
(8,  'Mariana',   'Flores',    'Aguilar',   'Calle Ignacio Zaragoza', '78',   'Playas de Tijuana'),
(9,  'Andrés',    'Gómez',     'Reyes',     'Av. Tecnológico',        '515',  'Tomas Aquino'),
(10, 'Renata',    'Cruz',      NULL,        'Calle Miguel Hidalgo',   '620',  'Independencia'),
(11, 'Emiliano',  'Chávez',    'Salazar',   'Blvd. Insurgentes',      '3400', 'Río Tijuana 3ra Etapa'),
(12, 'Ximena',    'Domínguez', 'Peña',      'Calle Emiliano Zapata',  '95',   'Cacho');

INSERT INTO telefono_usuario (num_tel, usuario) VALUES
('664-110-2001', 1),
('664-110-2002', 1),
('664-220-3001', 2),
('664-220-3002', 2),
('664-330-4001', 3),
('664-440-5001', 4),
('664-440-5002', 4),
('664-550-6001', 5),
('664-660-7001', 6),
('664-770-8001', 7),
('664-880-9001', 8),
('664-990-1001', 9),
('664-990-1002', 9),
('664-121-1101', 10),
('664-131-1201', 11),
('664-141-1301', 12);

-- ============================================================
-- 7. PRÉSTAMOS FICTICIOS (+14 DÍAS EXACTOS DE PLAZO)
--    - Folios 1..3: anteriores (con 3 entregas tardías -> 3 multas)
--    - Folios 4..15: 12 préstamos en la misma fecha (2026-11-10)
--    - Folio 16: préstamo activo reciente con 3 ejemplares
-- ============================================================
INSERT INTO prestamo (folio, fecha_salida, fecha_limite, empleado, usuario) VALUES
(1,  '2026-10-20', '2026-11-03', 2, 1),
(2,  '2026-10-25', '2026-11-08', 3, 2),
(3,  '2026-10-28', '2026-11-11', 4, 3),
(4,  '2026-11-10', '2026-11-24', 1, 4),
(5,  '2026-11-10', '2026-11-24', 2, 5),
(6,  '2026-11-10', '2026-11-24', 2, 6),
(7,  '2026-11-10', '2026-11-24', 3, 7),
(8,  '2026-11-10', '2026-11-24', 3, 8),
(9,  '2026-11-10', '2026-11-24', 4, 9),
(10, '2026-11-10', '2026-11-24', 1, 10),
(11, '2026-11-10', '2026-11-24', 2, 11),
(12, '2026-11-10', '2026-11-24', 3, 12),
(13, '2026-11-10', '2026-11-24', 4, 1),
(14, '2026-11-10', '2026-11-24', 1, 2),
(15, '2026-11-10', '2026-11-24', 2, 3),
(16, '2026-11-20', '2026-12-04', 1, 5);


USE prestamos_bibliotecarios;

-- 1. Prestamo (salida 01-11-2026, limite 15-11-2026, empleado #4 Diego)
INSERT INTO prestamo (fecha_salida, fecha_limite, empleado, usuario)
VALUES ('2026-11-01', '2026-11-15', 4, 6);

SET @folio_demo = LAST_INSERT_ID();

-- 2. Ejemplar prestado (Fisica universitaria Vol. 1, ejemplar #3)
INSERT INTO prestamo_ejemplar (obra, ejemplar, prestamo)
VALUES ('978-607-442-288-7', 3, @folio_demo);

-- 3. Devolucion tardia (19-11-2026 = 4 dias tarde, recibida por empleado #3 Humberto)
--    NO se inserta en la tabla multa a proposito para generarla desde Python
INSERT INTO devolucion (fecha_devolucion, empleado, obra, ejemplar, prestamo)
VALUES ('2026-11-19', 3, '978-607-442-288-7', 3, @folio_demo);
--Borrar la multa de demostracion de que se genera de manera automatica--
DELETE FROM multa
WHERE devolucion = (
    SELECT id_devolucion FROM devolucion
    WHERE fecha_devolucion = '2026-11-19'
      AND obra = '978-607-442-288-7'
      AND ejemplar = 3
);


USE prestamos_bibliotecarios;

-- 1. Borra cualquier multa de los folios 17 y 18 (usa IN en lugar de =)
DELETE FROM multa
WHERE devolucion IN (
    SELECT id_devolucion FROM devolucion WHERE prestamo IN (17, 18)
);

-- 2. Borra el folio 18 duplicado respetando el orden de llaves foraneas
DELETE FROM devolucion WHERE prestamo = 18;
DELETE FROM prestamo_ejemplar WHERE prestamo = 18;
DELETE FROM prestamo WHERE folio = 18;

-- 3. Deja el consecutivo listo para que la multa generada vuelva a ser la #4
ALTER TABLE multa AUTO_INCREMENT = 4;
-- ============================================================
-- 8. PRÉSTAMO_EJEMPLAR (ENLAZADO A LAS 15 OBRAS REALES EN ESPAÑOL)
-- ============================================================
INSERT INTO prestamo_ejemplar (obra, ejemplar, prestamo) VALUES
-- Folio 1 (4 ejemplares)
('978-968-12-1139-4', 1, 1),
('978-84-7829-059-8', 1, 1),
('978-1-4562-2396-0', 1, 1),
('978-607-442-288-7', 1, 1),
-- Folio 2 (2 ejemplares)
('978-84-9992-622-3', 1, 2),
('978-84-9759-220-8', 1, 2),
-- Folio 3 (1 ejemplar)
('978-84-7844-815-9', 1, 3),
-- Folio 4 (3 ejemplares, del 10-11-2026)
('978-84-376-0418-3', 1, 4),
('978-968-411-058-8', 1, 4),
('978-84-7888-719-4', 1, 4),
-- Folios 5 al 15 (1 ejemplar c/u, todos del 10-11-2026)
('978-84-08-04364-5', 1, 5),
('978-84-9989-094-4', 1, 6),
('978-84-254-3202-6', 1, 7),
('978-0-7148-9870-4', 1, 8),
('978-607-481-809-3', 1, 9),
('978-968-12-1139-4', 2, 10),
('978-1-4562-2396-0', 2, 11),
('978-607-442-288-7', 2, 12),
('978-84-7829-059-8', 2, 13),
('978-84-9759-220-8', 2, 14),
('978-84-9992-622-3', 2, 15),
-- Folio 16 (3 ejemplares activos recientes)
('978-84-376-0418-3', 2, 16),
('978-968-411-058-8', 2, 16),
('978-84-7888-719-4', 2, 16);

-- ============================================================
-- 9. DEVOLUCIONES FICTICIAS
--    - Devoluciones 2, 5 y 7: con retraso (3, 5 y 7 días, las 3 en libros con subtítulo real)
--    - Devoluciones 8..19: 12 devoluciones A TIEMPO el 2026-11-23
-- ============================================================
INSERT INTO devolucion (id_devolucion, fecha_devolucion, empleado, obra, ejemplar, prestamo) VALUES
-- Folio 1 (límite 2026-11-03)
(1,  '2026-11-01', 2, '978-968-12-1139-4', 1, 1),
(2,  '2026-11-06', 3, '978-84-7829-059-8', 1, 1), -- 3 días de retraso
(3,  '2026-11-02', 1, '978-1-4562-2396-0', 1, 1),
(4,  '2026-11-03', 4, '978-607-442-288-7', 1, 1),
-- Folio 2 (límite 2026-11-08)
(5,  '2026-11-13', 2, '978-84-9992-622-3', 1, 2), -- 5 días de retraso
(6,  '2026-11-07', 3, '978-84-9759-220-8', 1, 2),
-- Folio 3 (límite 2026-11-11)
(7,  '2026-11-18', 1, '978-84-7844-815-9', 1, 3), -- 7 días de retraso
-- 12 devoluciones A TIEMPO el 2026-11-23 (límite 2026-11-24)
(8,  '2026-11-23', 2, '978-84-376-0418-3', 1, 4),
(9,  '2026-11-23', 2, '978-968-411-058-8', 1, 4),
(10, '2026-11-23', 3, '978-84-08-04364-5', 1, 5),
(11, '2026-11-23', 3, '978-84-9989-094-4', 1, 6),
(12, '2026-11-23', 4, '978-84-254-3202-6', 1, 7),
(13, '2026-11-23', 4, '978-0-7148-9870-4', 1, 8),
(14, '2026-11-23', 1, '978-607-481-809-3', 1, 9),
(15, '2026-11-23', 1, '978-968-12-1139-4', 2, 10),
(16, '2026-11-23', 2, '978-1-4562-2396-0', 2, 11),
(17, '2026-11-23', 3, '978-607-442-288-7', 2, 12),
(18, '2026-11-23', 4, '978-84-7829-059-8', 2, 13),
(19, '2026-11-23', 1, '978-84-9759-220-8', 2, 14);

-- ============================================================
-- 10. MULTAS FICTICIAS ($15.00 / DÍA DE RETRASO)
-- ============================================================
INSERT INTO multa (multa, devolucion, estado, monto_dia, dias_retraso, total) VALUES
(1, 2, 'Pagada',    15.00, 3,  45.00),
(2, 5, 'Pendiente', 15.00, 5,  75.00),
(3, 7, 'Pendiente', 15.00, 7, 105.00);
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
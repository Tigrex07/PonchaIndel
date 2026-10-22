

INSERT INTO "main"."" ("sql") VALUES ('CREATE TABLE maestros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL,
        tipo TEXT CHECK(tipo IN (''NORMAL'', ''PA'')) NOT NULL,
        activo INTEGER DEFAULT 1
    )');
INSERT INTO "main"."" ("sql") VALUES ('CREATE TABLE sqlite_sequence(name,seq)');
INSERT INTO "main"."" ("sql") VALUES ('CREATE TABLE periodo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        fechaInicio TEXT NOT NULL,
        fechaFinal TEXT NOT NULL
    )');
INSERT INTO "main"."" ("sql") VALUES ('CREATE TABLE turno (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL,
        horaEntrada TEXT NOT NULL,  -- Formato ''HH:MM''
        horaSalida TEXT NOT NULL,   -- Formato ''HH:MM''
        diassemana TEXT NOT NULL DEFAULT ''1,2,3,4,5'' -- ''1,2,3,4,5'' = Lunes a Viernes
    )');
INSERT INTO "main"."" ("sql") VALUES ('CREATE TABLE horarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        idmaestro INTEGER NOT NULL,
        idperiodo INTEGER NOT NULL,
        idturno INTEGER NOT NULL,
        FOREIGN KEY (idmaestro) REFERENCES maestros(id) ON DELETE CASCADE,
        FOREIGN KEY (idperiodo) REFERENCES periodo(id) ON DELETE CASCADE,
        FOREIGN KEY (idturno) REFERENCES turno(id) ON DELETE RESTRICT,
        CONSTRAINT uq_maestro_periodo UNIQUE (idmaestro, idperiodo)
    )');
INSERT INTO "main"."" ("sql") VALUES ('CREATE TABLE ponchadas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        idMaestro INTEGER NOT NULL,
        fecha TEXT NOT NULL,  -- Formato ''YYYY-MM-DD''
        hora TEXT NOT NULL,   -- Formato ''HH:MM:SS''
        tipo TEXT CHECK(tipo IN (''ENTRADA'', ''SALIDA'', ''DESCONOCIDO'')) DEFAULT ''DESCONOCIDO'',
        FOREIGN KEY (idMaestro) REFERENCES maestros(id) ON DELETE CASCADE
    )');
INSERT INTO "main"."" ("sql") VALUES ('CREATE TABLE usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        correo TEXT UNIQUE NOT NULL,
        clave TEXT NOT NULL, -- Guardará el hash encriptado de la contraseña
        rol TEXT CHECK(rol IN (''ADMIN'', ''OPERADOR'')) NOT NULL DEFAULT ''OPERADOR'',
        activo INTEGER DEFAULT 1
    )');


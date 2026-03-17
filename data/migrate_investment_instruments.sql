-- Migración: separar investment_instruments de investments
-- Ejecutar con: psql $DATABASE_URL -f data/migrate_investment_instruments.sql
--
-- Qué hace:
--   1. Crea la tabla investment_instruments
--   2. La puebla con los símbolos únicos que ya existen en investments
--   3. Añade la FK en investments.asset_symbol
--   4. Elimina la columna asset_name de investments

BEGIN;

-- 1. Crear la tabla maestra de instrumentos
CREATE TABLE investment_instruments (
    symbol      VARCHAR(20)  PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    asset_type  VARCHAR(50)  NOT NULL DEFAULT 'stock'
);

-- 2. Poblar desde los datos existentes (un registro por símbolo único)
--    asset_type queda como 'stock' por defecto; actualiza manualmente los ETFs/cripto después
INSERT INTO investment_instruments (symbol, name)
SELECT DISTINCT ON (asset_symbol) asset_symbol, asset_name
FROM investments
ORDER BY asset_symbol, id;

-- 3. Añadir la FK (los datos ya son consistentes, así que no fallará)
ALTER TABLE investments
    ADD CONSTRAINT fk_investments_instrument
    FOREIGN KEY (asset_symbol) REFERENCES investment_instruments(symbol);

-- 4. Eliminar la columna redundante
ALTER TABLE investments DROP COLUMN asset_name;

COMMIT;

-- ---------------------------------------------------------------------------
-- Opcional: corregir asset_type de los instrumentos que no son acciones
-- Ejecuta esto después de revisar qué símbolos tienes:
--
-- UPDATE investment_instruments SET asset_type = 'etf'   WHERE symbol = 'CSSPX.MI';
-- UPDATE investment_instruments SET asset_type = 'stock' WHERE symbol = 'CANG';
-- UPDATE investment_instruments SET asset_type = 'stock' WHERE symbol = 'NFC.DU';
-- ---------------------------------------------------------------------------

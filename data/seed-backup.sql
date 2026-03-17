--
-- Seed generado a partir de backup.sql adaptado a la nueva estructura
-- (investment_instruments separado de investments)
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

-- ---------------------------------------------------------------------------
-- accounts
-- ---------------------------------------------------------------------------

INSERT INTO public.accounts (id, name, initial_balance) VALUES
    (1, 'Trade Republic', 1626.56),
    (2, 'Imagin', 208.28);

-- ---------------------------------------------------------------------------
-- investment_instruments  (tabla nueva — maestro de instrumentos)
-- ---------------------------------------------------------------------------

INSERT INTO public.investment_instruments (symbol, name, asset_type) VALUES
    ('CSSPX.MI', 'SP 500',  'etf'),
    ('CANG',     'Cango',   'stock'),
    ('NFC.DU',   'Netflix', 'stock');

-- ---------------------------------------------------------------------------
-- investments  (sin columna asset_name — viene del instrumento)
-- ---------------------------------------------------------------------------

INSERT INTO public.investments (id, asset_symbol, quantity, purchase_price, purchase_date, source_account_id, is_initial, notes) VALUES
    (1,  'CSSPX.MI', 0.96454200, 621.02, '2026-03-10', 1, true, NULL),
    (2,  'CSSPX.MI', 0.88670100, 562.76, '2025-03-10', 1, true, NULL),
    (3,  'CSSPX.MI', 1.24296600, 561.56, '2025-03-28', 1, true, NULL),
    (4,  'CSSPX.MI', 1.16130500, 516.66, '2025-04-28', 1, true, NULL),
    (5,  'CSSPX.MI', 1.07428500, 557.56, '2025-05-28', 1, true, NULL),
    (6,  'CSSPX.MI', 1.77322500, 563.38, '2025-06-30', 1, true, NULL),
    (7,  'CSSPX.MI', 1.02141700, 586.44, '2025-07-28', 1, true, NULL),
    (8,  'CSSPX.MI', 0.00195900, 587.03, '2025-08-11', 1, true, NULL),
    (9,  'CSSPX.MI', 1.01237100, 591.68, '2025-08-26', 1, true, NULL),
    (10, 'CSSPX.MI', 0.00142000, 591.55, '2025-09-09', 1, true, NULL),
    (11, 'CSSPX.MI', 0.00668900, 598.00, '2025-09-16', 1, true, NULL),
    (12, 'CSSPX.MI', 0.00403500, 607.19, '2025-09-23', 1, true, NULL),
    (13, 'CSSPX.MI', 0.98965700, 605.26, '2025-09-26', 1, true, NULL),
    (14, 'CSSPX.MI', 0.00008100, 617.28, '2025-10-02', 1, true, NULL),
    (15, 'CSSPX.MI', 0.00053000, 622.64, '2025-10-09', 1, true, NULL),
    (16, 'CANG',     400.00000000, 1.62, '2026-03-13', 1, true, NULL),
    (17, 'CSSPX.MI', 0.00285200, 613.60, '2025-10-16', 1, true, NULL),
    (18, 'CSSPX.MI', 0.01026000, 619.88, '2025-10-23', 1, true, NULL),
    (19, 'CSSPX.MI', 0.94709500, 632.46, '2025-10-28', 1, true, NULL),
    (20, 'CSSPX.MI', 0.01238700, 635.34, '2025-11-03', 1, true, NULL),
    (21, 'CSSPX.MI', 0.00575000, 629.57, '2025-11-10', 1, true, NULL),
    (22, 'CSSPX.MI', 0.00816300, 623.55, '2025-11-17', 1, true, NULL),
    (23, 'CSSPX.MI', 0.00511100, 616.32, '2025-11-24', 1, true, NULL),
    (24, 'CSSPX.MI', 0.95170000, 629.40, '2025-11-26', 1, true, NULL),
    (25, 'CSSPX.MI', 0.00600800, 630.83, '2025-12-02', 1, true, NULL),
    (26, 'CSSPX.MI', 0.00285300, 630.91, '2025-12-09', 1, true, NULL),
    (27, 'CSSPX.MI', 0.00797500, 618.18, '2025-12-16', 1, true, NULL),
    (28, 'CSSPX.MI', 0.95846100, 624.96, '2025-12-23', 1, true, NULL),
    (29, 'CSSPX.MI', 0.00330900, 625.57, '2025-12-23', 1, true, NULL),
    (30, 'CSSPX.MI', 0.00455900, 629.52, '2026-01-02', 1, true, NULL),
    (31, 'CSSPX.MI', 0.00373900, 639.21, '2026-01-09', 1, true, NULL),
    (32, 'CSSPX.MI', 0.01145900, 641.42, '2026-01-16', 1, true, NULL),
    (33, 'CSSPX.MI', 0.00633700, 629.64, '2026-01-23', 1, true, NULL),
    (34, 'CSSPX.MI', 0.95385200, 627.98, '2026-01-26', 1, true, NULL),
    (35, 'CSSPX.MI', 0.00393000, 631.04, '2026-02-02', 1, true, NULL),
    (38, 'NFC.DU',   0.38545500,  80.42, '2026-03-13', 1, true, NULL);

-- ---------------------------------------------------------------------------
-- Secuencias
-- ---------------------------------------------------------------------------

SELECT pg_catalog.setval('public.accounts_id_seq',     2,  true);
SELECT pg_catalog.setval('public.assets_id_seq',       1,  false);
SELECT pg_catalog.setval('public.investments_id_seq',  38, true);
SELECT pg_catalog.setval('public.transactions_id_seq', 1,  false);

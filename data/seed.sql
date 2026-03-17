TRUNCATE TABLE investments RESTART IDENTITY CASCADE;
TRUNCATE TABLE assets RESTART IDENTITY CASCADE;
TRUNCATE TABLE transactions RESTART IDENTITY CASCADE;
TRUNCATE TABLE accounts RESTART IDENTITY CASCADE;

INSERT INTO accounts (name, initial_balance) VALUES
('BBVA',       2500.00),
('Santander',  8000.00),
('Efectivo',    300.00);

INSERT INTO transactions (description, amount, category, date, is_income, notes, account_id) VALUES
-- Enero — BBVA (id=1)
('Salario enero',          28000.00, 'ingreso',        '2026-01-01', true,  NULL,                       1),
('Alquiler enero',          8500.00, 'servicios',      '2026-01-02', false, 'Piso centro',              1),
('Mercadona',                320.50, 'comida',         '2026-01-05', false, NULL,                       1),
('Netflix',                   17.99, 'entretenimiento','2026-01-06', false, NULL,                       1),
('Metro mensual',             54.60, 'transporte',     '2026-01-07', false, 'Abono transportes',        1),
('Farmacia',                  42.30, 'salud',          '2026-01-10', false, 'Vitaminas y paracetamol',  2),
('Comida con amigos',        118.00, 'comida',         '2026-01-11', false, 'Restaurante La Mar',       3),
('Amazon compras',           230.00, 'compras',        '2026-01-15', false, 'Auriculares + funda',      1),
('Gimnasio',                  45.00, 'salud',          '2026-01-15', false, NULL,                       2),
('Freelance web',           3500.00, 'ingreso',        '2026-01-20', true,  'Proyecto tienda online',   2),
('Gasolina',                  65.00, 'transporte',     '2026-01-22', false, NULL,                       3),
('Supermercado Dia',         210.80, 'comida',         '2026-01-28', false, NULL,                       1),
('Spotify',                   10.99, 'entretenimiento','2026-01-28', false, NULL,                       1),

-- Febrero
('Salario febrero',        28000.00, 'ingreso',        '2026-02-01', true,  NULL,                       1),
('Alquiler febrero',        8500.00, 'servicios',      '2026-02-02', false, 'Piso centro',              1),
('Factura luz',              134.20, 'servicios',      '2026-02-03', false, NULL,                       2),
('Factura internet',          45.00, 'servicios',      '2026-02-03', false, NULL,                       2),
('Mercadona',                295.40, 'comida',         '2026-02-06', false, NULL,                       1),
('Cine + palomitas',          32.00, 'entretenimiento','2026-02-08', false, 'Película estreno',         3),
('Médico privado',            80.00, 'salud',          '2026-02-10', false, 'Revisión anual',           2),
('Ropa invierno',            189.99, 'compras',        '2026-02-14', false, 'Abrigo y botas',           1),
('Taxi aeropuerto',           35.00, 'transporte',     '2026-02-16', false, NULL,                       3),
('Freelance diseño',        1800.00, 'ingreso',        '2026-02-18', true,  'Logo empresa',             2),
('Supermercado Carrefour',   178.60, 'comida',         '2026-02-22', false, NULL,                       1),
('Curso online',              89.00, 'educacion',      '2026-02-25', false, 'Udemy Python avanzado',    1),
('Gimnasio',                  45.00, 'salud',          '2026-02-28', false, NULL,                       2),

-- Marzo
('Salario marzo',          28000.00, 'ingreso',        '2026-03-01', true,  NULL,                       1),
('Alquiler marzo',          8500.00, 'servicios',      '2026-03-02', false, 'Piso centro',              1),
('Mercadona',                310.20, 'comida',         '2026-03-03', false, NULL,                       1),
('Metro mensual',             54.60, 'transporte',     '2026-03-04', false, 'Abono transportes',        1),
('Netflix',                   17.99, 'entretenimiento','2026-03-06', false, NULL,                       1),
('Spotify',                   10.99, 'entretenimiento','2026-03-06', false, NULL,                       1),
('Cena cumpleaños',          145.00, 'comida',         '2026-03-08', false, 'Restaurante japonés',      3),
('Librería',                  52.40, 'educacion',      '2026-03-10', false, 'Libros programación',      1),
('Gasolina',                  71.00, 'transporte',     '2026-03-11', false, NULL,                       3),
('Gimnasio',                  45.00, 'salud',          '2026-03-11', false, NULL,                       2);

-- Activos iniciales (is_initial=true): patrimonio de arranque, no cuentan como gasto
-- Activos adquiridos (is_initial=false): compras nuevas, sí cuentan como gasto
INSERT INTO assets (name, value, category, acquisition_date, is_initial, account_id, notes) VALUES
('Honda Civic 2019',      12000.00, 'vehiculo',    '2019-06-15', true,  1, 'Activo previo a la app'),
('MacBook Pro 16"',        2800.00, 'electronico', '2023-09-01', true,  1, 'Activo previo a la app'),
('Cámara Sony A7 IV',      2500.00, 'electronico', '2026-01-25', false, 1, 'Comprada en enero — cuenta como gasto'),
('Bicicleta Trek FX3',      850.00, 'otro',        '2026-02-20', false, 2, 'Comprada en febrero — cuenta como gasto');

INSERT INTO investments (asset_symbol, asset_name, quantity, purchase_price, purchase_date, source_account_id, is_initial, notes) VALUES
-- Cartera inicial (is_initial=true): no descuenta del balance, patrimonio de arranque
('MSFT',    'Microsoft Corp.',   3,    380.00, '2025-06-01', 1, true,  'Cartera previa a la app'),
('SPY',     'S&P 500 ETF',       10,   480.00, '2025-09-15', 2, true,  'ETF largo plazo previo a la app'),
-- AAPL: 3 compras nuevas (is_initial=false) → desuentan del balance, probar agrupación by-symbol
('AAPL',    'Apple Inc.',        5,    150.00, '2026-01-10', 1, false, 'Primera compra'),
('AAPL',    'Apple Inc.',        8,    162.00, '2026-02-05', 1, false, 'Segunda compra, precio subió'),
('AAPL',    'Apple Inc.',        3,    155.50, '2026-03-01', 1, false, 'Tercera compra, DCA'),
-- BTC-USD: 2 compras nuevas → DCA crypto
('BTC-USD', 'Bitcoin',           0.05, 95000.00,'2026-01-15', 2, false, 'DCA enero'),
('BTC-USD', 'Bitcoin',           0.03, 88000.00,'2026-02-20', 2, false, 'DCA febrero, precio bajó'),
-- ETH nueva compra
('ETH-USD', 'Ethereum',          0.5,  3200.00,'2026-03-05', 1, false, NULL);

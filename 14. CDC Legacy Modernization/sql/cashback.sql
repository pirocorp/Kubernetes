-- Modern service owns this DB. Legacy application has NO access to it.
CREATE TABLE IF NOT EXISTS customer_projection (
    customer_id BIGINT PRIMARY KEY,
    full_name TEXT NOT NULL,
    tier TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sale_stage (
    sale_id BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL,
    expected_lines INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS item_stage (
    line_item_id BIGINT PRIMARY KEY,
    sale_id BIGINT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price_cents BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_stage_sale ON item_stage(sale_id);
CREATE TABLE IF NOT EXISTS expenses (
    sale_id BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL,
    total_cents BIGINT NOT NULL,
    cashback_cents BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_expenses_customer ON expenses(customer_id);
CREATE TABLE IF NOT EXISTS wallets (
    customer_id BIGINT PRIMARY KEY,
    balance_cents BIGINT NOT NULL DEFAULT 0
);

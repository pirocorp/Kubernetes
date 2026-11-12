-- The simulated unmodifiable legacy application owns these four tables.
-- In a real legacy system, do NOT modify its schema without change approval.
CREATE TABLE IF NOT EXISTS customer (
    customer_id BIGINT PRIMARY KEY,
    full_name TEXT NOT NULL,
    tier TEXT NOT NULL CHECK (tier IN ('bronze','silver','gold'))
);
CREATE TABLE IF NOT EXISTS product (
    product_id BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    price_cents BIGINT NOT NULL CHECK (price_cents >= 0)
);
CREATE TABLE IF NOT EXISTS sale (
    sale_id BIGSERIAL PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customer(customer_id),
    expected_lines INTEGER NOT NULL CHECK (expected_lines > 0)
);
CREATE TABLE IF NOT EXISTS line_item (
    line_item_id BIGSERIAL PRIMARY KEY,
    sale_id BIGINT NOT NULL REFERENCES sale(sale_id),
    product_id BIGINT NOT NULL REFERENCES product(product_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price_cents BIGINT NOT NULL CHECK (unit_price_cents >= 0)
);
-- Snapshot will include these existing legacy rows.
INSERT INTO customer VALUES
    (1,'Alex Rivera','bronze'),(2,'Taylor Smith','gold')
    ON CONFLICT (customer_id) DO NOTHING;
INSERT INTO product VALUES
    (101,'Red Fern','A beautiful red-leaf houseplant',1500),
    (102,'Blue Pot','A ceramic blue flower pot',2000)
    ON CONFLICT (product_id) DO NOTHING;

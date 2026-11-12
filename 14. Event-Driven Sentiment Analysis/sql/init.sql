-- PostgreSQL persistence for APPROVED reviews only.
-- Idempotent retry: review_id is the stable event key.
CREATE TABLE IF NOT EXISTS approved_reviews (
    review_id UUID PRIMARY KEY,
    product_id VARCHAR(40) NOT NULL,
    category VARCHAR(64) NOT NULL,
    review_text VARCHAR(500) NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_review_category_time
    ON approved_reviews(category, submitted_at DESC);

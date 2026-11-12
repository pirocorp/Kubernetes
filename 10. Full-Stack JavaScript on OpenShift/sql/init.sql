-- Owned by the Shorties database. Container initialization runs only on an empty volume.
CREATE TABLE IF NOT EXISTS short_links (
    code VARCHAR(12) PRIMARY KEY,
    target_url TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_short_links_created_at ON short_links(created_at DESC);

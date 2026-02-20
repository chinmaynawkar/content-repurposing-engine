--  schema: users, content, generated_posts
-- Run this in Supabase SQL Editor (Dashboard → SQL Editor → New Query).

-- Create users table (for future multi-user support)
CREATE TABLE IF NOT EXISTS users (
    -- id: unique identifier for each row
    -- SERIAL: auto-incrementing integer (PostgreSQL shortcut for an integer primary key)
    -- PRIMARY KEY: sets this column as the unique row identifier
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100),
    created_at TIMESTAMP
    WITH
        TIME ZONE DEFAULT NOW()
);

-- Create content table
CREATE TABLE IF NOT EXISTS content (
    id SERIAL PRIMARY KEY,
    -- user_id: Stores the ID of the related user from 'users' table.
    -- REFERENCES users(id): Foreign key constraint, links to 'users' table's 'id' column.
    -- ON DELETE SET NULL: If referenced user is deleted, this value becomes NULL.
    user_id INTEGER REFERENCES users (id) ON DELETE SET NULL,
    original_text TEXT NOT NULL,
    title VARCHAR(255),
    word_count INTEGER,
    -- source_url: Web address where the content came from (if any).
    source_url VARCHAR(500),
    created_at TIMESTAMP
    WITH
        TIME ZONE DEFAULT NOW()
);

-- Create generated_posts table
CREATE TABLE IF NOT EXISTS generated_posts (
    id SERIAL PRIMARY KEY,
    -- content_id: Foreign key that links each generated post to a specific content record.
    -- REFERENCES content(id): Enforces referential integrity, ensuring this value matches an existing content row.
    -- ON DELETE CASCADE: If the related content is deleted, all associated generated_posts are automatically removed.
    content_id INTEGER REFERENCES content (id) ON DELETE CASCADE,
    -- platform: Stores the platform where the generated post will be published.
    -- CHECK: Ensures the value is one of the allowed platforms.
    platform VARCHAR(50) NOT NULL CHECK (
        platform IN (
            'linkedin',
            'twitter',
            'instagram',
            'seo',
            'thumbnail'
        )
    ),
    generated_text TEXT NOT NULL,
    post_metadata JSONB,
    is_favorite BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP
    WITH
        TIME ZONE DEFAULT NOW()
);

-- Indexes speed up query performance for common lookups and sorting:
-- This index makes finding all content for a specific user fast.
CREATE INDEX IF NOT EXISTS idx_content_user ON content (user_id);

-- This index makes sorting or searching content by creation date faster (newest first).
CREATE INDEX IF NOT EXISTS idx_content_created ON content (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_posts_content ON generated_posts (content_id);

CREATE INDEX IF NOT EXISTS idx_posts_platform ON generated_posts (platform);

-- These commands turn on Row Level Security (RLS) for the tables.
-- RLS lets you control who can see or edit each row in the table.
ALTER TABLE content ENABLE ROW LEVEL SECURITY;

ALTER TABLE generated_posts ENABLE ROW LEVEL SECURITY;

-- POLICY: Rules that control what users can do in a table. Each policy has a purpose (SELECT, INSERT) and a condition (USING or CHECK).
-- "USING (true)" means this policy allows everyone to read (SELECT) data.
CREATE POLICY "Allow read content" ON content FOR
SELECT USING (true);

-- Allows anyone to insert (add) rows into the 'content' table.
-- "CHECK (true)" means any inserted row is accepted, no restrictions.
CREATE POLICY "Allow insert content" ON content FOR
INSERT
WITH
    CHECK (true);

-- Allows everyone to read (SELECT) from 'generated_posts'.
CREATE POLICY "Allow read generated_posts" ON generated_posts FOR
SELECT USING (true);

-- Allows anyone to add (INSERT) rows to 'generated_posts'.
CREATE POLICY "Allow insert generated_posts" ON generated_posts FOR
INSERT
WITH
    CHECK (true);
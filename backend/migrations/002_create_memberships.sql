-- Phase 1 defined memberships with only an id column. Apply once to that table.
ALTER TABLE memberships
    ADD COLUMN user_id INT NOT NULL,
    ADD COLUMN plan_name VARCHAR(80) NOT NULL,
    ADD COLUMN plan_type ENUM('basic', 'pro', 'elite') NOT NULL,
    ADD COLUMN price DECIMAL(10, 2) NOT NULL,
    ADD COLUMN start_date DATE NOT NULL,
    ADD COLUMN end_date DATE NOT NULL,
    ADD COLUMN status ENUM('active', 'expired', 'cancelled') NOT NULL DEFAULT 'active',
    ADD COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ADD INDEX ix_memberships_user_id (user_id),
    ADD INDEX ix_memberships_plan_type (plan_type),
    ADD INDEX ix_memberships_start_date (start_date),
    ADD INDEX ix_memberships_end_date (end_date),
    ADD INDEX ix_memberships_status (status),
    ADD CONSTRAINT ck_memberships_price_nonnegative CHECK (price >= 0),
    ADD CONSTRAINT ck_memberships_date_range CHECK (end_date >= start_date),
    ADD CONSTRAINT fk_memberships_user_id
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE;

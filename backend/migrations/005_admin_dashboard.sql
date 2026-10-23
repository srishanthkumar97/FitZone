-- Existing payment/notification placeholder rows must be assigned valid owner
-- and content values before applying their NOT NULL column additions below.
ALTER TABLE users
    ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE,
    ADD INDEX ix_users_is_active (is_active);

ALTER TABLE memberships
    MODIFY COLUMN plan_type VARCHAR(40) NOT NULL;

CREATE TABLE membership_plans (
    id INT NOT NULL AUTO_INCREMENT,
    plan_type VARCHAR(40) NOT NULL,
    name VARCHAR(80) NOT NULL,
    monthly_price DECIMAL(10, 2) NOT NULL,
    durations_months JSON NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT uq_membership_plans_plan_type UNIQUE (plan_type),
    CONSTRAINT ck_membership_plans_price_nonnegative CHECK (monthly_price >= 0),
    INDEX ix_membership_plans_is_active (is_active)
);

INSERT INTO membership_plans (plan_type, name, monthly_price, durations_months) VALUES
    ('basic', 'BASIC', 1200.00, JSON_ARRAY(1, 3, 6)),
    ('pro', 'PRO', 1500.00, JSON_ARRAY(1, 3, 6)),
    ('elite', 'ELITE', 2500.00, JSON_ARRAY(1, 3, 6));

ALTER TABLE payments
    ADD COLUMN user_id INT NOT NULL,
    ADD COLUMN membership_id INT NULL,
    ADD COLUMN amount DECIMAL(10, 2) NOT NULL,
    ADD COLUMN status VARCHAR(16) NOT NULL DEFAULT 'pending',
    ADD COLUMN payment_method VARCHAR(40) NULL,
    ADD COLUMN paid_at DATETIME NULL,
    ADD COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ADD INDEX ix_payments_user_id (user_id),
    ADD INDEX ix_payments_membership_id (membership_id),
    ADD INDEX ix_payments_status (status),
    ADD INDEX ix_payments_paid_at (paid_at),
    ADD CONSTRAINT ck_payments_amount_nonnegative CHECK (amount >= 0),
    ADD CONSTRAINT ck_payments_status
        CHECK (status IN ('pending', 'completed', 'failed', 'refunded')),
    ADD CONSTRAINT fk_payments_user_id
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    ADD CONSTRAINT fk_payments_membership_id
        FOREIGN KEY (membership_id) REFERENCES memberships (id) ON DELETE SET NULL;

ALTER TABLE notifications
    ADD COLUMN title VARCHAR(160) NOT NULL,
    ADD COLUMN body TEXT NOT NULL,
    ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN created_by INT NULL,
    ADD COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ADD INDEX ix_notifications_is_active (is_active),
    ADD INDEX ix_notifications_created_by (created_by),
    ADD CONSTRAINT fk_notifications_created_by
        FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE SET NULL;

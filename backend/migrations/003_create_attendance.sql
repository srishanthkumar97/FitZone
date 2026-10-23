CREATE TABLE attendance (
    id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    attendance_date DATE NOT NULL,
    check_in_time DATETIME NOT NULL,
    check_out_time DATETIME NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'checked_in',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT uq_attendance_user_date UNIQUE (user_id, attendance_date),
    CONSTRAINT ck_attendance_status
        CHECK (status IN ('checked_in', 'checked_out')),
    INDEX ix_attendance_user_id (user_id),
    INDEX ix_attendance_attendance_date (attendance_date),
    CONSTRAINT fk_attendance_user_id
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

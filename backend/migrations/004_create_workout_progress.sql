-- Phase 1 created workouts and progress with only an id column.
ALTER TABLE workouts
    ADD COLUMN user_id INT NOT NULL,
    ADD COLUMN workout_date DATE NOT NULL,
    ADD COLUMN workout_type VARCHAR(80) NOT NULL,
    ADD COLUMN duration INT NOT NULL,
    ADD COLUMN notes TEXT NULL,
    ADD COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ADD INDEX ix_workouts_user_id (user_id),
    ADD INDEX ix_workouts_workout_date (workout_date),
    ADD CONSTRAINT ck_workouts_duration_positive CHECK (duration > 0),
    ADD CONSTRAINT fk_workouts_user_id
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE;

CREATE TABLE exercises (
    id INT NOT NULL AUTO_INCREMENT,
    workout_id INT NOT NULL,
    exercise_name VARCHAR(120) NOT NULL,
    sets INT NULL,
    reps INT NULL,
    weight DECIMAL(8, 2) NULL,
    PRIMARY KEY (id),
    CONSTRAINT ck_exercises_sets_positive CHECK (sets IS NULL OR sets > 0),
    CONSTRAINT ck_exercises_reps_positive CHECK (reps IS NULL OR reps > 0),
    CONSTRAINT ck_exercises_weight_nonnegative CHECK (weight IS NULL OR weight >= 0),
    INDEX ix_exercises_workout_id (workout_id),
    CONSTRAINT fk_exercises_workout_id
        FOREIGN KEY (workout_id) REFERENCES workouts (id) ON DELETE CASCADE
);

ALTER TABLE progress
    ADD COLUMN user_id INT NOT NULL,
    ADD COLUMN record_date DATE NOT NULL,
    ADD COLUMN weight DECIMAL(6, 2) NULL,
    ADD COLUMN height DECIMAL(6, 2) NULL,
    ADD COLUMN body_fat DECIMAL(5, 2) NULL,
    ADD COLUMN chest DECIMAL(6, 2) NULL,
    ADD COLUMN waist DECIMAL(6, 2) NULL,
    ADD COLUMN arms DECIMAL(6, 2) NULL,
    ADD COLUMN notes TEXT NULL,
    ADD COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ADD INDEX ix_progress_user_id (user_id),
    ADD INDEX ix_progress_record_date (record_date),
    ADD CONSTRAINT ck_progress_weight_positive CHECK (weight IS NULL OR weight > 0),
    ADD CONSTRAINT ck_progress_height_positive CHECK (height IS NULL OR height > 0),
    ADD CONSTRAINT ck_progress_body_fat_range
        CHECK (body_fat IS NULL OR (body_fat >= 0 AND body_fat <= 100)),
    ADD CONSTRAINT ck_progress_chest_positive CHECK (chest IS NULL OR chest > 0),
    ADD CONSTRAINT ck_progress_waist_positive CHECK (waist IS NULL OR waist > 0),
    ADD CONSTRAINT ck_progress_arms_positive CHECK (arms IS NULL OR arms > 0),
    ADD CONSTRAINT fk_progress_user_id
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE;

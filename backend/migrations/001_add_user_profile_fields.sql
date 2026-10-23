ALTER TABLE users
    ADD COLUMN fitness_goal VARCHAR(80) NULL,
    ADD COLUMN date_of_birth DATE NULL,
    ADD COLUMN gender VARCHAR(32) NULL,
    ADD COLUMN profile_photo VARCHAR(2048) NULL;

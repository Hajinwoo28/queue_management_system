ALTER TABLE students ADD COLUMN next_serving INT DEFAULT 0;

SELECT * FROM queue_management;

CREATE TABLE IF NOT EXISTS queue_management (
    office_name VARCHAR(100) PRIMARY KEY,
    currently_serving INT NOT NULL DEFAULT 0,
    next_serving INT NOT NULL DEFAULT 1
);
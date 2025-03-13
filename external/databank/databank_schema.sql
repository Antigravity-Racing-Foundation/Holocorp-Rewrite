PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(48) NOT NULL UNIQUE,
    text TEXT NOT NULL,
    is_deleted INTEGER DEFAULT 0,
    deleted_date TIMESTAMP 
);

CREATE TABLE IF NOT EXISTS edits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id INTEGER NOT NULL,
    editor INTEGER NOT NULL,
    date TIMESTAMP NOT NULL,
    diff TEXT NOT NULL,
    FOREIGN KEY (entry_id) REFERENCES entries (id)
);

CREATE TRIGGER deletion_timestamping
BEFORE UPDATE ON entries
FOR EACH ROW
BEGIN
    UPDATE entries
    SET deleted_date = CASE
        WHEN new.is_deleted = 1 THEN unixepoch()
        ELSE NULL
    END
    WHERE id = NEW.id;
END;
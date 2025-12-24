ALTER TABLE visits
ADD COLUMN IF NOT EXISTS created_by INT;

ALTER TABLE visits
ADD CONSTRAINT IF NOT EXISTS fk_visits_created_by
FOREIGN KEY (created_by) REFERENCES users(id);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(120),
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Демо-пользователи для проверки входа:
-- admin / admin123
-- user / user123
INSERT INTO users (username, password_hash, full_name, role)
VALUES
  ('admin', 'scrypt:32768:8:1$gdRnrV8oiN9hm1jf$3ec04dabb07fdebac196f4e31bf5d90439af5026c2d909b2e575df31d3920f458d0d71ef80fc12b61e886c0bc2192a7b7207f43db4ecd013148b77fb8eaa1f4d', 'Администратор', 'admin'),
  ('user',  'scrypt:32768:8:1$pahB0YLf8w7Ac4qZ$4db37ccd7ccea7ba809a68476b149b36ebecd280bec8db9c9d4bd77aaaef3f9abd2d39d2aff1fe103817064217e659f1bf6cc06230c0d0fe9accfe1e46cf2317',  'Пользователь',  'user')
ON CONFLICT (username) DO UPDATE
SET password_hash = EXCLUDED.password_hash,
    full_name      = EXCLUDED.full_name,
    role           = EXCLUDED.role;

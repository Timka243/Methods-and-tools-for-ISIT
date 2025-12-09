CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE visits (
    id SERIAL PRIMARY KEY,
    location_id INT REFERENCES locations(id),
    date DATE NOT NULL,
    material VARCHAR(200) NOT NULL,
    spent INT DEFAULT 0,
    discount INT DEFAULT 0
);

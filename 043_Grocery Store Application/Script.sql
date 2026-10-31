-- Create the Unit of Measure (UOM) table
CREATE TABLE IF NOT EXISTS uom (
    uom_id SERIAL PRIMARY KEY,
    uom_name VARCHAR(45) NOT NULL
);

-- Insert standard units to start with
INSERT INTO uom (uom_id, uom_name) VALUES 
(1, 'kg'),
(2, 'gram'),
(3, 'piece'),
(4, 'packet'),
(5, 'litre')
ON CONFLICT (uom_id) DO NOTHING;

-- Reset the sequence counter so new auto-incremented IDs don't conflict
SELECT setval('uom_uom_id_seq', (SELECT MAX(uom_id) FROM uom));

-- Create the Products table
CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    uom_id INT NOT NULL,
    price_per_unit NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_uom 
        FOREIGN KEY (uom_id) 
        REFERENCES uom(uom_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- Insert sample product records
INSERT INTO products (name, uom_id, price_per_unit) VALUES 
('Tomato', 1, 1.50),
('Potato', 1, 0.90),
('Apple', 1, 2.20),
('Milk', 5, 1.10),
('Rice', 4, 3.50);
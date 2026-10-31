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

-- 1. Main Orders Header Table
CREATE TABLE IF NOT EXISTS orders (
    order_id SERIAL PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    total_price NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Order Line Items / Details Table
CREATE TABLE IF NOT EXISTS order_details (
    order_detail_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity NUMERIC(10, 2) NOT NULL,
    total_price NUMERIC(10, 2) NOT NULL, -- (quantity * price_per_unit at time of order)
    CONSTRAINT fk_orders 
        FOREIGN KEY (order_id) 
        REFERENCES orders(order_id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_products 
        FOREIGN KEY (product_id) 
        REFERENCES products(product_id) 
        ON DELETE RESTRICT
);

-- Insert sample orders (Header)
-- order_id 1: Alice Johnson
-- order_id 2: Bob Smith
INSERT INTO orders (order_id, customer_name, total_price, created_at) VALUES 
(1, 'Alice Johnson', 5.60, '2026-10-30 10:15:00'),
(2, 'Bob Smith', 7.00, '2026-10-31 14:30:00')
ON CONFLICT (order_id) DO NOTHING;

-- Reset sequence counter for orders
SELECT setval('orders_order_id_seq', (SELECT MAX(order_id) FROM orders));

-- Insert sample order details (Line Items)
-- Order 1 items: 2 kg Tomatoes ($1.50/unit = $3.00) + 2 liters Milk ($1.10/unit = $2.20) -> Wait, let's match exact math:
-- Tomato (ID 1): 2 kg @ 1.50 = 3.00
-- Milk (ID 4): 2 litres @ 1.30 (let's use exact line total) -> Total order: 5.60
INSERT INTO order_details (order_id, product_id, quantity, total_price) VALUES 
(1, 1, 2.00, 3.00), -- 2 kg of Tomato
(1, 4, 2.00, 2.60), -- 2 litres of Milk
(2, 3, 2.00, 4.40), -- 2 kg of Apple (2.20 * 2)
(2, 5, 0.75, 2.62); -- 0.75 packets of Rice (3.50 * 0.75 approx)

-- Reset sequence counter for order_details
SELECT setval('order_details_order_detail_id_seq', (SELECT MAX(order_detail_id) FROM order_details));
-- Sample data for development. Safe to run more than once.

INSERT INTO uom (uom_name) VALUES
('kg'),
('gram'),
('piece'),
('packet'),
('litre')
ON CONFLICT (uom_name) DO NOTHING;

INSERT INTO products (name, icon, uom_id, price_per_unit)
SELECT v.name, v.icon, u.uom_id, v.price_per_unit
FROM (VALUES
    ('Tomato', '🍅', 'kg', 1.50),
    ('Potato', '🥔', 'kg', 0.90),
    ('Apple', '🍎', 'kg', 2.20),
    ('Banana', '🍌', 'kg', 1.30),
    ('Onion', '🧅', 'kg', 1.10),
    ('Carrot', '🥕', 'kg', 0.95),
    ('Sugar', '🍬', 'kg', 1.25),
    ('Milk', '🥛', 'litre', 1.10),
    ('Orange Juice', '🧃', 'litre', 2.49),
    ('Bread', '🍞', 'piece', 2.80),
    ('Eggs', '🥚', 'packet', 3.20),
    ('Rice', '🍚', 'packet', 3.50),
    ('Butter', '🧈', 'packet', 2.10)
) AS v(name, icon, uom_name, price_per_unit)
JOIN uom u ON u.uom_name = v.uom_name
ON CONFLICT (name) DO NOTHING;

-- Give existing products without an icon a matching emoji (never overwrites a chosen icon)
UPDATE products p SET icon = v.icon
FROM (VALUES
    ('tomato', '🍅'), ('potato', '🥔'), ('apple', '🍎'), ('banana', '🍌'), ('onion', '🧅'),
    ('carrot', '🥕'), ('sugar', '🍬'), ('milk', '🥛'), ('orange juice', '🧃'), ('juice', '🧃'),
    ('bread', '🍞'), ('egg', '🥚'), ('rice', '🍚'), ('butter', '🧈'), ('cheese', '🧀'),
    ('orange', '🍊'), ('lemon', '🍋'), ('grape', '🍇'), ('strawberr', '🍓'), ('water', '💧')
) AS v(keyword, icon)
WHERE p.icon IS NULL AND lower(p.name) LIKE '%' || v.keyword || '%';

-- Sample orders, only added to an empty orders table. Line totals are calculated from product prices.
-- Ten fixed recent orders, plus 90 generated ones over the last three months for the dashboard.
DO $$
DECLARE
    new_order_id INT;
    sample RECORD;
    customers TEXT[] := ARRAY['Maya Patel', 'Liam Novak', 'Sofia Rossi', 'Noah Fischer', 'Zoe Martin', 'Omar Haddad',
                              'Lena Schulz', 'Ethan Brooks', 'Mia Chen', 'Lucas Moreau', 'Aisha Bello', 'Tom Wagner'];
    -- Opening hours weighted towards lunch time and the evening rush
    hours INT[] := ARRAY[8, 9, 10, 11, 11, 12, 12, 12, 13, 14, 15, 16, 17, 17, 18, 18, 18, 19, 19, 20];
BEGIN
    IF EXISTS (SELECT 1 FROM orders) THEN
        RETURN;
    END IF;

    FOR sample IN
        SELECT * FROM (VALUES
            ('Jonas Becker',  12, 2, ARRAY['Orange Juice', 'Bread', 'Apple'],  ARRAY[1, 2, 2]::numeric[]),
            ('Ines Garcia',   10, 3, ARRAY['Eggs', 'Milk', 'Butter'],          ARRAY[2, 2, 1]::numeric[]),
            ('Hassan Ali',     8, 6, ARRAY['Tomato', 'Onion', 'Potato'],       ARRAY[1, 1, 2]::numeric[]),
            ('Grace Kim',      6, 2, ARRAY['Apple', 'Banana', 'Bread'],        ARRAY[1.5, 1, 1]::numeric[]),
            ('Farid Khan',     5, 4, ARRAY['Rice', 'Sugar', 'Milk'],           ARRAY[2, 1, 3]::numeric[]),
            ('Emma Weber',     3, 1, ARRAY['Banana', 'Orange Juice'],          ARRAY[1.2, 2]::numeric[]),
            ('David Lee',      2, 5, ARRAY['Potato', 'Onion', 'Carrot'],       ARRAY[3, 1.5, 1]::numeric[]),
            ('Carla Mendes',   1, 2, ARRAY['Bread', 'Eggs', 'Butter'],         ARRAY[2, 1, 1]::numeric[]),
            ('Bob Smith',      0, 3, ARRAY['Apple', 'Rice'],                   ARRAY[2, 1]::numeric[]),
            ('Alice Johnson',  0, 1, ARRAY['Tomato', 'Milk'],                  ARRAY[2, 2]::numeric[])
        ) AS s(customer_name, days_ago, hours_ago, product_names, quantities)
    LOOP
        INSERT INTO orders (customer_name, created_at)
        VALUES (sample.customer_name, now() - make_interval(days => sample.days_ago, hours => sample.hours_ago))
        RETURNING order_id INTO new_order_id;

        INSERT INTO order_details (order_id, product_id, quantity, unit_price, total_price)
        SELECT new_order_id, p.product_id, i.quantity, p.price_per_unit, round(p.price_per_unit * i.quantity, 2)
        FROM unnest(sample.product_names, sample.quantities) AS i(name, quantity)
        JOIN products p ON p.name = i.name;

        UPDATE orders
        SET total_price = (SELECT COALESCE(sum(total_price), 0) FROM order_details WHERE order_id = new_order_id)
        WHERE order_id = new_order_id;
    END LOOP;

    -- Same "random" data on every run
    PERFORM setseed(0.42);
    FOR i IN 1..90 LOOP
        INSERT INTO orders (customer_name, created_at)
        VALUES (
            customers[1 + floor(random() * array_length(customers, 1))::int],
            date_trunc('day', now())
                - make_interval(days => 1 + floor(random() * 89)::int)
                + make_interval(hours => hours[1 + floor(random() * array_length(hours, 1))::int],
                                mins => floor(random() * 60)::int)
        )
        RETURNING order_id INTO new_order_id;

        INSERT INTO order_details (order_id, product_id, quantity, unit_price, total_price)
        SELECT new_order_id, picked.product_id, picked.quantity, picked.price_per_unit, round(picked.price_per_unit * picked.quantity, 2)
        FROM (
            SELECT product_id, price_per_unit, (1 + floor(random() * 3))::numeric AS quantity
            FROM products
            ORDER BY random()
            LIMIT 1 + floor(random() * 4)::int
        ) AS picked;

        UPDATE orders
        SET total_price = (SELECT COALESCE(sum(total_price), 0) FROM order_details WHERE order_id = new_order_id)
        WHERE order_id = new_order_id;
    END LOOP;
END $$;

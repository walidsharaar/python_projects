-- Company dimension: the group companies
DROP TABLE IF EXISTS gold.dim_firma CASCADE;

CREATE TABLE gold.dim_firma AS
SELECT firma_id, firma_name, quellsystem
FROM silver.firma;

ALTER TABLE gold.dim_firma ADD PRIMARY KEY (firma_id);

-- Multi-Source Tea Data Platform
-- Phase: relational source data
-- Seed: warehouses

INSERT INTO source.warehouses (
    warehouse_id,
    warehouse_name,
    city,
    country,
    country_code,
    currency_code,
    capacity_units,
    is_active
)
VALUES
    (1001, 'London Central Warehouse', 'London', 'United Kingdom', 'GB', 'GBP', 120000, TRUE),
    (1002, 'Manchester Distribution Center', 'Manchester', 'United Kingdom', 'GB', 'GBP', 85000, TRUE),
    (1003, 'Birmingham Tea Distribution Hub', 'Birmingham', 'United Kingdom', 'GB', 'GBP', 70000, TRUE),

    (1004, 'Miami Distribution Center', 'Miami', 'United States', 'US', 'USD', 100000, TRUE),
    (1005, 'New York Tea Distribution Hub', 'New York', 'United States', 'US', 'USD', 110000, TRUE),
    (1006, 'Los Angeles Distribution Center', 'Los Angeles', 'United States', 'US', 'USD', 95000, TRUE),

    (1007, 'Amsterdam European Hub', 'Amsterdam', 'Netherlands', 'NL', 'EUR', 90000, TRUE),
    (1008, 'Berlin Central Warehouse', 'Berlin', 'Germany', 'DE', 'EUR', 80000, TRUE),

    (1009, 'Buenos Aires Distribution Center', 'Buenos Aires', 'Argentina', 'AR', 'ARS', 75000, TRUE);
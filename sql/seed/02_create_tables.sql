-- Multi-Source Tea Data Platform
-- Phase: relational source catalog
-- Execute after 01_create_schemas.sql.

-- ============================================================
-- BRANDS
-- ============================================================

CREATE TABLE IF NOT EXISTS source.brands (

    brand_id INTEGER PRIMARY KEY,

    brand_name VARCHAR(120) NOT NULL UNIQUE,

    headquarters_country VARCHAR(80) NOT NULL,

    is_fictional BOOLEAN NOT NULL DEFAULT FALSE,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT brands_name_not_blank
        CHECK (btrim(brand_name) <> ''),

    CONSTRAINT brands_country_not_blank
        CHECK (btrim(headquarters_country) <> '')

);


-- ============================================================
-- PRODUCTS
-- ============================================================

CREATE TABLE IF NOT EXISTS source.products (

    product_id INTEGER PRIMARY KEY,

    brand_id INTEGER NOT NULL,

    product_name VARCHAR(180) NOT NULL,

    tea_type VARCHAR(40) NOT NULL,

    origin_country VARCHAR(80) NOT NULL,

    product_format VARCHAR(40) NOT NULL,

    net_weight_g NUMERIC(8, 2) NOT NULL,

    units_per_package INTEGER,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT products_brand_fk
        FOREIGN KEY (brand_id)
        REFERENCES source.brands (brand_id),

    CONSTRAINT products_name_not_blank
        CHECK (btrim(product_name) <> ''),

    CONSTRAINT products_tea_type_check
        CHECK (
            tea_type IN (
                'Black Tea',
                'Green Tea',
                'Oolong',
                'White Tea',
                'Pu-erh',
                'Yellow Tea',
                'Matcha',
                'Chai',
                'Rooibos',
                'Herbal Infusion',
                'Fruit Infusion'
            )
        ),

    CONSTRAINT products_format_check
        CHECK (
            product_format IN (
                'Tea Bags',
                'Loose Leaf',
                'Tea Sachets',
                'Tin',
                'Box',
                'Pouch',
                'Matcha Tin',
                'Tea Cake'
            )
        ),

    CONSTRAINT products_weight_positive
        CHECK (net_weight_g > 0),

    CONSTRAINT products_units_positive
        CHECK (
            units_per_package IS NULL
            OR units_per_package > 0
        ),

    CONSTRAINT products_teabag_units_check
        CHECK (
            product_format NOT IN ('Tea Bags', 'Tea Sachets')
            OR units_per_package IS NOT NULL
        ),

    CONSTRAINT products_matcha_format_check
        CHECK (
            tea_type <> 'Matcha'
            OR product_format = 'Matcha Tin'
        ),

    CONSTRAINT products_tea_cake_format_check
        CHECK (
            product_format <> 'Tea Cake'
            OR tea_type = 'Pu-erh'
        )

);


-- ============================================================
-- WAREHOUSES
-- ============================================================

CREATE TABLE IF NOT EXISTS source.warehouses (

    warehouse_id INTEGER PRIMARY KEY,

    warehouse_name VARCHAR(120) NOT NULL UNIQUE,

    city VARCHAR(100) NOT NULL,

    country VARCHAR(80) NOT NULL,

    country_code CHAR(2) NOT NULL,

    currency_code CHAR(3) NOT NULL,

    capacity_units INTEGER NOT NULL,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT warehouses_name_not_blank
        CHECK (btrim(warehouse_name) <> ''),

    CONSTRAINT warehouses_city_not_blank
        CHECK (btrim(city) <> ''),

    CONSTRAINT warehouses_country_not_blank
        CHECK (btrim(country) <> ''),

    CONSTRAINT warehouses_country_code_check
        CHECK (country_code ~ '^[A-Z]{2}$'),

    CONSTRAINT warehouses_currency_code_check
        CHECK (currency_code ~ '^[A-Z]{3}$'),

    CONSTRAINT warehouses_capacity_positive
        CHECK (capacity_units > 0)

);


-- ============================================================
-- CUSTOMERS
-- ============================================================

CREATE TABLE IF NOT EXISTS source.customers (

    customer_id INTEGER PRIMARY KEY,

    first_name VARCHAR(80) NOT NULL,

    last_name VARCHAR(80) NOT NULL,

    email VARCHAR(180) NOT NULL UNIQUE,

    phone VARCHAR(40),

    country VARCHAR(80) NOT NULL,

    city VARCHAR(100) NOT NULL,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT customers_first_name_not_blank
        CHECK (btrim(first_name) <> ''),

    CONSTRAINT customers_last_name_not_blank
        CHECK (btrim(last_name) <> ''),

    CONSTRAINT customers_email_not_blank
        CHECK (btrim(email) <> ''),

    CONSTRAINT customers_country_not_blank
        CHECK (btrim(country) <> ''),

    CONSTRAINT customers_city_not_blank
        CHECK (btrim(city) <> '')

);


-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_products_brand_id
    ON source.products (brand_id);

CREATE INDEX IF NOT EXISTS idx_products_tea_type
    ON source.products (tea_type);

CREATE INDEX IF NOT EXISTS idx_products_origin_country
    ON source.products (origin_country);

CREATE INDEX IF NOT EXISTS idx_customers_country
    ON source.customers (country);

CREATE INDEX IF NOT EXISTS idx_warehouses_country
    ON source.warehouses (country);

CREATE INDEX IF NOT EXISTS idx_warehouses_currency
    ON source.warehouses (currency_code);
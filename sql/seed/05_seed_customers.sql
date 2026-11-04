-- Multi-Source Tea Data Platform
-- Phase: relational source data
-- Seed: synthetic customers
--
-- Generates 10,000 fictional customers across multiple international markets.
-- All generated email addresses use example.com and are non-real.

INSERT INTO source.customers (
    customer_id,
    first_name,
    last_name,
    email,
    phone,
    country,
    city,
    is_active,
    created_at
)

SELECT
    200000 + gs AS customer_id,

    names.first_name,

    names.last_name,

    'customer_' || (200000 + gs) || '@example.com' AS email,

    '+' ||
    CASE country
        WHEN 'United Kingdom' THEN '44'
        WHEN 'Ireland' THEN '353'
        WHEN 'France' THEN '33'
        WHEN 'Spain' THEN '34'
        WHEN 'Italy' THEN '39'
        WHEN 'Belgium' THEN '32'
        WHEN 'Netherlands' THEN '31'
        WHEN 'Germany' THEN '49'
        WHEN 'Portugal' THEN '351'
        WHEN 'United States' THEN '1'
        WHEN 'Canada' THEN '1'
        WHEN 'Mexico' THEN '52'
        WHEN 'Argentina' THEN '54'
        WHEN 'Chile' THEN '56'
        WHEN 'Uruguay' THEN '598'
        WHEN 'Brazil' THEN '55'
    END
    ||
    floor(100000000 + random() * 899999999)::bigint AS phone,

    country,

    location.city,

    random() > 0.05 AS is_active,

    TIMESTAMPTZ '2020-01-01 00:00:00'
        + random() * (
            TIMESTAMPTZ '2026-08-01 00:00:00'
            - TIMESTAMPTZ '2020-01-01 00:00:00'
        ) AS created_at

FROM (

    SELECT
        gs,

        CASE
            WHEN r < 0.24 THEN 'United Kingdom'
            WHEN r < 0.30 THEN 'United States'
            WHEN r < 0.37 THEN 'Germany'
            WHEN r < 0.43 THEN 'France'
            WHEN r < 0.49 THEN 'Spain'
            WHEN r < 0.55 THEN 'Italy'
            WHEN r < 0.61 THEN 'Netherlands'
            WHEN r < 0.66 THEN 'Ireland'
            WHEN r < 0.71 THEN 'Belgium'
            WHEN r < 0.76 THEN 'Portugal'
            WHEN r < 0.82 THEN 'Canada'
            WHEN r < 0.87 THEN 'Mexico'
            WHEN r < 0.93 THEN 'Argentina'
            WHEN r < 0.97 THEN 'Chile'
            WHEN r < 0.985 THEN 'Brazil'
            ELSE 'Uruguay'
        END AS country

    FROM (
        SELECT
            gs,
            random() AS r
        FROM generate_series(1, 10000) AS gs
    ) generated

) customers

CROSS JOIN LATERAL (

    SELECT
        CASE country

            WHEN 'United Kingdom' THEN
                (ARRAY[
                    'Oliver', 'George', 'Harry', 'Jack', 'Jacob',
                    'Noah', 'Charlie', 'Emily', 'Olivia', 'Amelia',
                    'Isla', 'Sophie'
                ])[1 + floor(random() * 12)::int]

            WHEN 'Ireland' THEN
                (ARRAY[
                    'Liam', 'Conor', 'Sean', 'Cian', 'Patrick',
                    'Aoife', 'Saoirse', 'Ciara', 'Emma', 'Niamh'
                ])[1 + floor(random() * 10)::int]

            WHEN 'France' THEN
                (ARRAY[
                    'Louis', 'Gabriel', 'Arthur', 'Hugo', 'Lucas',
                    'Jules', 'Emma', 'Louise', 'Chloé', 'Camille'
                ])[1 + floor(random() * 10)::int]

            WHEN 'Spain' THEN
                (ARRAY[
                    'Alejandro', 'Daniel', 'Pablo', 'Lucas', 'Mateo',
                    'Sergio', 'Sofía', 'Lucía', 'Martina', 'Carmen'
                ])[1 + floor(random() * 10)::int]

            WHEN 'Italy' THEN
                (ARRAY[
                    'Lorenzo', 'Matteo', 'Leonardo', 'Marco', 'Luca',
                    'Francesco', 'Sofia', 'Giulia', 'Aurora', 'Chiara'
                ])[1 + floor(random() * 10)::int]

            WHEN 'Belgium' THEN
                (ARRAY[
                    'Louis', 'Lucas', 'Arthur', 'Victor', 'Thomas',
                    'Emma', 'Louise', 'Marie', 'Charlotte', 'Julie'
                ])[1 + floor(random() * 10)::int]

            WHEN 'Netherlands' THEN
                (ARRAY[
                    'Daan', 'Lars', 'Lucas', 'Finn', 'Sem',
                    'Noah', 'Emma', 'Sophie', 'Julia', 'Lotte'
                ])[1 + floor(random() * 10)::int]

            WHEN 'Germany' THEN
                (ARRAY[
                    'Paul', 'Leon', 'Felix', 'Jonas', 'Lukas',
                    'Maximilian', 'Anna', 'Emma', 'Mia', 'Sophie'
                ])[1 + floor(random() * 10)::int]

            WHEN 'Portugal' THEN
                (ARRAY[
                    'João', 'Miguel', 'Tiago', 'Diogo', 'Francisco',
                    'Rafael', 'Maria', 'Inês', 'Beatriz', 'Leonor'
                ])[1 + floor(random() * 10)::int]

            WHEN 'United States' THEN
                (ARRAY[
                    'James', 'William', 'Benjamin', 'Lucas', 'Henry',
                    'Michael', 'Emma', 'Olivia', 'Charlotte', 'Sophia'
                ])[1 + floor(random() * 10)::int]

            WHEN 'Canada' THEN
                (ARRAY[
                    'Liam', 'Noah', 'Ethan', 'Oliver', 'Lucas',
                    'Mason', 'Emma', 'Olivia', 'Charlotte', 'Amelia'
                ])[1 + floor(random() * 10)::int]

            WHEN 'Mexico' THEN
                (ARRAY[
                    'Santiago', 'Mateo', 'Sebastián', 'Diego', 'Alejandro',
                    'Daniel', 'Sofía', 'Valentina', 'Camila', 'Mariana'
                ])[1 + floor(random() * 10)::int]

            WHEN 'Argentina' THEN
                (ARRAY[
                    'Santiago', 'Mateo', 'Tomás', 'Martín', 'Lucas',
                    'Nicolás', 'Sofía', 'Valentina', 'Martina', 'Camila'
                ])[1 + floor(random() * 10)::int]

            WHEN 'Chile' THEN
                (ARRAY[
                    'Benjamín', 'Mateo', 'Vicente', 'Sebastián', 'Tomás',
                    'Matías', 'Sofía', 'Florencia', 'Catalina', 'Antonia'
                ])[1 + floor(random() * 10)::int]

            WHEN 'Uruguay' THEN
                (ARRAY[
                    'Mateo', 'Santiago', 'Martín', 'Nicolás', 'Joaquín',
                    'Felipe', 'Sofía', 'Valentina', 'Martina', 'Agustina'
                ])[1 + floor(random() * 10)::int]

            WHEN 'Brazil' THEN
                (ARRAY[
                    'Miguel', 'Arthur', 'Heitor', 'Gabriel', 'Pedro',
                    'Lucas', 'Alice', 'Helena', 'Laura', 'Valentina'
                ])[1 + floor(random() * 10)::int]

        END AS first_name,

        (ARRAY[
            'Smith',
            'Johnson',
            'Williams',
            'Brown',
            'Jones',
            'Miller',
            'Davis',
            'Wilson',
            'Taylor',
            'Anderson',
            'Thomas',
            'Jackson',
            'White',
            'Harris',
            'Martin',
            'Thompson',
            'Garcia',
            'Martinez',
            'Robinson',
            'Clark',
            'Lewis',
            'Walker',
            'Hall',
            'Allen',
            'Young',
            'King',
            'Wright',
            'Scott',
            'Green',
            'Baker'
        ])[1 + floor(random() * 30)::int] AS last_name

) names

CROSS JOIN LATERAL (

    SELECT
        CASE country

            WHEN 'United Kingdom' THEN
                (ARRAY[
                    'London',
                    'Manchester',
                    'Birmingham',
                    'Leeds',
                    'Liverpool'
                ])[1 + floor(random() * 5)::int]

            WHEN 'Ireland' THEN
                (ARRAY[
                    'Dublin',
                    'Cork',
                    'Galway',
                    'Limerick',
                    'Waterford'
                ])[1 + floor(random() * 5)::int]

            WHEN 'France' THEN
                (ARRAY[
                    'Paris',
                    'Lyon',
                    'Marseille',
                    'Toulouse',
                    'Nice'
                ])[1 + floor(random() * 5)::int]

            WHEN 'Spain' THEN
                (ARRAY[
                    'Madrid',
                    'Barcelona',
                    'Valencia',
                    'Seville',
                    'Bilbao'
                ])[1 + floor(random() * 5)::int]

            WHEN 'Italy' THEN
                (ARRAY[
                    'Rome',
                    'Milan',
                    'Turin',
                    'Florence',
                    'Bologna'
                ])[1 + floor(random() * 5)::int]

            WHEN 'Belgium' THEN
                (ARRAY[
                    'Brussels',
                    'Antwerp',
                    'Ghent',
                    'Bruges',
                    'Leuven'
                ])[1 + floor(random() * 5)::int]

            WHEN 'Netherlands' THEN
                (ARRAY[
                    'Amsterdam',
                    'Rotterdam',
                    'Utrecht',
                    'The Hague',
                    'Eindhoven'
                ])[1 + floor(random() * 5)::int]

            WHEN 'Germany' THEN
                (ARRAY[
                    'Berlin',
                    'Munich',
                    'Hamburg',
                    'Frankfurt',
                    'Cologne'
                ])[1 + floor(random() * 5)::int]

            WHEN 'Portugal' THEN
                (ARRAY[
                    'Lisbon',
                    'Porto',
                    'Braga',
                    'Coimbra',
                    'Faro'
                ])[1 + floor(random() * 5)::int]

            WHEN 'United States' THEN
                (ARRAY[
                    'New York',
                    'Miami',
                    'Los Angeles',
                    'Chicago',
                    'Boston'
                ])[1 + floor(random() * 5)::int]

            WHEN 'Canada' THEN
                (ARRAY[
                    'Toronto',
                    'Vancouver',
                    'Montreal',
                    'Calgary',
                    'Ottawa'
                ])[1 + floor(random() * 5)::int]

            WHEN 'Mexico' THEN
                (ARRAY[
                    'Mexico City',
                    'Guadalajara',
                    'Monterrey',
                    'Puebla',
                    'Tijuana'
                ])[1 + floor(random() * 5)::int]

            WHEN 'Argentina' THEN
                (ARRAY[
                    'Buenos Aires',
                    'La Plata',
                    'Mar del Plata',
                    'Córdoba',
                    'Rosario'
                ])[1 + floor(random() * 5)::int]

            WHEN 'Chile' THEN
                (ARRAY[
                    'Santiago',
                    'Valparaíso',
                    'Concepción',
                    'Viña del Mar',
                    'La Serena'
                ])[1 + floor(random() * 5)::int]

            WHEN 'Uruguay' THEN
                (ARRAY[
                    'Montevideo',
                    'Salto',
                    'Punta del Este',
                    'Paysandú',
                    'Colonia del Sacramento'
                ])[1 + floor(random() * 5)::int]

            WHEN 'Brazil' THEN
                (ARRAY[
                    'São Paulo',
                    'Rio de Janeiro',
                    'Curitiba',
                    'Belo Horizonte',
                    'Porto Alegre'
                ])[1 + floor(random() * 5)::int]

        END AS city

) location;
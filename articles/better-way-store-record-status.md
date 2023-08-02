# A Better Way To Store Record Status
In a relational database

Relational database records often require various states; for example `active`, `pending`, `deleted` etc.

## The Naive Solution

Makes use of an `ENUM` column to define status.
```sql
-- Postgres
CREATE TYPE product_status AS ENUM ('in stock', 'on order', 'sold out', 'archived');

CREATE TABLE product (
  product_id SERIAL PRIMARY KEY,
  title VARCHAR(200) NOT NULL,
  status product_status
);
```

Where the enum values have the following semantics
| Value | State |
| ----- | ----- |
| `in stock` | This product is in stock and may be purchased by customers |
| `on order` | This product is not in stock, but is on back order and may be purchased by customers |
| `sold out` | This product is not in stock, there ia no back order and customers should not be able to purchase it. It should still be available to back office |
| `archived` | This product should not be listed on shop front or back office |

This is convenient, however
- If you need to add, remove, or reorder values, you'll need to use the `ALTER TABLE`` command, which can be slow on large tables.
- If you insert a value that's not in the enum list, MySQL will not throw an error; instead, it will insert a special error value.
- `ENUM` values are sorted based on their index numbers, which depend on the order in which the enumeration members were listed in the column specification

It is also clear that each state has various characteristics that need to be implemented in business logic.
```python
from dataclasses import dataclass

@dataclass
class ProductStatus:
    is_in_stock: bool
    is_buyable: bool
    is_active: bool

def derive_status(status: str) -> ProductStatus:
    match status:
        case 'in stock':
            return ProductStatus(is_in_stock=True, is_buyable=True, is_active=True)
        case 'on order':
            return ProductStatus(is_in_stock=False, is_buyable=True, is_active=True)
        case 'sold out':
            return ProductStatus(is_in_stock=False, is_buyable=False, is_active=True)
        case 'archived':
            return ProductStatus(is_in_stock=False, is_buyable=False, is_active=False)
        case _:
            raise ValueError('Unable to determine product status)
```
## Add state flag columns
Add state flag columns to the `product` table.
```sql
-- Postgres
CREATE TABLE product (
  product_id SERIAL PRIMARY KEY,
  title VARCHAR(250) NOT NULL,
  is_in_stock SMALLINT NOT NULL,
  is_buyable SMALLINT NOT NULL,
  is_active SMALLINT NOT NULL
);
```

This is better, but also has limitations. We cannot add any metadata to the status flags.

## Normalise the database
Normalise the database structure by adding a foreign key to a `product_status` table
```sql
-- Postgres
CREATE TABLE product_status (
  product_status_id SERIAL PRIMARY KEY,
  status_uid VARCHAR(50) NOT NULL UNIQUE,   -- unique string identifier
  description VARCHAR(250) NULL,
  is_in_stock SMALLINT NOT NULL,
  is_buyable SMALLINT NOT NULL,
  is_active SMALLINT NOT NULL
);

CREATE TABLE product (
  product_id SERIAL PRIMARY KEY,
  title VARCHAR(250) NOT NULL,
  product_status_id INTEGER NOT NULL,
  FOREIGN KEY (product_status_id) REFERENCES product_status (product_status_id)
);
```
We then now create records for th various status values, and associated state flags.
```sql
INSERT INTO product_status
    (status_uid, description, is_in_stock, is_buyable, is_active)
VALUES
    ('in stock', 'Product is in stock', 1, 1, 1),
    ('on order', 'Product is on order', 0, 1, 1),
    ('sold out', 'Product is sold out', 0, 0, 1),
    ('archived', 'Product is archived', 0, 0, 0)
;
SELECT * FROM product_status;
 product_status_id | status_uid |     description     | is_in_stock | is_buyable | is_active
-------------------+------------+---------------------+-------------+------------+-----------
                 1 | in stock   | Product is in stock |           1 |          1 |         1
                 2 | on order   | Product is on order |           0 |          1 |         1
                 3 | sold out   | Product is sold out |           0 |          0 |         1
                 4 | archived   | Product is archived |           0 |          0 |         0

INSERT INTO product
    (title, product_status_id)
VALUES
    ('EcoBoost Portable Charger', 1),
    ('AquaPure Water Filter', 2),
    ('SolarGlow Garden Lights', 3),
    ('FitFlex Yoga Mat', 4),
    ('BreezeAir Conditioner', 1),
    ('CrispSound Bluetooth Speaker', 2),
    ('SmoothBlend Juicer', 3),
    ('QuickCook Microwave Oven', 4),
    ('UltraView Binoculars', 1),
    ('ProFit Running Shoes', 1)
;
```

The unique string `status_uid` value is useful for reducing cognitive load when constructing queries.
For example...
```sql
SELECT p.title
    FROM product p
    JOIN product_status ps
        ON p.product_status_id=ps.product_status_id
WHERE
    status_uid='in stock'
;
```
is easier to understand at a glance, than
```sql
SELECT title
    FROM product
WHERE
    product_status_id=1
;
```

Another nice thing that this abstraction offers us is the ability to log status changes.
```sql
-- Postgres
CREATE TABLE product_status_log (
  product_id INTEGER NOT NULL,
  product_status_id INTEGER NOT NULL,
  logged_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  FOREIGN KEY (product_id) REFERENCES product (product_id),
  FOREIGN KEY (product_status_id) REFERENCES product_status (product_status_id)
);
```
And we get a nice log
```sql
SELECT p.title, ps.status_uid, psl.logged_at
    FROM product p
    JOIN product_status_log psl
        ON p.product_id=psl.product_id
    JOIN product_status ps
        ON psl.product_status_id=ps.product_status_id
WHERE
    p.product_id=3
ORDER BY
    psl.logged_at ASC
;
          title          | status_uid |           logged_at
-------------------------+------------+-------------------------------
 SolarGlow Garden Lights | in stock   | 2023-08-03 00:36:56.830402+02
 SolarGlow Garden Lights | on order   | 2023-08-03 00:37:01.222067+02
 SolarGlow Garden Lights | sold out   | 2023-08-03 00:37:06.101503+02
 SolarGlow Garden Lights | archived   | 2023-08-03 00:37:11.805526+02
 SolarGlow Garden Lights | in stock   | 2023-08-03 00:37:25.575631+02
(5 rows)
```

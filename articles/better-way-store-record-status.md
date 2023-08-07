# A Better Way To Store Record Status In A Relational Database

Relational database records often require transitions between various states; for example `active`, `pending`, `deleted` etc.

Various structures may be used to store this states.

## A Simple Solution

This simple solution makes use of an `ENUM` column to define status.
```sql
-- Postgres
DROP TYPE IF EXISTS product_status;
CREATE TYPE product_status AS ENUM ('in stock', 'on order', 'unavailable', 'deleted');

DROP TABLE IF EXISTS product;
CREATE TABLE product (
  product_id SERIAL PRIMARY KEY,
  title VARCHAR(200) NOT NULL,
  status product_status
);

```

These enum values have the following semantics:
| Value | Product is.. |
| ----- | ----- |
| `in stock` | In stock. May be purchased by customers. |
| `on order` | Not in stock. On back order. May *not* be purchased by customers. |
| `unavailable` | Not procurable. May *not* be purchased by customers. Available in order history. |
| `deleted` | Deleted. Not visible to any systems. |

This is convenient, however, if we need to add, remove, or reorder values, we'll need to use the `ALTER TABLE`` command, which can be slow on large tables.

It is also clear that each status has various characteristics. These now need to be implemented in business logic.
Something like:
```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProductStatus:
    """A data model for product status"""

    is_in_stock: bool
    is_buyable: bool
    is_active: bool

    @classmethod
    def create(cls, status: str) -> ProductStatus:
        """Create a `ProductStatus` instance derived from the given string"""

        match status:
            case "in stock":
                return ProductStatus(is_in_stock=True, is_buyable=True, is_active=True)
            case "on order":
                return ProductStatus(is_in_stock=False, is_buyable=True, is_active=True)
            case "unavailable":
                return ProductStatus(
                    is_in_stock=False, is_buyable=False, is_active=True
                )
            case "deleted":
                return ProductStatus(
                    is_in_stock=False, is_buyable=False, is_active=False
                )
            case _:
                raise ValueError("Unable to determine product status")

```
This is easy enough, but it does split the domain between the database and the code base.
It would be better if we could represent the state better within the database.

## Add state columns
In order to store these state values better in the database, we could add a few columns to the `product` table:
```sql
-- Postgres
DROP TABLE IF EXISTS product;
CREATE TABLE product (
  product_id SERIAL PRIMARY KEY,
  title VARCHAR(250) NOT NULL,
  is_in_stock SMALLINT NOT NULL,
  is_buyable SMALLINT NOT NULL,
  is_active SMALLINT NOT NULL
);
```

This is an improvement, as we now have status attributes linked to each product records.
But, some limitations remain.
We cannot add any metadata to the various status flags. We also would need to add further columns if we ever needed a status that requires additional state flags.

## Normalise the database
The best solution would be to abstract product status from the `product` table.
To achieve this, we normalise the database structure by adding a foreign key to a `product_status` table:
```sql
-- Postgres
DROP TYPE IF EXISTS product_status;
CREATE TABLE product_status (
  product_status_id SERIAL PRIMARY KEY,
  product_status_uid VARCHAR(50) NOT NULL UNIQUE,   -- unique string identifier
  description VARCHAR(250) NULL,
  is_in_stock SMALLINT NOT NULL,
  is_buyable SMALLINT NOT NULL,
  is_active SMALLINT NOT NULL
);

DROP TABLE IF EXISTS product;
CREATE TABLE product (
  product_id SERIAL PRIMARY KEY,
  title VARCHAR(250) NOT NULL,
  product_status_id INTEGER NOT NULL,
  FOREIGN KEY (product_status_id) REFERENCES product_status (product_status_id)
);

```
Next, let's create records for the various status values, and associated state flags.
```sql
-- Postgres
INSERT INTO product_status
    (product_status_uid, description, is_in_stock, is_buyable, is_active)
VALUES
    ('in stock', 'Product is in stock', 1, 1, 1),
    ('on order', 'Product is on back order', 0, 1, 1),
    ('unavailable', 'Product is unavailable', 0, 0, 1),
    ('deleted', 'Product is deleted', 0, 0, 0)
;
SELECT * FROM product_status;

```
Which gives us:
```
 product_status_id | product_status_uid |       description        | is_in_stock | is_buyable | is_active
-------------------+--------------------+--------------------------+-------------+------------+-----------
                 1 | in stock           | Product is in stock      |           1 |          1 |         1
                 2 | on order           | Product is on back order |           0 |          1 |         1
                 3 | unavailable        | Product is unavailable   |           0 |          0 |         1
                 4 | deleted            | Product is deleted       |           0 |          0 |         0
(4 rows)
```
And add some junk products:
```
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

The unique string `product_status_uid` value is useful for reducing cognitive load when constructing queries.
For example:
```sql
SELECT product.title, status.description
    FROM product
    JOIN product_status status
        ON product.product_status_id=status.product_status_id
WHERE
    product_status_uid='in stock'
;
           title           |     description
---------------------------+---------------------
 EcoBoost Portable Charger | Product is in stock
 BreezeAir Conditioner     | Product is in stock
 UltraView Binoculars      | Product is in stock
 ProFit Running Shoes      | Product is in stock
(4 rows)
```
is far easier to understand at a glance, than
```sql
SELECT product.title, status.description
    FROM product
    JOIN product_status status
        ON product.product_status_id=status.product_status_id
WHERE
    product.product_status_id=1
;
```

## Extensibility
Another benefit that this abstraction offers us, is the ability to extend our architecture fairly easily.
For example, to add a table to log status changes.
```sql
-- Postgres
CREATE TABLE product_status_log (
  product_id INTEGER NOT NULL,
  product_status_id INTEGER NOT NULL,
  logged_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  FOREIGN KEY (product_id) REFERENCES product (product_id),
  FOREIGN KEY (product_status_id) REFERENCES product_status (product_status_id)
);
CREATE INDEX idx_product_status ON product_status_log (product_id, product_status_id);

```
And we have a nice log
```sql
SELECT
    product.title,
    product_status.product_status_uid status,
    log.logged_at
FROM product
    JOIN product_status_log log
        ON product.product_id=log.product_id
    JOIN product_status
        ON log.product_status_id=product_status.product_status_id
WHERE
    product.product_id=3
ORDER BY
    log.logged_at ASC
;
          title          |   status    |           logged_at
-------------------------+-------------+-------------------------------
 SolarGlow Garden Lights | in stock    | 2013-08-07 02:46:21.388738+02
 SolarGlow Garden Lights | on order    | 2013-11-07 22:26:57.509255+02
 SolarGlow Garden Lights | in stock    | 2013-11-09 08:17:01.686259+02
 SolarGlow Garden Lights | on order    | 2013-11-29 14:57:19.070394+02
 SolarGlow Garden Lights | in stock    | 2013-12-07 12:07:26.662571+02
 SolarGlow Garden Lights | unavailable | 2019-01-27 02:00:31.837687+02
 SolarGlow Garden Lights | deleted     | 2023-08-07 22:00:37.574532+02
(7 rows)
```
## One Step Further
A use case may exists in which we would want ot define which transitions between statuses should be allowed.
For example, we my only want a product to be changed to status `deleted` if it was first in status `unavailable` for at least a certain amount of time.

This can be encoded into a new table structure:
```sql
-- Postgres
DROP TABLE IF EXISTS product_status_transitions;
CREATE TABLE product_status_transitions (
  from_product_status_id INTEGER NOT NULL,
  to_product_status_id INTEGER NOT NULL,
  time_must_pass INTEGER NOT NULL, -- minimum time period (in minutes) that should elapse between state change
  FOREIGN KEY (from_product_status_id) REFERENCES product_status (product_status_id),
  FOREIGN KEY (to_product_status_id) REFERENCES product_status (product_status_id),
  PRIMARY KEY (from_product_status_id, to_product_status_id)
);

```
If we wanted to define a rule, that a product must be in status `unavailable` for 5 years before it can be transitioned to `deleted`, we can create a record like:
```sql
INSERT INTO product_status_transitions
(
    from_product_status_id,
    to_product_status_id,
    time_must_pass
)
VALUES
(
    (SELECT product_status_id FROM product_status WHERE product_status_uid='unavailable'),
    (SELECT product_status_id FROM product_status WHERE product_status_uid='deleted'),
    (5 * 526000)
)
;
```
And we can craft a query that will update records that have status `unavailable` and was last updated at a time in excess of `time_must_pass`

```sql
UPDATE product
SET product_status_id = (
    SELECT product_status_id
    FROM product_status
    WHERE product_status_uid = 'deleted'
)
WHERE
product_status_id = (
    SELECT product_status_id
    FROM product_status
    WHERE product_status_uid = 'unavailable'
)
AND
(CURRENT_TIMESTAMP - (
    SELECT
        MAX(logged_at)
    FROM
        product_status_log
    WHERE
        product_status_log.product_id = product.product_id
    AND
        product_status_log.product_status_id = product.product_status_id
    )) >= (
    SELECT
        time_must_pass * INTERVAL '1 hour'
    FROM
        product_status_transitions
    WHERE
        from_product_status_id = product.product_status_id
    AND
        to_product_status_id = (
        SELECT
            product_status_id
        FROM
            product_status
        WHERE
            product_status_uid = 'deleted'
    )
);
```
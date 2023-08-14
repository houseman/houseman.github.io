# A Better Way To Store Record Status In A Relational Database

Relational database records often require transitions between various statuses; for example `active`, `pending`, `deleted` etc.

Various database structures may be used to store this status.
## A Naive Solution
The most naive database design would simply store this `status` field as a varchar type
```sql
-- Postgres
DROP TABLE IF EXISTS product CASCADE;
CREATE TABLE product (
  product_id SERIAL PRIMARY KEY,
  title VARCHAR(200) NOT NULL,
  sku VARCHAR(50) NOT NULL,
  status VARCHAR(20) NOT NULL
);

```

## A Better Solution

This improved solution makes use of an `ENUM` type to define status.
```sql
-- Postgres
DROP TYPE IF EXISTS product_status CASCADE;
CREATE TYPE product_status AS ENUM ('in stock', 'on order', 'unavailable', 'deleted');

DROP TABLE IF EXISTS product CASCADE;
CREATE TABLE product (
  product_id SERIAL PRIMARY KEY,
  title VARCHAR(200) NOT NULL,
  sku VARCHAR(200) NOT NULL,
  status product_status
);

```
This limits the possible value of `status` to one of 'in stock', 'on order', 'unavailable' or 'deleted'.

There are several benefits of using an `enum` type over a `varchar`:
1. **Data Integrity**: ensure that the value is always within a specific set of values. This is not possible with varchar (unless you add a `CHECK` constraint).
2. **Performance**: `enum` values are internally sorted according to their order in the `enum` type declaration, not their lexicographical order. This can lead to more efficient sorting and indexing.
3. **Readability**: `enum` types can make your code more readable and self-documenting by making it clear what values are allowed for a field.
4. **Storage**: `enum` values are stored as integers, which can be more space-efficient than `varchar`.

**However**, adding new values to an `enum` type requires an `ALTER TYPE` statement, which can be a heavy operation if your database is large.

### Metadata
These enum status values have the following semantics with regards to a Product:

| Value | In (warehouse) stock | On back order | Buyable | Visible in Order History |
| - | - | - | - | - |
| `in stock` | Yes | No | Yes | Yes |
| `on order` | No | Yes | Yes | Yes |
| `unavailable` | No | No | No | Yes |
| `deleted` | No | No | No | No |

These now need to be implemented in business logic.

Something like:
```python
# status.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProductStatus:
    """A data model for product status"""

    is_in_stock: bool
    is_on_back_order: bool
    is_buyable: bool
    is_active: bool

    @classmethod
    def create(cls, status: str) -> ProductStatus:
        """Create a `ProductStatus` instance derived from the given string"""

        match status.lower():
            case "in stock":
                return ProductStatus(
                    is_in_stock=True,
                    is_on_back_order=False,
                    is_buyable=True,
                    is_active=True,
                )
            case "on order":
                return ProductStatus(
                    is_in_stock=False,
                    is_on_back_order=True,
                    is_buyable=True,
                    is_active=True,
                )
            case "unavailable":
                return ProductStatus(
                    is_in_stock=False,
                    is_on_back_order=False,
                    is_buyable=False,
                    is_active=True,
                )
            case "deleted":
                return ProductStatus(
                    is_in_stock=False,
                    is_on_back_order=False,
                    is_buyable=False,
                    is_active=False,
                )
            case _:
                raise ValueError(f"Unable to determine product status '{status}'")


```
This works well enough, but it does split the domain between the database and the code base.
It would be better if we could represent the state better within the database.

## Add state columns
In order to store these state values better in the database, we could add a few columns to the `product` table:
```sql
-- Postgres
DROP TABLE IF EXISTS product CASCADE;
CREATE TABLE product (
  product_id SERIAL PRIMARY KEY,
  title VARCHAR(250) NOT NULL,
  sku VARCHAR(200) NOT NULL,
  is_in_stock BOOLEAN NOT NULL,
  is_on_back_order BOOLEAN NOT NULL,
  is_buyable BOOLEAN NOT NULL,
  is_active BOOLEAN NOT NULL
);

```

This is an improvement, as we now have status attributes for each product record.

But, some limitations remain.
We cannot add any metadata to the various status flags. We also would need to add further columns if we ever needed a status that requires additional state flags. This would necessitate an `ALTER` operation on our large `product` table.

## Normalise the database
The best solution would be to abstract product status from the `product` table.
To achieve this, we normalise the database structure by adding a foreign key to a `product_status` table:
```sql
-- Postgres
DROP TABLE IF EXISTS product_status CASCADE;
CREATE TABLE product_status (
  product_status_id SERIAL PRIMARY KEY,
  product_status_usid VARCHAR(50) NOT NULL UNIQUE,   -- unique string identifier
  description VARCHAR(250) NULL,
  is_in_stock BOOLEAN NOT NULL,
  is_on_back_order BOOLEAN NOT NULL,
  is_buyable BOOLEAN NOT NULL,
  is_active BOOLEAN NOT NULL
);

DROP TABLE IF EXISTS product CASCADE;
CREATE TABLE product (
  product_id SERIAL PRIMARY KEY,
  title VARCHAR(250) NOT NULL,
  sku VARCHAR(200) NOT NULL,
  product_status_id INTEGER NOT NULL,
  FOREIGN KEY (product_status_id) REFERENCES product_status (product_status_id)
);

```
Next, let's create records for the various status values, and associated state flags.
```sql
-- Postgres
INSERT INTO product_status
    (product_status_usid, description, is_in_stock, is_on_back_order, is_buyable, is_active)
VALUES
    ('in stock', 'Product is in stock', true, false, true, true),
    ('on order', 'Product is on back order', false, true, true, true),
    ('unavailable', 'Product is unavailable', false, false, false, true),
    ('deleted', 'Product is deleted', false, false, false, false)
;
SELECT * FROM product_status;

```
Which gives us:
```
 product_status_id | product_status_usid |       description        | is_in_stock | is_on_back_order | is_buyable | is_active
-------------------+---------------------+--------------------------+-------------+------------------+------------+-----------
                 1 | in stock            | Product is in stock      | t           | f                | t          | t
                 2 | on order            | Product is on back order | f           | t                | t          | t
                 3 | unavailable         | Product is unavailable   | f           | f                | f          | t
                 4 | deleted             | Product is deleted       | f           | f                | f          | f
(4 rows)

```
And add some junk product data:
```sql
INSERT INTO product
    (title, sku, product_status_id)
VALUES
    ('EcoBoost Portable Charger', 'SKU-ECB-1234', 1),
    ('AquaPure Water Filter', 'SKU-AQPF-5678', 2),
    ('SolarGlow Garden Lights', 'SKU-SGL-9101', 3),
    ('FitFlex Yoga Mat', 'SKU-FFYM-1121', 4),
    ('BreezeAir Conditioner', 'SKU-BAC-3141', 1),
    ('CrispSound Bluetooth Speaker', 'SKU-CSBS-5161', 2),
    ('SmoothBlend Juicer', 'SKU-SBJ-7181', 3),
    ('QuickCook Microwave Oven', 'SKU-QCMO-9201', 4),
    ('UltraView Binoculars', 'SKU-UVB-1221', 1),
    ('ProFit Running Shoes', 'SKU-PFRS-3241', 1)
;

```

### The value of a usid
The unique string identifier (usid) `product_status_usid` value is useful for reducing cognitive load when constructing queries.
For example:
```sql
SELECT
    product.title,
    product.sku,
    product_status.description status
FROM
    product
JOIN
    product_status
    ON
        product.product_status_id=product_status.product_status_id
WHERE
    product_status_usid='in stock'
;
```
```

           title           |      sku      |       status
---------------------------+---------------+---------------------
 EcoBoost Portable Charger | SKU-ECB-1234  | Product is in stock
 BreezeAir Conditioner     | SKU-BAC-3141  | Product is in stock
 UltraView Binoculars      | SKU-UVB-1221  | Product is in stock
 ProFit Running Shoes      | SKU-PFRS-3241 | Product is in stock
(4 rows)
```
is far easier to understand at a glance, than
```sql
SELECT
    product.title,
    product.sku,
    product_status.description status
FROM
    product
JOIN
    product_status
    ON
        product.product_status_id=product_status.product_status_id
WHERE
    product.product_status_id=1
;

```

> Similarly, when referring to these foreign key records in code, we do not want to use a primary key integer value as a constant (as these are strictly-speaking *not* constant) identifier. Rather, we would want to use the usid for this.

## Extensibility
### Adding a new status
Should we need to add a new status (for example `pre-order`) to our system, it is as simple as adding a new record to the `product_status` table. We may want to extend the structure for this as well. Fortunately altering the `product_status` table is far quicker and less risky than doing the same to the large `product` table.
```sql
-- Postgres
ALTER TABLE
    product_status
ADD COLUMN
    is_pre_order BOOLEAN NOT NULL DEFAULT false
;

INSERT INTO
    product_status
(
    product_status_usid,
    description,
    is_in_stock,
    is_on_back_order,
    is_buyable,
    is_active,
    is_pre_order
)
VALUES
(
    'pre-order',
    'Product is available for pre-order',
    false,
    false,
    true,
    true,
    true
)
;

```

### Adding a status log
Another benefit that this abstraction offers us, is the ability to extend our architecture fairly easily.
For example, to add a table to log status changes.
```sql
-- Postgres
DROP TABLE IF EXISTS product_status_log CASCADE;
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
    product_status.product_status_usid status,
    log.logged_at
FROM product
    JOIN product_status_log log
        ON product.product_id=log.product_id
    JOIN product_status
        ON log.product_status_id=product_status.product_status_id
WHERE
    product.sku='SKU-SGL-9101'
ORDER BY
    log.logged_at ASC
;

```
```
   status    |           logged_at
-------------+-------------------------------
 in stock    | 2023-08-07 22:46:21.388738+02
 on order    | 2023-08-07 22:46:57.509255+02
 in stock    | 2023-08-07 22:47:01.686259+02
 on order    | 2023-08-07 22:47:19.070394+02
 in stock    | 2023-08-07 22:47:26.662571+02
 unavailable | 2023-08-07 22:47:31.837687+02
 deleted     | 2023-08-07 22:47:37.574532+02
(7 rows)

```

Cheers!
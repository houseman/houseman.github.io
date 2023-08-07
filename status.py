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

if __name__ == "__main__":
    product_status = ProductStatus.create("in stock")
    print(f"Status: {product_status}")

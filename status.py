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


if __name__ == "__main__":
    assert ProductStatus.create("in stock") == ProductStatus.create("IN STOCK")
    assert ProductStatus.create("unavailable").is_in_stock is False
    assert ProductStatus.create("on order").is_on_back_order is True

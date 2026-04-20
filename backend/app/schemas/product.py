from datetime import datetime
from decimal import Decimal
from enum import Enum, IntEnum
from pydantic import BaseModel

from app.models.product import (
    Currency,
    StockStatus,
)


class ExtractedProduct(
    BaseModel
):
    name: str
    description: (
        str | None
    ) = None

    img_url: str | None = None
    product_url: (
        str | None
    ) = None
    category_name: (
        str | None
    ) = None

    sku: str | None = None
    external_id: (
        int | None
    ) = None

    currency: Currency
    price: Decimal
    price_old: (
        Decimal | None
    ) = None

    stock_quantity: (
        int | None
    ) = None
    stock_status: (
        StockStatus
    ) = StockStatus.UNKNOWN

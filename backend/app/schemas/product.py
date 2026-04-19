from datetime import datetime
from decimal import Decimal
from enum import Enum, IntEnum
from pydantic import BaseModel


class Currency(Enum):
    USD = "USD"
    UAH = "UAH"
    EUR = "EUR"

class StockStatus(IntEnum):
    UNKNOWN = -1
    OUT_OF_STOCK = 0     
    CRITICAL_LOW = 1
    LOW_STOCK = 2    
    IN_STOCK = 3        


class ExtractedProduct(BaseModel):
    name: str
    description: str | None = None

    img_url: str | None = None
    product_url: str | None = None
    category_name: str | None = None
    
    sku: str | None = None
    external_id: int | None = None

    currency: Currency
    price: Decimal | None = None
    price_old: Decimal | None = None

    stock_quantity: int | None = None
    stock_status: StockStatus = StockStatus.UNKNOWN







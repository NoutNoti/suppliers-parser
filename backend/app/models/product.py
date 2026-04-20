from app.db.base import Base

from decimal import Decimal
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Numeric, Enum as SQLEnum, ForeignKey
from enum import Enum, IntEnum


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


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(255))

    img_url: Mapped[str | None] = mapped_column(String(2048))
    product_url: Mapped[str | None] = mapped_column(String(2048))
    suplier_category_name: Mapped[str | None] = mapped_column(String(255))

    sku: Mapped[str | None] = mapped_column(String(255))
    external_id: Mapped[int | None]

    price: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2))
    price_old: Mapped[Decimal | None] = mapped_column(Numeric(precision=10, scale=2))

    stock_quantity: Mapped[int | None]

    currency: Mapped[Currency] = mapped_column(
        SQLEnum(Currency, name="currency"), default=Currency.USD
    )
    stock_status: Mapped[StockStatus] = mapped_column(
        SQLEnum(StockStatus, name="stock_status"), default=StockStatus.UNKNOWN
    )
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))

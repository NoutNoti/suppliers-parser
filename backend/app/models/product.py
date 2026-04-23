from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum, IntEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.category import Category


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
    description: Mapped[str | None] = mapped_column(Text)

    img_url: Mapped[str | None] = mapped_column(String(2048))
    product_url: Mapped[str | None] = mapped_column(String(2048))
    supplier_category_name: Mapped[str | None] = mapped_column(String(255))

    supplier_name: Mapped[str | None] = mapped_column(String(255), index=True)

    sku: Mapped[str | None] = mapped_column(String(255))
    external_id: Mapped[int | None]

    price: Mapped[Decimal | None] = mapped_column(Numeric(precision=10, scale=2))
    price_old: Mapped[Decimal | None] = mapped_column(Numeric(precision=10, scale=2))

    stock_quantity: Mapped[int | None]

    currency: Mapped[Currency] = mapped_column(
        SQLEnum(Currency, name="currency"), default=Currency.USD
    )

    stock_status: Mapped[StockStatus] = mapped_column(
        SQLEnum(StockStatus, name="stock_status"), default=StockStatus.UNKNOWN
    )

    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))

    supplier_deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    category: Mapped["Category"] = relationship("Category", back_populates="products")


class ProductStockHistory(Base):
    __tablename__ = "product_stock_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

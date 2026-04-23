from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.product import Currency, StockStatus


class ProductCategoryUpdate(BaseModel):
    product_id: int
    category_id: int


class ProductCreate(BaseModel):
    name: str
    description: str | None = None

    img_url: str | None = None
    product_url: str | None = None
    supplier_category_name: str | None = None

    supplier_name: str | None = None

    sku: str | None = None
    external_id: int | None = None

    currency: Currency
    price: Decimal | None = None
    price_old: Decimal | None = None

    stock_quantity: int | None = None
    stock_status: StockStatus = StockStatus.UNKNOWN
    supplier_deleted_at: datetime | None = None


class ProductOut(ProductCreate):
    id: int
    category_id: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductListOut(BaseModel):
    items: list[ProductOut]
    total: int
    page: int
    limit: int


class ProductFilter(BaseModel):
    in_stock: bool | None = None
    out_of_stock: bool | None = None
    category_ids: list[int] | None = None
    supplier_names: list[str] | None = None
    sort: str = Field(default="price_asc", pattern="^(price_asc|price_desc)$")
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=200)

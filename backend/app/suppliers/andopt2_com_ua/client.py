import asyncio
import re
from decimal import Decimal
from email.policy import default

from bs4 import Tag

from app.schemas.product import Currency, ProductCreate
from app.suppliers.base import BaseSupplierParser, FieldExtractor, PageConfig


class SupplierAndopt2(BaseSupplierParser):
    SUPPLIER_NAME = "andopt2.com.ua"

    def __init__(self, email, password):
        super().__init__(email, password)

        self.base_url = "https://andopt2.com.ua"
        self.limit = 10000
        self.limit_separator = "&"
        self._semaphore = asyncio.Semaphore(30)

        self.PAGE_CONFIG = PageConfig(
            category_tag="#oct-menu-dropdown-menu a.oct-menu-a",
            product_block_tag="div.product-layout",
        )

        self.PRODUCT_CONFIG = {
            "name": FieldExtractor(
                selector=".us-module-title a",
                required=True,
            ),
            "product_url": FieldExtractor(
                selector=".us-module-title a",
                attribute="href",
            ),
            "img_url": FieldExtractor(
                selector=".us-module-img img",
                attribute="src",
            ),
            "sku": FieldExtractor(
                selector=".us-product-list-description",
                transform=lambda t: (
                    re.sub(
                        r"Артикул\s*-\s*",
                        "",
                        t,
                    ).strip()
                    if t
                    else None
                ),
            ),
            "external_id": FieldExtractor(
                selector="",
                attribute="data-pid",
                transform=lambda v: (int(v) if v else None),
            ),
            "price": FieldExtractor(
                selector=".us-module-price-actual",
                attribute="data-price-current",
                transform=lambda v: (Decimal(v) if v and v != "0" else None),
            ),
            "currency_raw": FieldExtractor(
                selector=".us-module-price-actual",
                attribute="data-format-price-left",
            ),
            "stock_quantity": FieldExtractor(
                selector=".us-product-quantity input.form-control",
                attribute="data-max-value",
                transform=lambda v: (int(v) if v else 0),
            ),
            "stock_text": FieldExtractor(
                selector="span[class*='quantity__']",
            ),
        }

    async def _extract_product(
        self,
        block: Tag,
        category_name: str,
    ) -> ProductCreate:
        fields = self._extract_fields_from_config(block)

        currency = self._get_currency(fields.get("currency_raw") or "$")

        return ProductCreate(
            name=fields["name"],
            product_url=fields.get("product_url"),
            img_url=fields.get("img_url"),
            sku=fields.get("sku"),
            external_id=fields.get("external_id"),
            price=fields.get("price"),
            currency=currency or Currency.USD,
            stock_quantity=fields.get("stock_quantity") or 0,
            stock_status=self._get_stock_status(fields.get("stock_text") or ""),
            supplier_category_name=category_name,
        )

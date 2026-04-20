import re
from decimal import Decimal

from bs4 import Tag

from app.suppliers.base import BaseSupplierParser, FieldExtractor, PageConfig
from app.schemas.product import ExtractedProduct, Currency, StockStatus


class SupplierDtopelectronic(BaseSupplierParser):

    def __init__(self, email, password):
        super().__init__(email, password)

        self.base_url = "http://www.dtopelectronic.com.ua"
        self.limit = 10000
        self.limit_separator = "&"

        self.PAGE_CONFIG = PageConfig(
            category_tag="nav#menu > ul > li > a",
            product_block_tag="div.product-layout",
            qty_input_tag="input[data-maximum]",
            qty_input_art="data-maximum",
        )

        self.PRODUCT_CONFIG = {
            "name": FieldExtractor(
                selector=".product-thumb__name",
                required=True,
            ),
            "product_url": FieldExtractor(
                selector=".product-thumb__name",
                attribute="href",
            ),
            "img_url": FieldExtractor(
                selector=".product-thumb__image img",
                attribute="src",
            ),
            "sku": FieldExtractor(
                selector=".product-thumb__model",
            ),
            "external_id": FieldExtractor(
                selector="button[data-pid]",
                attribute="data-pid",
                transform=lambda v: int(v) if v else None,
            ),
            "price": FieldExtractor(
                selector=".product-thumb__price",
                attribute="data-price",
                transform=lambda v: Decimal(v) if v and v != "0" else None,
            ),
            "stock_text": FieldExtractor(
                selector=".qty-indicator__text",
            ),
        }

    async def _extract_product(self, block: Tag, category_name: str) -> ExtractedProduct:
        fields = self._extract_fields_from_config(block)

        external_id = fields.get("external_id")

        # Get quantity from product detail page
        stock_quantity = 0
        if external_id:
            stock_quantity = await self._get_quantity_by_product_page(external_id)

        stock_text = fields.get("stock_text") or ""
        stock_status = self._get_stock_status(stock_text)
        if stock_quantity == 0 and stock_status == StockStatus.IN_STOCK:
            stock_status = StockStatus.UNKNOWN

        return ExtractedProduct(
            name=fields["name"],
            product_url=fields.get("product_url"),
            img_url=fields.get("img_url"),
            sku=fields.get("sku"),
            external_id=external_id,
            price=fields.get("price"),
            currency=Currency.USD,
            stock_quantity=stock_quantity,
            stock_status=stock_status,
            category_name=category_name,
        )

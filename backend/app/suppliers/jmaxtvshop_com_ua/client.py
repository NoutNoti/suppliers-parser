import re
from decimal import Decimal

from bs4 import BeautifulSoup, Tag

from app.schemas.product import Currency, ProductCreate, StockStatus
from app.suppliers.base import BaseSupplierParser, FieldExtractor, PageConfig


class SupplierJmaxtvshop(BaseSupplierParser):
    SUPPLIER_NAME = "jmaxtvshop.com.ua"

    def __init__(self, email, password):
        super().__init__(email, password)

        self.base_url = "https://www.jmaxtvshop.com.ua"
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
            "external_id": FieldExtractor(
                selector="button[data-pid]",
                attribute="data-pid",
                transform=lambda v: (int(v) if v else None),
            ),
            "price": FieldExtractor(
                selector=".product-thumb__price",
                attribute="data-price",
                transform=lambda v: (Decimal(v) if v and v != "0" else None),
            ),
        }

    async def _get_product_detail(self, product_id: int) -> dict:
        """Fetch product detail page and extract qty, sku, description."""
        url = f"{self.base_url}/index.php?route=product/product&product_id={product_id}"
        async with self._semaphore:
            resp = await self.client.get(url)
        soup = BeautifulSoup(
            resp.text,
            "html.parser",
        )

        # Quantity
        qty_tag = soup.select_one(self.PAGE_CONFIG.qty_input_tag)
        quantity = int(qty_tag[self.PAGE_CONFIG.qty_input_art]) if qty_tag else 0

        # SKU — "Код товара:XXX"
        sku = None
        model_el = soup.select_one(".product-data__item.model")
        if model_el:
            sku = re.sub(
                r"^.*?:",
                "",
                model_el.get_text(strip=True),
            ).strip()

        # Description
        description = None
        desc_el = soup.select_one("#tab-description")
        if desc_el:
            text = desc_el.get_text(strip=True)
            if text:
                description = text

        return {
            "stock_quantity": quantity,
            "sku": sku,
            "description": description,
        }

    async def _extract_product(
        self,
        block: Tag,
        category_name: str,
    ) -> ProductCreate:
        fields = self._extract_fields_from_config(block)

        external_id = fields.get("external_id")

        detail = {
            "stock_quantity": 0,
            "sku": None,
            "description": None,
        }
        if external_id:
            detail = await self._get_product_detail(external_id)

        stock_quantity = detail["stock_quantity"]
        stock_status = (
            StockStatus.IN_STOCK if stock_quantity > 0 else StockStatus.OUT_OF_STOCK
        )

        return ProductCreate(
            name=fields["name"],
            product_url=fields.get("product_url"),
            img_url=fields.get("img_url"),
            sku=detail["sku"],
            description=detail["description"],
            external_id=external_id,
            price=fields.get("price"),
            currency=Currency.USD,
            stock_quantity=stock_quantity,
            stock_status=stock_status,
            supplier_category_name=category_name,
        )

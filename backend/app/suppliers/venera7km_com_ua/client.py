import re
from decimal import Decimal
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from app.schemas.product import Currency, ProductCreate, StockStatus
from app.suppliers.base import BaseSupplierParser, FieldExtractor, PageConfig


class SupplierVenera7km(BaseSupplierParser):
    SUPPLIER_NAME = "venera7km.com.ua"

    def __init__(self, email, password):
        super().__init__(email, password)

        self.base_url = "https://venera7km.com.ua"
        self.limit = 10000
        self.limit_separator = "?"

        self.PAGE_CONFIG = PageConfig(
            category_tag="nav.ds-menu-catalog-inner a",
            product_block_tag="div.product-layout",
        )

        self.PRODUCT_CONFIG = {
            "name": FieldExtractor(
                selector="a.ds-module-title",
                required=True,
            ),
            "product_url": FieldExtractor(
                selector="a.ds-module-title",
                attribute="href",
            ),
            "img_url": FieldExtractor(
                selector=".ds-module-img-box a img",
                attribute="src",
            ),
            "external_id": FieldExtractor(
                selector="",
                attribute="data-pid",
                transform=lambda v: (int(v) if v else None),
            ),
            "sku": FieldExtractor(
                selector=".ds-module-code",
                transform=lambda v: (
                    re.sub(
                        r"^.*?:\s*",
                        "",
                        v,
                    ).strip()
                    if v
                    else None
                ),
            ),
            "price_text": FieldExtractor(
                selector=".ds-price-new",
            ),
            "price_old_text": FieldExtractor(
                selector=".ds-price-old",
            ),
        }

    async def _get_all_categories(
        self,
        category_tag: str = None,
    ) -> list:
        """Get top-level categories only (single URL path segment)."""
        # Remove x-requested-with for this request - server returns empty nav with it
        orig_headers = dict(self.client.headers)
        self.client.headers.pop(
            "x-requested-with",
            None,
        )

        resp = await self.client.get(self.base_url)

        self.client.headers.update(orig_headers)

        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(
            resp.text,
            "html.parser",
        )
        nav = soup.select_one("nav.ds-menu-catalog-inner")
        if not nav:
            return []

        categories = []
        seen_urls = set()
        for a in nav.select("a"):
            href = a.get("href", "")
            name = a.get_text(strip=True)
            if not href or not name:
                continue

            full_url = urljoin(
                self.base_url,
                href,
            )
            path = full_url.replace(
                self.base_url,
                "",
            ).strip("/")

            # Only top-level categories (single path segment, no slashes)
            if path and "/" not in path and full_url not in seen_urls:
                seen_urls.add(full_url)
                categories.append(
                    {
                        "url": full_url,
                        "name": name,
                    }
                )

        return categories

    async def _get_product_detail(self, product_url: str) -> dict:
        """Fetch product detail page and extract stock quantity."""
        async with self._semaphore:
            resp = await self.client.get(product_url)
        soup = BeautifulSoup(
            resp.text,
            "html.parser",
        )

        # Quantity from hidden input#max-product-quantity
        quantity = 0
        max_qty = soup.select_one("input#max-product-quantity")
        if max_qty:
            try:
                quantity = int(
                    max_qty.get(
                        "value",
                        0,
                    )
                )
            except (
                ValueError,
                TypeError,
            ):
                quantity = 0

        return {"stock_quantity": quantity}

    async def _extract_product(
        self,
        block: Tag,
        category_name: str,
    ) -> ProductCreate:
        fields = self._extract_fields_from_config(block)

        price_text = fields.get("price_text") or ""
        price = self._get_price(price_text)
        currency = self._get_currency(price_text) or Currency.USD

        price_old = None
        if fields.get("price_old_text"):
            price_old = self._get_price(fields["price_old_text"])

        product_url = fields.get("product_url")
        stock_quantity = 0
        if product_url:
            detail = await self._get_product_detail(product_url)
            stock_quantity = detail["stock_quantity"]

        stock_status = (
            StockStatus.IN_STOCK if stock_quantity > 0 else StockStatus.OUT_OF_STOCK
        )

        return ProductCreate(
            name=fields["name"],
            product_url=product_url,
            img_url=fields.get("img_url"),
            sku=fields.get("sku"),
            external_id=fields.get("external_id"),
            price=price,
            price_old=price_old,
            currency=currency,
            stock_quantity=stock_quantity,
            stock_status=stock_status,
            supplier_category_name=category_name,
        )

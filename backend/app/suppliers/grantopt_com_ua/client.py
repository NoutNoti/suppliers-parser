import asyncio
import re
from decimal import Decimal
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from app.schemas.product import Currency, ProductCreate, StockStatus
from app.suppliers.base import BaseSupplierParser, FieldExtractor, PageConfig


class SupplierGrantopt(BaseSupplierParser):
    SUPPLIER_NAME = "grantopt.com.ua"

    def __init__(self, email, password):
        super().__init__(email, password)

        self.base_url = "https://grantopt.com.ua"
        self.limit = 10000
        self.limit_separator = "?"
        self._semaphore = asyncio.Semaphore(3)
        self.timeout = 260

        self.PAGE_CONFIG = PageConfig(
            category_tag="a[href*='/tovar/']",
            product_block_tag="div.products__item:not(.products__item--small)",
        )

        self.PRODUCT_CONFIG = {
            "name": FieldExtractor(
                selector=".products__item-title",
                required=True,
            ),
            "product_url": FieldExtractor(
                selector=".products__item-title",
                attribute="href",
            ),
            "img_url": FieldExtractor(
                selector=".products__item-image img, .products__item-gallery .products__item-image img",
                attribute="src",
            ),
            "sku": FieldExtractor(
                selector=".products__item-id",
                transform=lambda t: (
                    re.sub(
                        r"Артикул\s*:\s*",
                        "",
                        t,
                    ).strip()
                    if t
                    else None
                ),
            ),
            "external_id": FieldExtractor(
                selector="button[data-for]",
                attribute="data-for",
                transform=lambda v: (int(v) if v else None),
            ),
            "price_raw": FieldExtractor(
                selector=".products__item-price",
            ),
            "stock_status_el": FieldExtractor(
                selector="[class*='products__item-status']",
            ),
        }

    async def _get_all_categories(
        self,
        category_tag: str = None,
    ) -> list:
        resp = await self.client.get(f"{self.base_url}/tovar/")
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(
            resp.text,
            "html.parser",
        )
        links = soup.select("a[href*='/tovar/']")

        categories = []
        seen = set()
        base_tovar = f"{self.base_url}/tovar/"

        for a in links:
            href = a.get("href", "")
            name = a.get_text(strip=True)
            if not href or not name or href in seen:
                continue
            if href == base_tovar or "?page=" in href:
                continue

            path = href.replace(base_tovar, "").strip("/")
            depth = len(path.split("/")) if path else 0
            if depth != 1:
                continue

            seen.add(href)
            categories.append(
                {
                    "url": href,
                    "name": name,
                }
            )

        return categories

    async def _extract_product(
        self,
        block: Tag,
        category_name: str,
    ) -> ProductCreate:
        fields = self._extract_fields_from_config(block)

        price_raw = fields.get("price_raw") or ""
        currency = self._get_currency(price_raw) or Currency.USD

        # Price text may contain box info: "$204.00  за ящик (120 шт.)"
        # Extract first decimal number only
        price_match = re.search(
            r"[\d,.]+",
            price_raw,
        )
        price = Decimal(price_match.group().replace(",", ".")) if price_match else None

        status_text = fields.get("stock_status_el") or ""
        status_el = block.select_one("[class*='products__item-status']")
        if status_el and "products__item-status--true" in status_el.get("class", []):
            stock_status = StockStatus.IN_STOCK
        elif status_text:
            stock_status = self._get_stock_status(status_text)
        else:
            stock_status = StockStatus.UNKNOWN

        return ProductCreate(
            name=fields["name"],
            product_url=fields.get("product_url"),
            img_url=fields.get("img_url"),
            sku=fields.get("sku"),
            external_id=fields.get("external_id"),
            price=price,
            currency=currency,
            stock_status=stock_status,
            supplier_category_name=category_name,
        )

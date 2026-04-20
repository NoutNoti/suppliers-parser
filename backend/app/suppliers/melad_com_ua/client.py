import re
import asyncio
from decimal import Decimal
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from app.suppliers.base import BaseSupplierParser, FieldExtractor, PageConfig
from app.schemas.product import ExtractedProduct, Currency, StockStatus


class SupplierMelad(BaseSupplierParser):

    def __init__(self, email, password):
        super().__init__(email, password)

        self.base_url = "https://melad.com.ua"
        self.limit = 10000
        self.limit_separator = "?"
        self.login_path = "/login/"
        self.login_fail_indicator = "/login"
        self._semaphore = asyncio.Semaphore(10)

        self.PAGE_CONFIG = PageConfig(
            category_tag="[class*='menu'] a",
            product_block_tag="div.product-layout",
        )

        self.PRODUCT_CONFIG = {
            "name": FieldExtractor(
                selector=".caption a",
                required=True,
            ),
            "product_url": FieldExtractor(
                selector=".caption a",
                attribute="href",
            ),
            "img_url": FieldExtractor(
                selector=".image img",
                attribute="src",
            ),
            "sku": FieldExtractor(
                selector=".kod_sku b",
            ),
            "price_raw": FieldExtractor(
                selector=".price",
            ),
            "cart_button": FieldExtractor(
                selector="button.add_to_cart",
                attribute="onclick",
            ),
        }

    async def _get_all_categories(self, category_tag: str = None) -> list:
        resp = await self.client.get(self.base_url)
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        links = soup.select("[class*='menu'] a")

        all_urls = set()
        url_to_name = {}
        base = f"{self.base_url}/"
        skip_words = ["login", "register", "wishlist", "delivery", "account",
                       "order", "transaction", "download", "logout",
                       "simpleregister", "forgot", "drop", "top-sale",
                       "sale", "new_prod", "ucenka"]

        for a in links:
            href = a.get("href", "")
            name = a.get_text(strip=True)
            if not href or not name or "melad.com.ua" not in href:
                continue
            if any(w in href.lower() for w in skip_words):
                continue
            if href == base or "index.php" in href:
                continue

            path = href.replace(base, "").strip("/")
            if not path:
                continue

            all_urls.add(href.rstrip("/"))
            url_to_name[href.rstrip("/")] = name

        # Keep only leaf categories (no other URL starts with this URL + "/")
        leaf_categories = []
        seen = set()
        for url in sorted(all_urls):
            is_parent = any(
                other != url and other.startswith(url + "/")
                for other in all_urls
            )
            if not is_parent and url not in seen:
                seen.add(url)
                leaf_categories.append({
                    "url": url,
                    "name": url_to_name[url],
                })

        return leaf_categories

    async def _extract_product(self, block: Tag, category_name: str) -> ExtractedProduct:
        fields = self._extract_fields_from_config(block)

        price_raw = fields.get("price_raw") or ""
        currency = self._get_currency(price_raw) or Currency.USD
        price = self._get_price(price_raw)

        # Extract external_id from cart.add('5488', ...) onclick
        external_id = None
        onclick = fields.get("cart_button") or ""
        id_match = re.search(r"cart\.add\('(\d+)'", onclick)
        if id_match:
            external_id = int(id_match.group(1))

        # If product has an "add to cart" button, it's in stock
        stock_status = StockStatus.IN_STOCK if onclick else StockStatus.UNKNOWN

        return ExtractedProduct(
            name=fields["name"],
            product_url=fields.get("product_url"),
            img_url=fields.get("img_url"),
            sku=fields.get("sku"),
            external_id=external_id,
            price=price,
            currency=currency,
            stock_status=stock_status,
            category_name=category_name,
        )

import asyncio
import re
from decimal import Decimal
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from app.schemas.product import Currency, ProductCreate, StockStatus
from app.suppliers.base import BaseSupplierParser, FieldExtractor, PageConfig


class SupplierJumpex(BaseSupplierParser):
    SUPPLIER_NAME = "jumpex.com.ua"

    def __init__(self, email, password):
        super().__init__(email, password)

        self.base_url = "https://jumpex.com.ua"
        self.limit = 10000
        self.limit_separator = "?"

        self.PAGE_CONFIG = PageConfig(
            category_tag="div.catalog_treenameClass a",
            product_block_tag="div.product",
        )

        self.PRODUCT_CONFIG = {
            "name": FieldExtractor(
                selector=".name a",
                required=True,
            ),
            "product_url": FieldExtractor(
                selector=".name a",
                attribute="href",
            ),
            "img_url": FieldExtractor(
                selector=".image_block img.jshop_img",
                attribute="src",
            ),
            "price_raw": FieldExtractor(
                selector=".jshop_price span",
            ),
            "stock_text": FieldExtractor(
                selector="[class*='avail']",
            ),
            "external_id": FieldExtractor(
                selector="input[name='product_id']",
                attribute="value",
            ),
        }

    async def _login(self):
        """Joomla login: потрібен CSRF токен з форми"""
        resp = await self.client.get(f"{self.base_url}/login")
        soup = BeautifulSoup(
            resp.text,
            "html.parser",
        )

        login_form = None
        for form in soup.select("form"):
            if form.select_one("input[type='password']"):
                login_form = form
                break

        csrf_token = None
        if login_form:
            for inp in login_form.select("input[type='hidden']"):
                name = inp.get("name", "")
                if len(name) == 32 and inp.get("value") == "1":
                    csrf_token = name
                    break

        data = {
            "username": self.email,
            "passwd": self.password,
        }
        if csrf_token:
            data[csrf_token] = "1"

        resp = await self.client.post(
            f"{self.base_url}/user/loginsave",
            data=data,
        )

        if resp.status_code != 200 or "logout" not in resp.text.lower():
            raise ConnectionError(f"Login failed for {self.email} at {self.base_url}")

    async def _get_all_categories(
        self,
        category_tag: str = None,
    ) -> list:
        resp = await self.client.get(self.base_url)
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(
            resp.text,
            "html.parser",
        )
        links = soup.select("div.catalog_treenameClass a")

        all_urls = {}
        skip_words = [
            "login",
            "logout",
            "about",
            "delivery",
            "contacts",
            "search",
            "registration",
            "recover",
            "cart",
            "user",
            "wishlist",
            "orders",
        ]

        for a in links:
            href = a.get("href", "")
            name = a.get_text(strip=True)
            if not href or not name or not href.startswith("/"):
                continue
            if any(w in href.lower() for w in skip_words):
                continue

            segments = [s for s in href.strip("/").split("/") if s]
            if len(segments) not in (1, 2):
                continue

            url = urljoin(
                self.base_url,
                href,
            )
            if url not in all_urls:
                all_urls[url] = {
                    "url": url,
                    "name": name,
                    "depth": len(segments),
                }

        # Keep subcategories (depth=2); add top-level only if it has no children
        parent_urls = set()
        for (
            url,
            data,
        ) in all_urls.items():
            if data["depth"] == 2:
                parent_url = url.rsplit("/", 1)[0]
                parent_urls.add(parent_url.rstrip("/"))

        categories = []
        for (
            url,
            data,
        ) in all_urls.items():
            if data["depth"] == 2:
                categories.append(
                    {
                        "url": url,
                        "name": data["name"],
                    }
                )
            elif data["depth"] == 1 and url.rstrip("/") not in parent_urls:
                categories.append(
                    {
                        "url": url,
                        "name": data["name"],
                    }
                )

        return categories

    async def _extract_product(
        self,
        block: Tag,
        category_name: str,
    ) -> ProductCreate | None:
        fields = self._extract_fields_from_config(block)

        name = fields.get("name")
        if not name:
            return None

        product_url = fields.get("product_url")
        if product_url:
            product_url = urljoin(
                self.base_url,
                product_url,
            )

        img_url = fields.get("img_url")
        if img_url:
            img_url = urljoin(
                self.base_url,
                img_url,
            )

        price_raw = fields.get("price_raw") or ""
        currency = self._get_currency(price_raw) or Currency.USD
        price = self._get_price(price_raw)

        stock_text = fields.get("stock_text") or ""
        stock_status = self._get_stock_status(stock_text)

        external_id = None
        ext_raw = fields.get("external_id")
        if ext_raw and ext_raw.isdigit():
            external_id = int(ext_raw)

        return ProductCreate(
            name=name,
            product_url=product_url,
            img_url=img_url,
            external_id=external_id,
            price=price,
            currency=currency,
            stock_status=stock_status,
            supplier_category_name=category_name,
        )

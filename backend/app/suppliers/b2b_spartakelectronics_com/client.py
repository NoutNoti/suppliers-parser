import re
import asyncio
import logging
from decimal import Decimal

from bs4 import (
    BeautifulSoup,
    Tag,
)
import httpx

from app.suppliers.base import (
    BaseSupplierParser,
    FieldExtractor,
    PageConfig,
)
from app.schemas.product import (
    ExtractedProduct,
    Currency,
    StockStatus,
)


class SupplierSpartakB2B(BaseSupplierParser):

    def __init__(self, email, password):
        super().__init__(email, password)

        self.base_url = "https://b2b.spartakelectronics.com"
        self.login_path = "/ru/login"

        self.PAGE_CONFIG = PageConfig(
            product_block_tag="table.footable tr",
        )

        self._semaphore = asyncio.Semaphore(20)

    async def _login(self):
        login_url = f"{self.base_url}{self.login_path}"
        resp = await self.client.get(login_url)
        if resp.status_code != 200:
            raise ConnectionError(f"Cannot reach login page: {login_url}")

        soup = BeautifulSoup(
            resp.text,
            "html.parser",
        )
        token_input = soup.select_one("input[name='_token']")
        if not token_input:
            raise ConnectionError("CSRF token not found on login page")

        csrf = token_input.get("value")
        data = {
            "_token": csrf,
            "email": self.email,
            "password": self.password,
        }
        resp = await self.client.post(
            login_url,
            data=data,
        )
        if "login" in str(resp.url).rstrip("/").split("/")[-1]:
            raise ConnectionError(f"Login failed for {self.email} at {self.base_url}")

    async def _get_all_categories(
        self,
        category_tag: str = None,
    ) -> list:
        resp = await self.client.get(f"{self.base_url}/ru/catalog/list")
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(
            resp.text,
            "html.parser",
        )
        links = soup.select("a[href*='cat=']")

        categories = []
        seen_ids = set()
        for a in links:
            href = a.get("href", "")
            name = a.get_text(strip=True)
            m = re.search(
                r"cat=(\d+)",
                href,
            )
            if not m or not name:
                continue
            cat_id = m.group(1)
            if cat_id in seen_ids:
                continue
            seen_ids.add(cat_id)
            categories.append(
                {
                    "url": f"{self.base_url}/ru/catalog/list?cat={cat_id}",
                    "name": name,
                }
            )

        return categories

    async def _get_products_by_categories(
        self,
        category_data: list,
    ):
        async def process_category(
            data,
        ):
            base_url = data["url"]
            name = data["name"]
            all_products = []
            page = 1

            while True:
                url = f"{base_url}&page={page}" if page > 1 else base_url

                try:
                    async with self._semaphore:
                        resp = await self.client.get(
                            url,
                            timeout=self.timeout,
                        )
                except httpx.ReadTimeout:
                    logging.warning(
                        "Timeout for %s page %s",
                        name,
                        page,
                    )
                    break

                if resp.status_code != 200:
                    break

                soup = BeautifulSoup(
                    resp.text,
                    "html.parser",
                )
                table = soup.select_one("table.footable")
                if not table:
                    break

                rows = table.select("tr")
                # Skip header row
                product_rows = [r for r in rows if r.select("td")]
                if not product_rows:
                    break

                tasks = [
                    self._extract_product(
                        row,
                        name,
                    )
                    for row in product_rows
                ]
                results = await asyncio.gather(*tasks)
                all_products.extend([p for p in results if p is not None])

                # Check for next page
                pag = soup.select("ul.pagination li")
                max_page = 1
                for li in pag:
                    a = li.select_one("a")
                    if a:
                        text = a.get_text(strip=True)
                        if text.isdigit():
                            max_page = max(
                                max_page,
                                int(text),
                            )

                if page >= max_page:
                    break
                page += 1

            return all_products

        results = await asyncio.gather(*[process_category(d) for d in category_data])
        products = []
        for result in results:
            products.extend(result)
        return products

    async def _extract_product(
        self,
        block: Tag,
        category_name: str,
    ) -> ExtractedProduct | None:
        cells = block.select("td")
        if len(cells) < 6:
            return None

        # Image (td 0)
        img = cells[0].select_one("img")
        img_url = None
        if img:
            src = img.get("src", "")
            img_url = f"{self.base_url}{src}" if src.startswith("/") else src

        # Name (td 1)
        name = cells[1].get_text(strip=True)
        if not name:
            return None

        # SKU / Article (td 3)
        sku_el = cells[3].select_one("span")
        sku = sku_el.get_text(strip=True) if sku_el else None

        # Price (td 4)
        price_el = cells[4].select_one("span.price")
        price_raw = price_el.get_text(strip=True) if price_el else ""
        currency = self._get_currency(price_raw) or Currency.UAH
        price = self._get_price(price_raw)

        # Stock status (td 5)
        stock_el = cells[5].select_one("span.label")
        stock_text = stock_el.get_text(strip=True) if stock_el else ""
        stock_status = self._get_stock_status(stock_text)

        # Stock quantity - look for cell with "шт." pattern
        stock_quantity = None
        for cell in cells:
            cell_text = cell.get_text(strip=True)
            if "шт" in cell_text.lower():
                qty_match = re.search(
                    r"(\d+)\s*шт",
                    cell_text,
                    re.IGNORECASE,
                )
                if qty_match:
                    stock_quantity = int(qty_match.group(1))
                    break

        # External ID from "Подробнее" link (td 6)
        external_id = None
        if len(cells) > 6:
            detail_link = cells[6].select_one("a[href*='/catalog/product/']")
            if detail_link:
                href = detail_link.get("href", "")
                m = re.search(
                    r"/catalog/product/(\d+)",
                    href,
                )
                if m:
                    external_id = int(m.group(1))

        # Product URL
        product_url = None
        if external_id:
            product_url = f"{self.base_url}/ru/catalog/product/{external_id}"

        return ExtractedProduct(
            name=name,
            product_url=product_url,
            img_url=img_url,
            external_id=external_id,
            sku=sku,
            price=price,
            currency=currency,
            stock_status=stock_status,
            stock_quantity=stock_quantity,
            category_name=category_name,
        )

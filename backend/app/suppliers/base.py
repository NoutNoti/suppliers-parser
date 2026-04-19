import re
import asyncio
from decimal import Decimal
from abc import ABC, abstractmethod
from urllib.parse import urljoin

from dataclasses import dataclass
from typing import Callable, Any
from bs4 import BeautifulSoup, Tag
import httpx
from playwright.async_api import async_playwright
import logging

from app.schemas.product import Currency, StockStatus


@dataclass
class FieldExtractor:
    selector: str = ""
    attribute: str | None = None  
    transform: Callable[[Any], Any] | None = None  
    required: bool = False
    
@dataclass
class CategoryData:
    category_tag: str

@dataclass
class PageConfig:
    category_tag: str = ""
    product_block_tag: str = "div.product-layout"
    qty_input_tag: str = "input[data-maximum]"
    qty_input_art: str = "data-maximum"

class BaseSupplierParser(ABC):

    def __init__(self, email, password):
        super().__init__()
        self.base_url = None
        self.client = None
        self.limit = 10000
        self.js_wait = False
        self.limit_separator = "/"
        
        self.PRODUCT_CONFIG: dict[str, FieldExtractor] = {}

        self.PAGE_CONFIG: PageConfig = PageConfig()
        
        self.email = email
        self.password = password
        self._semaphore = asyncio.Semaphore(10)
        self.timeout = 60.0

    async def __aenter__(self):
        headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest",
            "referer": self.base_url + "/",
        }
        self.client = httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=self.timeout)
        await self._login()
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        if self.client:
            await self.client.aclose()

    @staticmethod
    def _get_currency(text: str) -> Currency | None:
        if not text:
            return None
            
        text = text.lower().strip()

        currency_map = {
            Currency.USD: ["$", "usd", "доллар"],
            Currency.EUR: ["€", "eur", "євро", "евро"],
            Currency.UAH: ["₴", "грн", "uah", "uan"]
        }

        for currency, symbols in currency_map.items():
            if any(symbol in text for symbol in symbols):
                return currency

        return None

    @staticmethod
    def _get_price(text) -> Decimal | None:
        num = re.sub(r"[^0-9,\.]", "", text).replace(',', '.')

        try:
            return Decimal(num) if num else Decimal("0.00")
        except Exception:
            return None
    

    def _extract_fields_from_config(self, block: Tag) -> dict:
        result = {}
        for field_name, extractor in self.PRODUCT_CONFIG.items():
            if not extractor.selector:
                element = block
            else:
                element = block.select_one(extractor.selector)
            if extractor.required and element is None:
                raise ValueError(f"Required field '{field_name}' not found (selector: '{extractor.selector}')")
            if element is None:
                result[field_name] = None
                continue
            value = element.get(extractor.attribute) if extractor.attribute else element.get_text(strip=True)
            if extractor.transform and value is not None:
                value = extractor.transform(value)
            result[field_name] = value
        return result

    def _get_stock_status(self, source) -> StockStatus:
        out_of_stock_text = ["закончился", "нет в наличии"]
        critical_stock_text = ["очень мало"]
        low_stock_text = ["мало", "заканчивается"]
        in_stock_text = ["есть в наличии", "в наличии", "в наявності" ]

        text = str(source).lower()

        if any(w in text for w in out_of_stock_text):
            return StockStatus.OUT_OF_STOCK
        if any(w in text for w in critical_stock_text):
            return StockStatus.CRITICAL_LOW
        if any(w in text for w in low_stock_text):
            return StockStatus.LOW_STOCK
        if any(w in text for w in in_stock_text):
            return StockStatus.IN_STOCK

        return StockStatus.UNKNOWN

    @abstractmethod
    async def _extract_product(self, block: Tag, category_name: str):
        """Парсинг з html в схему"""
        pass


    @abstractmethod
    async def _login(self):
        """Вхід на сайт постачальника"""
        pass

    async def _get_page_html(self, url: str, wait_selector: str = None) -> str:
        """Отримання HTML сторінки через Playwright з очікуванням селектора"""
        # Передаємо куки з httpx в Playwright
        cookies = []
        for cookie in self.client.cookies.jar:
            cookies.append({
                "name": cookie.name,
                "value": cookie.value,
                "domain": cookie.domain or self.base_url.split("//")[1].split("/")[0],
                "path": cookie.path or "/",
            })
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            if cookies:
                await context.add_cookies(cookies)
            page = await context.new_page()
            await page.goto(url, wait_until="domcontentloaded")
            if wait_selector:
                try:
                    await page.wait_for_selector(wait_selector, timeout=15000)
                except Exception:
                    pass
            html = await page.content()
            await browser.close()
        return html

    async def _get_all_categories(self, category_tag: str = None) -> list:
        """Отримання всіх категрій"""
        if self.js_wait:
            html = await self._get_page_html(self.base_url, wait_selector=category_tag)
        else:
            resp = await self.client.get(self.base_url)
            if resp.status_code != 200:
                return []
            html = resp.text

        soup = BeautifulSoup(html, 'html.parser')
        category_tags = soup.select(category_tag)
        category_data = []

        for tag in category_tags:
            url = tag.get("href")
            name = tag.get_text(strip=True)
            if url:
                category_data.append({
                    "url": urljoin(self.base_url, url),
                    "name": name
                })

        return category_data


    async def _get_products_by_categories(self, category_data: list):
        product_block_tag = self.PAGE_CONFIG.product_block_tag

        async def process_category(data):
            link = data.get("url")
            name = data.get("name")
            url = f"{link}{self.limit_separator}limit={self.limit}"

            async def _get_with_retries(u: str, retries: int = 3, backoff: float = 1.0):
                attempt = 0
                while attempt < retries:
                    attempt += 1
                    try:
                        async with self._semaphore:
                            resp = await self.client.get(u, timeout=self.timeout)
                        return resp
                    except httpx.ReadTimeout:
                        logging.warning("ReadTimeout for %s (attempt %s/%s)", u, attempt, retries)
                        if attempt >= retries:
                            raise
                        await asyncio.sleep(backoff)
                        backoff *= 2
                    except httpx.HTTPError as e:
                        logging.error("HTTP error for %s: %s", u, e)
                        raise

            resp = await _get_with_retries(url)
            if resp.status_code != 200:
                return []
            html = resp.text

            soup = BeautifulSoup(html, 'html.parser')
            product_blocks = soup.select(product_block_tag)
            if not product_blocks:
                return []

            tasks = [self._extract_product(block=pb, category_name=name) for pb in product_blocks]
            return await asyncio.gather(*tasks)

        results = await asyncio.gather(*[process_category(d) for d in category_data])
        products = []
        for result in results:
            products.extend(result)
        return products

    async def get_stock_by_product_id(self, product_id: str | int = None, stock_status: StockStatus = None) -> int:
        pass

    async def parse_all(self):
        categories = await self._get_all_categories(self.PAGE_CONFIG.category_tag)
        products = await self._get_products_by_categories(categories)
        
        return products

    async def _get_quantity_by_product_page(self, product_id) -> int:
        product_url = f"{self.base_url}/index.php?route=product/product&product_id={product_id}"

        async with self._semaphore:
            product_page = await self.client.get(product_url)

        soup = BeautifulSoup(product_page, 'html.parser')

        qty_tag = soup.select_one(self.PAGE_CONFIG.qty_input_tag)

        if qty_tag is None:
            return 0

        return int(qty_tag[self.PAGE_CONFIG.qty_input_art])
    
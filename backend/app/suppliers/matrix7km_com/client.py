import re
import asyncio
from decimal import Decimal
from urllib.parse import (
    urljoin,
)

from bs4 import (
    BeautifulSoup,
    Tag,
)

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


class SupplierMatrix7km(
    BaseSupplierParser
):

    def __init__(
        self, email, password
    ):
        super().__init__(
            email, password
        )

        self.base_url = "https://matrix7km.com"
        self.limit = 10000
        self.limit_separator = (
            "?"
        )

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
                selector=".ds-module-img-box img",
                attribute="src",
            ),
            "price_raw": FieldExtractor(
                selector=".ds-price-new",
            ),
            "stock_text": FieldExtractor(
                selector=".ds-module-stock",
            ),
        }

    async def _get_all_categories(
        self,
        category_tag: str = None,
    ) -> list:
        resp = await self.client.get(
            self.base_url
        )
        if (
            resp.status_code
            != 200
        ):
            return []

        soup = BeautifulSoup(
            resp.text,
            "html.parser",
        )
        links = soup.select(
            "nav.ds-menu-catalog-inner a"
        )

        all_urls = {}
        skip_words = [
            "login",
            "logout",
            "account",
            "contact",
            "index.php",
            "wishlist",
            "compare",
            "information",
            "special",
        ]

        for a in links:
            href = a.get(
                "href", ""
            )
            name = a.get_text(
                strip=True
            )
            if (
                not href
                or not name
            ):
                continue
            if any(
                w
                in href.lower()
                for w in skip_words
            ):
                continue

            url = href.rstrip(
                "/"
            )
            # Extract path segments (skip domain and /ua/ prefix)
            path = url.replace(
                f"{self.base_url}/",
                "",
            ).replace(
                "ua/", ""
            )
            segments = [
                s
                for s in path.split(
                    "/"
                )
                if s
            ]
            if not segments:
                continue

            all_urls[url] = {
                "url": url,
                "name": name,
                "depth": len(
                    segments
                ),
            }

        # Keep only leaf categories (no other URL starts with this URL + "/")
        categories = []
        sorted_urls = sorted(
            all_urls.keys()
        )
        for (
            url
        ) in sorted_urls:
            is_parent = any(
                other != url
                and other.startswith(
                    url + "/"
                )
                for other in sorted_urls
            )
            if not is_parent:
                categories.append(
                    {
                        "url": url,
                        "name": all_urls[
                            url
                        ][
                            "name"
                        ],
                    }
                )

        return categories

    async def _extract_product(
        self,
        block: Tag,
        category_name: str,
    ) -> (
        ExtractedProduct
        | None
    ):
        fields = self._extract_fields_from_config(
            block
        )

        name = fields.get(
            "name"
        )
        if not name:
            return None

        product_url = (
            fields.get(
                "product_url"
            )
        )
        if (
            product_url
            and "?"
            in product_url
        ):
            product_url = product_url.split(
                "?"
            )[
                0
            ]
        img_url = fields.get(
            "img_url"
        )

        price_raw = (
            fields.get(
                "price_raw"
            )
            or ""
        )
        currency = (
            self._get_currency(
                price_raw
            )
            or Currency.USD
        )
        price = (
            self._get_price(
                price_raw
            )
        )

        # Stock status
        stock_text = (
            fields.get(
                "stock_text"
            )
            or ""
        )
        if stock_text:
            stock_status = self._get_stock_status(
                stock_text
            )
        else:
            # Check if block has ds-no-stock class on child
            no_stock_el = block.select_one(
                ".ds-no-stock"
            )
            stock_status = (
                StockStatus.OUT_OF_STOCK
                if no_stock_el
                else StockStatus.UNKNOWN
            )

        # External ID from data-pid attribute
        external_id = None
        pid = block.get(
            "data-pid"
        )
        if (
            pid
            and str(
                pid
            ).isdigit()
        ):
            external_id = int(
                pid
            )

        return ExtractedProduct(
            name=name,
            product_url=product_url,
            img_url=img_url,
            external_id=external_id,
            price=price,
            currency=currency,
            stock_status=stock_status,
            category_name=category_name,
        )

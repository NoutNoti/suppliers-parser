import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.dal.product import ProductDAL
from app.schemas.product import ProductFilter, ProductListOut, ProductOut
from app.services.category import CategoryService
from app.suppliers.registry import SUPPLIERS, SupplierEntry

logger = logging.getLogger(__name__)


class ProductService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.dal = ProductDAL(session=session)

    async def _parse_one_supplier(self, entry: SupplierEntry) -> list:
        """
        Parses a single supplier in isolation. Returns [] on any failure so
        that one broken supplier does not block others.
        """
        name = entry.name
        try:
            async with entry.build() as parser:
                products, cat_count = await parser.parse_all()
            logger.info(
                "Supplier %s: parsed %d products from %d categories",
                name,
                len(products),
                cat_count,
            )
            return products
        except Exception:
            logger.exception("Supplier %s: parsing failed, skipping", name)
            return []

    async def parse_all_and_store(self) -> dict:
        tasks = [self._parse_one_supplier(entry) for entry in SUPPLIERS]
        results = await asyncio.gather(*tasks)

        totals = {
            "suppliers": 0,
            "inserted": 0,
            "updated": 0,
            "restored": 0,
            "marked_deleted": 0,
        }
        for entry, products in zip(SUPPLIERS, results):
            if not products:
                continue
            try:
                stats = await self.dal.upsert_supplier_batch(entry.name, products)
                await self.session.commit()
                totals["suppliers"] += 1
                for key in ("inserted", "updated", "restored", "marked_deleted"):
                    totals[key] += stats[key]
                logger.info("Supplier %s stored: %s", entry.name, stats)
            except Exception:
                await self.session.rollback()
                logger.exception("Supplier %s: DB persist failed", entry.name)

        return totals

    async def categorize_uncategorized(self) -> dict:
        service = CategoryService(session=self.session)
        return await service.categorize_uncategorized()

    async def list_products(self, flt: ProductFilter) -> ProductListOut:
        items, total = await self.dal.list_filtered(flt)
        return ProductListOut(
            items=[ProductOut.model_validate(p) for p in items],
            total=total,
            page=flt.page,
            limit=flt.limit,
        )

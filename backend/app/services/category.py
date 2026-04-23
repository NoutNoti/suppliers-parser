import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.category_classifier import classify_category
from app.dal.category import CategoryDAL
from app.dal.product import ProductDAL

logger = logging.getLogger(__name__)


class CategoryService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.category_dal = CategoryDAL(session=session)
        self.product_dal = ProductDAL(session=session)

    async def categorize_uncategorized(self) -> dict:
        uncategorized = await self.product_dal.get_uncategorized()
        if not uncategorized:
            logger.info("No uncategorized products")
            return {"categorized": 0, "failed": 0}

        categories = await self.category_dal.get_all()
        if not categories:
            logger.warning("No categories in DB, skipping AI classification")
            return {"categorized": 0, "failed": 0}

        products_map = {p.id: p.name for p in uncategorized}
        categories_map = {c.id: c.name for c in categories}
        valid_category_ids = set(categories_map.keys())

        try:
            ai_results = await classify_category(products_map, categories_map)
        except Exception:
            logger.exception("AI classification failed, leaving products uncategorized")
            return {"categorized": 0, "failed": len(uncategorized)}

        categorized = 0
        for item in ai_results:
            product_id = item.get("product_id")
            category_id = item.get("category_id")
            if product_id in products_map and category_id in valid_category_ids:
                await self.product_dal.set_category(product_id, category_id)
                categorized += 1

        await self.session.commit()
        logger.info(
            "Categorized %d/%d products via AI", categorized, len(uncategorized)
        )
        return {"categorized": categorized, "failed": len(uncategorized) - categorized}

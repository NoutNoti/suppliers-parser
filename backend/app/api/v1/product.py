import logging
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Query

from app.api.deps import SessionDep
from app.dal.category import CategoryDAL
from app.db.session import async_session
from app.schemas.product import ProductFilter, ProductListOut
from app.services.product import ProductService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["products"])


@router.get("/products", response_model=ProductListOut)
async def list_products(
    session: SessionDep,
    in_stock: bool | None = Query(default=None),
    out_of_stock: bool | None = Query(default=None),
    category_ids: list[int] | None = Query(default=None),
    supplier_names: list[str] | None = Query(default=None),
    sort: Literal["price_asc", "price_desc"] = Query(default="price_asc"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=200),
) -> ProductListOut:
    flt = ProductFilter(
        in_stock=in_stock,
        out_of_stock=out_of_stock,
        category_ids=category_ids,
        supplier_names=supplier_names,
        sort=sort,
        page=page,
        limit=limit,
    )
    service = ProductService(session=session)
    return await service.list_products(flt)


@router.get("/categories")
async def list_categories(session: SessionDep):
    categories = await CategoryDAL(session).get_all()
    return [{"id": c.id, "name": c.name} for c in categories]


async def _run_parse_and_categorize() -> None:
    async with async_session() as session:
        service = ProductService(session=session)
        try:
            await service.parse_all_and_store()
            await service.categorize_uncategorized()
        except Exception:
            logger.exception("Manual parse job failed")


async def _run_categorize() -> None:
    async with async_session() as session:
        service = ProductService(session=session)
        try:
            await service.categorize_uncategorized()
        except Exception:
            logger.exception("Manual categorize job failed")


@router.post("/admin/parse-now")
async def trigger_parse(background_tasks: BackgroundTasks) -> dict:
    background_tasks.add_task(_run_parse_and_categorize)
    return {"status": "scheduled"}


@router.post("/admin/categorize-now")
async def trigger_categorize(background_tasks: BackgroundTasks) -> dict:
    # background_tasks.add_task(_run_categorize)
    return {"status": "scheduled"}

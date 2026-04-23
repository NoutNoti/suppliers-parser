from datetime import datetime, timezone

from sqlalchemy import case, func, literal, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Currency, Product, ProductStockHistory, StockStatus
from app.schemas.product import ProductCreate, ProductFilter

# Currency conversion rates for sorting (per requirements.md)
CURRENCY_RATE = {
    Currency.USD: 44,
    Currency.EUR: 50,
    Currency.UAH: 1,
}


class ProductDAL:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_supplier(self, supplier_name: str) -> list[Product]:
        stmt = select(Product).where(Product.supplier_name == supplier_name)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_uncategorized(self, limit: int | None = None) -> list[Product]:
        stmt = select(Product).where(
            Product.category_id.is_(None),
            Product.supplier_deleted_at.is_(None),
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def set_category(self, product_id: int, category_id: int) -> None:
        stmt = (
            update(Product)
            .where(Product.id == product_id)
            .values(category_id=category_id)
        )
        await self.session.execute(stmt)

    async def mark_supplier_deleted(self, product_ids: list[int]) -> None:
        if not product_ids:
            return
        stmt = (
            update(Product)
            .where(
                Product.id.in_(product_ids),
                Product.supplier_deleted_at.is_(None),
            )
            .values(supplier_deleted_at=datetime.now(timezone.utc))
        )
        await self.session.execute(stmt)

    async def insert_stock_history(self, rows: list[dict]) -> None:
        if not rows:
            return
        self.session.add_all(ProductStockHistory(**row) for row in rows)
        await self.session.flush()

    def _apply_product_data(self, product: Product, data: ProductCreate) -> bool:
        changed = False
        fields = (
            "name",
            "description",
            "img_url",
            "product_url",
            "supplier_category_name",
            "supplier_name",
            "sku",
            "external_id",
            "currency",
            "price",
            "price_old",
            "stock_quantity",
            "stock_status",
        )
        for field in fields:
            new_val = getattr(data, field)
            if new_val is None and field not in {
                "stock_quantity",
                "price_old",
                "description",
            }:
                continue
            if getattr(product, field) != new_val:
                setattr(product, field, new_val)
                changed = True
        return changed

    async def upsert_supplier_batch(
        self,
        supplier_name: str,
        parsed: list[ProductCreate],
    ) -> dict:
        """
        Persists a single supplier's parsed products following MVP rules:
        - New product → insert + stock history.
        - Existing product → update fields, add stock history, clear
          supplier_deleted_at if it was set.
        - Existing in DB but missing from parse → set supplier_deleted_at.

        Matching key: (supplier_name, external_id) when external_id exists,
        otherwise (supplier_name, product_url), otherwise (supplier_name, sku).
        """
        existing_products = await self.list_by_supplier(supplier_name)
        by_ext: dict[int, Product] = {}
        by_url: dict[str, Product] = {}
        by_sku: dict[str, Product] = {}
        for p in existing_products:
            if p.external_id is not None:
                by_ext[p.external_id] = p
            elif p.product_url:
                by_url[p.product_url] = p
            elif p.sku:
                by_sku[p.sku] = p

        seen_ids: set[int] = set()
        stock_rows: list[dict] = []
        inserted = 0
        updated = 0
        restored = 0

        new_products: list[Product] = []
        for data in parsed:
            match: Product | None = None
            if data.external_id is not None:
                match = by_ext.get(data.external_id)
            if match is None and data.product_url:
                match = by_url.get(data.product_url)
            if match is None and data.sku:
                match = by_sku.get(data.sku)

            if match is None:
                product = Product(
                    name=data.name,
                    description=data.description,
                    img_url=data.img_url,
                    product_url=data.product_url,
                    supplier_category_name=data.supplier_category_name,
                    supplier_name=supplier_name,
                    sku=data.sku,
                    external_id=data.external_id,
                    currency=data.currency,
                    price=data.price,
                    price_old=data.price_old,
                    stock_quantity=data.stock_quantity,
                    stock_status=data.stock_status,
                )
                self.session.add(product)
                new_products.append(product)
                inserted += 1
            else:
                self._apply_product_data(match, data)
                if match.supplier_deleted_at is not None:
                    match.supplier_deleted_at = None
                    restored += 1
                else:
                    updated += 1
                seen_ids.add(match.id)

        await self.session.flush()

        for product in new_products:
            if product.stock_quantity is not None:
                stock_rows.append(
                    {"product_id": product.id, "quantity": product.stock_quantity}
                )

        for product_id in seen_ids:
            product = next(p for p in existing_products if p.id == product_id)
            if product.stock_quantity is not None:
                stock_rows.append(
                    {"product_id": product.id, "quantity": product.stock_quantity}
                )

        await self.insert_stock_history(stock_rows)

        # Products that exist in DB but weren't parsed → mark as supplier-deleted
        missing_ids = [
            p.id
            for p in existing_products
            if p.id not in seen_ids and p.supplier_deleted_at is None
        ]
        await self.mark_supplier_deleted(missing_ids)

        return {
            "inserted": inserted,
            "updated": updated,
            "restored": restored,
            "marked_deleted": len(missing_ids),
            "total_parsed": len(parsed),
        }

    def _price_uah_expression(self):
        whens = [
            (Product.currency == currency, Product.price * literal(rate))
            for currency, rate in CURRENCY_RATE.items()
        ]
        return case(*whens, else_=Product.price * literal(1))

    async def list_filtered(self, flt: ProductFilter) -> tuple[list[Product], int]:
        stmt = select(Product).where(Product.supplier_deleted_at.is_(None))

        stock_conditions = []
        if flt.in_stock:
            stock_conditions.append(
                Product.stock_status.in_(
                    [
                        StockStatus.IN_STOCK,
                        StockStatus.LOW_STOCK,
                        StockStatus.CRITICAL_LOW,
                    ]
                )
            )
        if flt.out_of_stock:
            stock_conditions.append(Product.stock_status == StockStatus.OUT_OF_STOCK)
        if stock_conditions:
            stmt = stmt.where(or_(*stock_conditions))

        if flt.category_ids:
            stmt = stmt.where(Product.category_id.in_(flt.category_ids))

        if flt.supplier_names:
            stmt = stmt.where(Product.supplier_name.in_(flt.supplier_names))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar_one()

        # Out-of-stock always last; then sort by price in UAH equivalent
        out_of_stock_order = case(
            (Product.stock_status == StockStatus.OUT_OF_STOCK, 1),
            else_=0,
        )
        price_uah = self._price_uah_expression()
        price_order = price_uah.asc() if flt.sort == "price_asc" else price_uah.desc()

        stmt = stmt.order_by(
            out_of_stock_order.asc(),
            price_order,
            Product.id.asc(),
        )
        stmt = stmt.offset((flt.page - 1) * flt.limit).limit(flt.limit)

        result = await self.session.execute(stmt)
        items = list(result.scalars().all())
        return items, total

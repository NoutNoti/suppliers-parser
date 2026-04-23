import json
import logging
import re

from app.ai.client import gemini_client

logger = logging.getLogger(__name__)

# Keep batches small to stay under per-request token caps and let the
# rate limiter space requests out across many minutes instead of blowing
# the per-minute quota on one giant prompt.
BATCH_SIZE = 50


async def _classify_batch(
    products: dict[int, str],
    categories: dict[int, str],
) -> list[dict]:
    prompt = (
        "You are a product categorization assistant. "
        "You are given a list of available categories and a list of products. "
        "For each product, assign the most appropriate category. "
        "Return ONLY a JSON array in this exact format, no markdown, no explanation:\n"
        '[{"product_id": <int>, "category_id": <int>}, ...]\n\n'
        f"Categories: {json.dumps(categories, ensure_ascii=False)}\n\n"
        f"Products: {json.dumps(products, ensure_ascii=False)}"
    )
    raw = await gemini_client.generate(prompt, retries=6)
    raw = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
    return json.loads(raw)


async def classify_category(
    products: dict[int, str],
    categories: dict[int, str],
) -> list[dict]:
    items = list(products.items())
    results: list[dict] = []
    total_batches = (len(items) + BATCH_SIZE - 1) // BATCH_SIZE
    for idx, i in enumerate(range(0, len(items), BATCH_SIZE), start=1):
        batch = dict(items[i : i + BATCH_SIZE])
        try:
            batch_result = await _classify_batch(batch, categories)
            results.extend(batch_result)
            logger.info(
                "AI batch %d/%d: classified %d products",
                idx,
                total_batches,
                len(batch_result),
            )
        except Exception:
            # Per requirements: on persistent AI failure do nothing —
            # products in this batch stay uncategorized, move on.
            logger.exception(
                "AI batch %d/%d failed after retries, leaving %d products uncategorized",
                idx,
                total_batches,
                len(batch),
            )
    return results

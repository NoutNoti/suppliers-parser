import asyncio
import logging
import re
import time

from google import genai
from google.genai.errors import ClientError, ServerError

from app.config.settings import settings

logger = logging.getLogger(__name__)

# Gemini free tier: 10 requests/minute. We pick a safety margin and enforce
# a minimum interval between calls plus serial execution (no concurrency).
MIN_INTERVAL_SECONDS = 7.0


def _parse_retry_delay(error: Exception) -> float | None:
    """
    Extract RetryInfo.retryDelay (seconds) from a Gemini 429 response.
    Error structure: ClientError has .details dict with nested 'details' list.
    """
    try:
        details_dict = getattr(error, "details", {})
        if not isinstance(details_dict, dict):
            return None
        error_dict = details_dict.get("error", {})
        details_list = error_dict.get("details", [])
        for item in details_list:
            if "RetryInfo" in item.get("@type", ""):
                raw = item.get("retryDelay", "")
                m = re.match(r"(\d+(?:\.\d+)?)s", str(raw))
                if m:
                    return float(m.group(1))
    except Exception as e:
        logger.debug("Failed to parse retry delay: %s", e)
    return None


class GeminiClient:
    def __init__(self, model: str = "gemini-2.5-flash-lite"):
        self.model = model
        self._client: genai.Client | None = None
        self._lock = asyncio.Lock()
        self._last_call_ts = 0.0

    def _ensure_client(self) -> genai.Client:
        if self._client is None:
            if not settings.GEMINI_API_KEY:
                raise RuntimeError("GEMINI_API_KEY is not set")
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self._client

    async def _throttle(self) -> None:
        """Serialize calls and enforce MIN_INTERVAL_SECONDS between them."""
        now = time.monotonic()
        wait = MIN_INTERVAL_SECONDS - (now - self._last_call_ts)
        if wait > 0:
            await asyncio.sleep(wait)
        self._last_call_ts = time.monotonic()

    async def generate(self, prompt: str, retries: int = 6) -> str:
        backoff = 15.0
        for attempt in range(retries):
            wait = backoff
            async with self._lock:
                await self._throttle()
                try:
                    client = self._ensure_client()
                    response = await client.aio.models.generate_content(
                        model=self.model,
                        contents=prompt,
                    )
                    return response.text
                except (ClientError, ServerError) as e:
                    status = getattr(e, "status_code", None)
                    if status in (429, 503) and attempt < retries - 1:
                        wait = _parse_retry_delay(e) or backoff
                        logger.warning(
                            "Gemini %s, retry %d/%d in %.1fs",
                            status,
                            attempt + 1,
                            retries,
                            wait,
                        )
                    else:
                        raise
            # Sleep outside the lock before next attempt
            if attempt < retries - 1:
                await asyncio.sleep(wait)
            backoff *= 2


gemini_client = GeminiClient()

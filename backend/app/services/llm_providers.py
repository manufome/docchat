"""LLM provider clients: OpenAI, Google Gemini, Groq.

All providers expose the same async generator interface so the chat service
can swap them without knowing which provider is active.
"""

import asyncio
import re
from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from app.core.config import settings


async def _retry_on_429(factory, max_retries: int = 1, delay: float = 30.0):
    """Call *factory()* and await the result, retrying once on 429.

    *factory* is a zero-argument callable that returns a coroutine.
    Using a factory ensures each retry creates a fresh coroutine.
    """
    for attempt in range(max_retries + 1):
        try:
            return await factory()
        except Exception as e:
            if attempt < max_retries and "429" in str(e):
                await asyncio.sleep(delay)
            else:
                raise


async def stream_openai(
    messages: list[dict],
    api_key: str,
) -> AsyncGenerator[str, None]:
    """Stream token deltas from OpenAI GPT-4o.

    Retries once with backoff on 429 rate limits.
    """
    client = AsyncOpenAI(api_key=api_key)

    async def _call():
        return await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            stream=True,
            max_tokens=settings.openai_max_tokens,
            timeout=settings.openai_timeout_seconds,
        )

    stream = await _retry_on_429(_call)
    async for chunk in stream:
        delta = chunk.choices[0].delta if chunk.choices else None
        if delta and delta.content:
            yield delta.content


async def stream_groq(
    messages: list[dict],
    api_key: str,
) -> AsyncGenerator[str, None]:
    """Stream token deltas from Groq (Llama 3.3 70B via OpenAI-compatible API).

    Retries once with backoff on 429 rate limits.
    """
    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )

    async def _call():
        return await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            stream=True,
            max_tokens=settings.openai_max_tokens,
            timeout=settings.openai_timeout_seconds,
        )

    stream = await _retry_on_429(_call)
    async for chunk in stream:
        delta = chunk.choices[0].delta if chunk.choices else None
        if delta and delta.content:
            yield delta.content


async def stream_gemini(
    messages: list[dict],
    api_key: str,
) -> AsyncGenerator[str, None]:
    """Stream token deltas from Google Gemini.

    Converts the OpenAI-format messages list to Gemini's content format.
    Retries once with backoff on 429/RESOURCE_EXHAUSTED.
    """
    try:
        from google import genai
    except ImportError:
        raise ImportError(
            "El paquete 'google-genai' no está instalado. "
            "Ejecuta: pip install google-genai"
        )

    from google.api_core import exceptions as google_exceptions

    client = genai.Client(api_key=api_key)

    # Convert OpenAI message format to Gemini content format
    gemini_contents: list[dict] = []
    for msg in messages:
        role = "model" if msg["role"] == "assistant" else "user"
        gemini_contents.append({
            "role": role,
            "parts": [{"text": msg["content"]}],
        })

    max_retries = 1
    for attempt in range(max_retries + 1):
        try:
            response = client.models.generate_content_stream(
                model="gemini-2.0-flash",
                contents=gemini_contents,
                config={
                    "max_output_tokens": settings.openai_max_tokens,
                },
            )

            for chunk in response:
                if chunk.text:
                    yield chunk.text
            return  # Success — exit generator
        except google_exceptions.ResourceExhausted as e:
            if attempt < max_retries:
                # Parse suggested retry delay from error
                delay_match = re.search(r"retry in (\d+\.?\d*)s", str(e), re.IGNORECASE)
                delay = float(delay_match.group(1)) if delay_match else 30.0
                delay = min(delay, 60.0)  # Cap at 60s
                await asyncio.sleep(delay)
            else:
                raise  # Last attempt — let caller handle it


PROVIDER_STREAM = {
    "openai": stream_openai,
    "gemini": stream_gemini,
    "groq": stream_groq,
}

PROVIDER_DISPLAY = {
    "openai": "OpenAI",
    "gemini": "Google Gemini",
    "groq": "Groq (Llama 3.3 70B)",
}

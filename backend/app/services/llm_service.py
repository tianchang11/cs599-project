import os
from typing import Literal

from openai import AsyncOpenAI
import httpx

from app.core.exceptions import ValidationError


_llm_clients: dict[str, AsyncOpenAI] = {}


def _get_client(api_key: str, provider: str) -> AsyncOpenAI:
    if provider not in _llm_clients:
        base_url = _PROVIDER_BASE_URLS.get(provider, "")
        _llm_clients[provider] = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url or None,
            http_client=httpx.AsyncClient(timeout=60.0),
        )
    else:
        _llm_clients[provider].api_key = api_key
    return _llm_clients[provider]


_PROVIDER_BASE_URLS: dict[str, str] = {
    "deepseek": "https://api.deepseek.com",
    "openai": "",
    "anthropic": "",
}


async def chat_completion(
    messages: list[dict],
    api_key: str,
    provider: str,
    model: str,
    temperature: float = 0.7,
) -> str:
    client = _get_client(api_key, provider)

    extra_kwargs = {}
    if provider == "anthropic":
        system_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
        user_msgs = [m for m in messages if m["role"] != "system"]
        combined = ""
        for m in user_msgs:
            combined += f"\n\n{m['content']}"
        combined = f"{system_msg}\n\n{combined}".strip()

        async with client.messages.stream(
            max_tokens=4096,
            system=system_msg,
            messages=[{"role": "user", "content": combined}],
            model=model,
        ) as stream:
            content = ""
            async for text in stream.text_stream:
                content += text
            return content
    else:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            stream=False,
        )
        return response.choices[0].message.content or ""


async def chat_completion_stream(
    messages: list[dict],
    api_key: str,
    provider: str,
    model: str,
    temperature: float = 0.7,
):
    client = _get_client(api_key, provider)

    if provider == "anthropic":
        system_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
        user_msgs = [m for m in messages if m["role"] != "system"]
        combined = "\n\n".join(m["content"] for m in user_msgs)

        async with client.messages.stream(
            max_tokens=4096,
            system=system_msg,
            messages=[{"role": "user", "content": combined}],
            model=model,
        ) as stream:
            async for text in stream.text_stream:
                yield text
    else:
        stream = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

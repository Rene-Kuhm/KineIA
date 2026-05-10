import json
from collections.abc import AsyncGenerator

import httpx
from anthropic import AsyncAnthropic
from groq import AsyncGroq

from app.config import settings
from app.core.rag.prompts import MODE_INSTRUCTIONS, SYSTEM_PROMPT

DEEPSEEK_BASE = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-v4-flash"


class LLMProvider:
    def __init__(self):
        self.provider = settings.llm_provider
        if self.provider == "anthropic":
            self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        elif self.provider == "groq":
            self.client = AsyncGroq(api_key=settings.groq_api_key)
        # DeepSeek uses httpx directly (OpenAI-compatible API)

    def _build_prompts(
        self,
        query: str,
        context_docs: list[dict],
        history: list[dict] | None = None,
        mode: str = "student",
    ) -> tuple[str, str]:
        if history is None:
            history = []

        context_text = ""
        for i, doc in enumerate(context_docs, 1):
            source = doc.get("metadata", {}).get("source", "Desconocido")
            title = doc.get("metadata", {}).get("title", "Documento")
            context_text += f"\n[Fuente {i}]: {title} ({source})\n{doc.get('text', '')}\n"

        history_text = "\n".join(
            [f"{msg.get('role', 'user').capitalize()}: {msg.get('content', '')}" for msg in history]
        )

        system_prompt = SYSTEM_PROMPT.format(context=context_text, history=history_text)
        mode_instruction = MODE_INSTRUCTIONS.get(mode, MODE_INSTRUCTIONS["student"])
        user_message = f"{mode_instruction}\n\nPregunta: {query}"

        return system_prompt, user_message

    async def generate_response(
        self,
        query: str,
        context_docs: list[dict],
        history: list[dict] | None = None,
        mode: str = "student",
    ) -> str:
        system_prompt, user_message = self._build_prompts(query, context_docs, history, mode)

        if self.provider == "anthropic":
            return await self._generate_anthropic(system_prompt, user_message)
        elif self.provider == "groq":
            return await self._generate_groq(system_prompt, user_message)
        elif self.provider == "deepseek":
            return await self._generate_deepseek(system_prompt, user_message)
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")

    async def generate_response_stream(
        self,
        query: str,
        context_docs: list[dict],
        history: list[dict] | None = None,
        mode: str = "student",
    ) -> AsyncGenerator[str, None]:
        system_prompt, user_message = self._build_prompts(query, context_docs, history, mode)

        if self.provider == "anthropic":
            async for token in self._stream_anthropic(system_prompt, user_message):
                yield token
        elif self.provider == "groq":
            async for token in self._stream_groq(system_prompt, user_message):
                yield token
        elif self.provider == "deepseek":
            async for token in self._stream_deepseek(system_prompt, user_message):
                yield token
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")

    # ── DeepSeek (OpenAI-compatible) ──────────────────────────────

    async def _call_deepseek(self, messages: list[dict], stream: bool = False) -> httpx.Response:
        """Call DeepSeek API — OpenAI-compatible endpoint."""
        headers = {
            "Authorization": f"Bearer {settings.deepseek_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": DEEPSEEK_MODEL,
            "messages": messages,
            "max_tokens": 2048,
            "temperature": 0.3,
            "stream": stream,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{DEEPSEEK_BASE}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            return response

    async def _generate_deepseek(self, system_prompt: str, user_message: str) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        response = await self._call_deepseek(messages)
        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def _stream_deepseek(self, system_prompt: str, user_message: str) -> AsyncGenerator[str, None]:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        response = await self._call_deepseek(messages, stream=True)
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    content = data["choices"][0]["delta"].get("content", "")
                    if content:
                        yield content
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue

    # ── Anthropic ─────────────────────────────────────────────────

    async def _generate_anthropic(self, system_prompt: str, user_message: str) -> str:
        response = await self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            temperature=0.3,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text

    async def _stream_anthropic(self, system_prompt: str, user_message: str) -> AsyncGenerator[str, None]:
        async with self.client.messages.stream(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            temperature=0.3,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        ) as stream:
            async for text in stream.text_stream:
                if text:
                    yield text

    # ── Groq ──────────────────────────────────────────────────────

    async def _generate_groq(self, system_prompt: str, user_message: str) -> str:
        response = await self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1024,
            temperature=0.3,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        return response.choices[0].message.content

    async def _stream_groq(self, system_prompt: str, user_message: str) -> AsyncGenerator[str, None]:
        response = await self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1024,
            temperature=0.3,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            stream=True,
        )
        async for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                yield content


llm_provider = LLMProvider()

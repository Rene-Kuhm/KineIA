from anthropic import AsyncAnthropic

from app.config import settings
from app.core.rag.prompts import MODE_INSTRUCTIONS, SYSTEM_PROMPT


class LLMProvider:
    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def generate_response(
        self,
        query: str,
        context_docs: list[dict],
        history: list[dict] | None = None,
        mode: str = "student",
    ) -> str:
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

        messages = [{"role": "user", "content": f"{mode_instruction}\n\nPregunta: {query}"}]

        response = await self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            temperature=0.3,
            system=system_prompt,
            messages=messages,
        )
        return response.content[0].text


llm_provider = LLMProvider()

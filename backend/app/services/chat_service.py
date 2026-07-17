# ruff: noqa: E501
import logging
import re
import time
import uuid
from datetime import datetime

from app.core.llm.provider import llm_provider
from app.core.rag.reranker import rerank
from app.db.postgres import async_session
from app.models.conversation import Conversation
from app.models.message import Message
from app.services.rag.citations import format_sources
from app.services.rag.retriever import retriever
from sqlalchemy import delete, select

logger = logging.getLogger(__name__)

LLM_FAILURE_CODE = "AI_SERVICE_UNAVAILABLE"
LLM_FAILURE_MESSAGE = "No pude generar una respuesta porque el servicio de IA no está disponible. Intentá nuevamente más tarde."
LLM_FAILURE_RESPONSE = f"⚠️ {LLM_FAILURE_MESSAGE}\n\nCódigo: {LLM_FAILURE_CODE}"
_SAFE_EXCEPTION_CLASS = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,63}\Z")


def record_llm_failure(error: Exception) -> str:
    """Emit a bounded diagnostic without serializing provider details."""
    correlation_id = uuid.uuid4().hex
    try:
        exception_class = type(error).__name__
        if not _SAFE_EXCEPTION_CLASS.fullmatch(exception_class):
            exception_class = "Exception"
        logger.error(
            "llm_generation_failed",
            extra={
                "reason_code": LLM_FAILURE_CODE,
                "exception_class": exception_class,
                "correlation_id": correlation_id,
            },
        )
    except Exception:
        # Diagnostics are best-effort and must not affect the public response.
        pass
    return correlation_id

# Anatomical image map — matched by keyword in query
ANATOMY_IMAGES = {
    "hombro": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/48/Shoulder_joint_bf.svg/800px-Shoulder_joint_bf.svg.png",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/Pectoralis_major.png/400px-Pectoralis_major.png",
    ],
    "deltoides": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/48/Shoulder_joint_bf.svg/800px-Shoulder_joint_bf.svg.png",
    ],
    "rodilla": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/Knee_diagram_es.svg/800px-Knee_diagram_es.svg.png",
    ],
    "lca": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/Knee_diagram_es.svg/800px-Knee_diagram_es.svg.png",
    ],
    "columna": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/6/64/Illu_vertebral_column-es.svg/400px-Illu_vertebral_column-es.svg.png",
    ],
    "cadera": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Hip_joint-es.svg/600px-Hip_joint-es.svg.png",
    ],
    "codo": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/Elbow_es.svg/800px-Elbow_es.svg.png",
    ],
    "muñeca": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/16/Wrist_and_hand_deeper_palmar_es.svg/400px-Wrist_and_hand_deeper_palmar_es.svg.png",
    ],
    "mano": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/16/Wrist_and_hand_deeper_palmar_es.svg/400px-Wrist_and_hand_deeper_palmar_es.svg.png",
    ],
    "tobillo": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bf/Ankle_es.svg/800px-Ankle_es.svg.png",
    ],
    "pie": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/Blausen_0411_FootAnatomy.png/600px-Blausen_0411_FootAnatomy.png",
    ],
    "craneo": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/86/Human_skull_side_simplified_%28bones%29-es.svg/400px-Human_skull_side_simplified_%28bones%29-es.svg.png",
    ],
    "torax": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Thoracic_landmarks_anterior_view-es.svg/400px-Thoracic_landmarks_anterior_view-es.svg.png",
    ],
    "pelvis": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Pelvis_diagram_es.svg/400px-Pelvis_diagram_es.svg.png",
    ],
    "inserción": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/37/Muscles_anterior_labeled.png/600px-Muscles_anterior_labeled.png",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Muscles_posterior_labeled.png/600px-Muscles_posterior_labeled.png",
    ],
    "inserciones": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/37/Muscles_anterior_labeled.png/600px-Muscles_anterior_labeled.png",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Muscles_posterior_labeled.png/600px-Muscles_posterior_labeled.png",
    ],
    "origen": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/37/Muscles_anterior_labeled.png/600px-Muscles_anterior_labeled.png",
    ],
    "musculos": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/37/Muscles_anterior_labeled.png/600px-Muscles_anterior_labeled.png",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Muscles_posterior_labeled.png/600px-Muscles_posterior_labeled.png",
    ],
    "brazo": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/37/Muscles_anterior_labeled.png/600px-Muscles_anterior_labeled.png",
    ],
    "pierna": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Muscles_posterior_labeled.png/600px-Muscles_posterior_labeled.png",
    ],
    "corazon": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Heart_anterior_exterior_es.svg/600px-Heart_anterior_exterior_es.svg.png",
    ],
    "pulmones": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Lungs_diagram_detailed-es.svg/600px-Lungs_diagram_detailed-es.svg.png",
    ],
    "medula": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/95/Spinal_cord_diagram-es.svg/400px-Spinal_cord_diagram-es.svg.png",
    ],
}


def _normalize(text: str) -> str:
    """Remove accents for accent-insensitive matching."""
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c)).lower()


def _find_images(query: str) -> list[dict]:
    """Find relevant anatomical images based on query keywords (accent-insensitive)."""
    query_normalized = _normalize(query)
    found = []
    seen = set()
    for keyword, urls in ANATOMY_IMAGES.items():
        if _normalize(keyword) in query_normalized:
            for url in urls:
                if url not in seen:
                    seen.add(url)
                    found.append({
                        "url": url,
                        "label": keyword.capitalize(),
                        "source": "Wikimedia Commons (CC BY-SA)",
                    })
    return found[:4]  # Max 4 images per response


class ChatService:
    async def chat(
        self,
        query: str,
        area: str | None = None,
        evidence_level: str | None = None,
        mode: str = "student",
        history: list[dict] | None = None,
        user_id: str | None = None,
        conversation_id: str | None = None,
        retrieval=None,
    ) -> dict:
        # Retrieve relevant context
        docs = (retrieval or retriever).search(
            query=query, area=area, evidence_level=evidence_level)

        # Re-rank results for better relevance
        docs = rerank(query=query, documents=docs)

        # Generate response
        start_time = time.time()
        try:
            response = await llm_provider.generate_response(
                query=query, context_docs=docs, history=history, mode=mode
            )
        except Exception as error:
            record_llm_failure(error)
            response = LLM_FAILURE_RESPONSE
        response_time_ms = int((time.time() - start_time) * 1000)

        sources = format_sources(docs)

        result = {
            "answer": response,
            "sources": sources,
            "images": _find_images(query),
            "response_time_ms": response_time_ms,
        }

        # Persist conversation and messages when user is authenticated
        if user_id:
            async with async_session() as session:
                # Find or create conversation
                if conversation_id:
                    conv_result = await session.execute(
                        select(Conversation).where(
                            Conversation.id == conversation_id,
                            Conversation.user_id == user_id,
                        )
                    )
                    conversation = conv_result.scalar_one_or_none()
                    if not conversation:
                        # If conversation_id doesn't belong to user, create new one
                        conversation = Conversation(user_id=user_id, mode=mode)
                        session.add(conversation)
                        await session.flush()
                else:
                    conversation = Conversation(user_id=user_id, mode=mode)
                    session.add(conversation)
                    await session.flush()

                # Auto-update title from first user message if still default
                if conversation.title == "Nueva conversación":
                    conversation.title = query[:100] + ("..." if len(query) > 100 else "")

                # Save user message
                user_msg = Message(
                    conversation_id=conversation.id,
                    role="user",
                    content=query,
                )
                session.add(user_msg)

                # Save assistant message
                assistant_msg = Message(
                    conversation_id=conversation.id,
                    role="assistant",
                    content=response,
                    sources=sources,
                    response_time_ms=response_time_ms,
                )
                session.add(assistant_msg)

                # Update conversation timestamp
                conversation.updated_at = datetime.utcnow()

                await session.commit()
                result["conversation_id"] = conversation.id

        return result

    async def get_conversations(self, user_id: str) -> list[dict]:
        """Return all conversations for a user, ordered by most recent first."""
        async with async_session() as session:
            result = await session.execute(
                select(Conversation)
                .where(Conversation.user_id == user_id)
                .order_by(Conversation.updated_at.desc())
            )
            conversations = result.scalars().all()

            return [
                {
                    "id": c.id,
                    "title": c.title,
                    "mode": c.mode,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                    "updated_at": c.updated_at.isoformat() if c.updated_at else None,
                    "message_count": len(c.messages) if c.messages else 0,
                }
                for c in conversations
            ]

    async def get_conversation_messages(self, conversation_id: str, user_id: str) -> dict | None:
        """Return conversation info and messages for a conversation owned by the user.

        Returns None if the conversation does not exist or does not belong to the user.
        Returns a dict with conversation metadata and messages list otherwise.
        """
        async with async_session() as session:
            # Verify ownership
            conv_result = await session.execute(
                select(Conversation).where(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id,
                )
            )
            conversation = conv_result.scalar_one_or_none()
            if not conversation:
                return None

            msg_result = await session.execute(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.asc())
            )
            messages = msg_result.scalars().all()

            return {
                "conversation": {
                    "id": conversation.id,
                    "title": conversation.title,
                    "mode": conversation.mode,
                    "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
                    "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
                },
                "messages": [
                    {
                        "id": m.id,
                        "role": m.role,
                        "content": m.content,
                        "sources": format_sources(m.sources),
                        "tokens_used": m.tokens_used,
                        "response_time_ms": m.response_time_ms,
                        "created_at": m.created_at.isoformat() if m.created_at else None,
                    }
                    for m in messages
                ],
            }

    async def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """Delete a conversation and its messages. Returns True if deleted, False if not found."""
        async with async_session() as session:
            conv_result = await session.execute(
                select(Conversation).where(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id,
                )
            )
            conversation = conv_result.scalar_one_or_none()
            if not conversation:
                return False

            # Delete messages first (FK constraint)
            await session.execute(
                delete(Message).where(Message.conversation_id == conversation_id)
            )
            await session.delete(conversation)
            await session.commit()
            return True


chat_service = ChatService()

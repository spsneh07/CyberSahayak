from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Conversation, Feedback, Message


class ConversationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, title: str | None = None) -> Conversation:
        conv = Conversation(title=title or "New conversation")
        self.db.add(conv)
        self.db.commit()
        return conv

    def get(self, conversation_id: str) -> Conversation | None:
        return self.db.get(Conversation, conversation_id)

    def list_messages(self, conversation_id: str, limit: int = 50) -> list[Message]:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        return list(reversed(self.db.scalars(stmt).all()))

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        intent: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> Message:
        msg = Message(conversation_id=conversation_id, role=role, content=content, intent=intent, payload=payload)
        self.db.add(msg)
        self.db.commit()
        return msg

    def set_title_if_default(self, conv: Conversation, title: str) -> None:
        if conv.title == "New conversation":
            conv.title = title[:200]
            self.db.commit()

    def add_feedback(self, message_id: str, rating: int, comment: str | None) -> Feedback:
        fb = Feedback(message_id=message_id, rating=rating, comment=comment)
        self.db.add(fb)
        self.db.commit()
        return fb

    def get_message(self, message_id: str) -> Message | None:
        return self.db.get(Message, message_id)

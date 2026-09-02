from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
)
from sqlalchemy.orm import relationship
import enum
from app.database import Base

class LanguageEnum(str, enum.Enum):
    FA = "fa"
    EN = "en"
    AUTO = "auto"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    display_name = Column(String(100), nullable=True)
    language = Column(String(10), default=LanguageEnum.FA)
    joined_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)
    is_banned = Column(Boolean, default=False)

    links = relationship("Link", back_populates="user", cascade="all, delete-orphan")
    messages_received = relationship("Message", back_populates="receiver", cascade="all, delete-orphan")
    blocks_issued = relationship("Block", back_populates="blocker", cascade="all, delete-orphan", foreign_keys="Block.blocker_id")
    quick_replies = relationship("QuickReply", back_populates="user", cascade="all, delete-orphan")

class Link(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(100), unique=True, index=True, nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=True)
    label = Column(String(100), nullable=True)
    link_type = Column(String(50), default="telegram") # telegram, web
    default_language = Column(String(10), default=LanguageEnum.AUTO)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="links")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(100), unique=True, index=True, nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False) # The anonymous person
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False) # The owner of the link
    link_id = Column(Integer, ForeignKey("links.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(String(50), default="text")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_read = Column(Boolean, default=False)

    conversation = relationship("Conversation", back_populates="messages")
    receiver = relationship("User", back_populates="messages_received")
    reactions = relationship("Reaction", back_populates="message", cascade="all, delete-orphan")

class Reaction(Base):
    __tablename__ = "reactions"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    reactor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    emoji = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    message = relationship("Message", back_populates="reactions")

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reported_message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    reported_user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Usually unknown to reporter
    reason = Column(String(255), nullable=False)
    status = Column(String(50), default="open") # open, resolved, dismissed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Block(Base):
    __tablename__ = "blocks"

    id = Column(Integer, primary_key=True, index=True)
    blocker_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    blocked_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    blocker = relationship("User", foreign_keys=[blocker_id], back_populates="blocks_issued")

class QuickReply(Base):
    __tablename__ = "quick_replies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    trigger = Column(String(255), nullable=False)
    response = Column(Text, nullable=False)
    match_mode = Column(String(50), default="exact") # exact, contains
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="quick_replies")

class AdminRole(Base):
    __tablename__ = "admin_roles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    role = Column(String(50), nullable=False) # superadmin, admin, moderator
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False)
    target = Column(String(255), nullable=True)
    reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class CallbackToken(Base):
    __tablename__ = "callback_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(100), unique=True, index=True, nullable=False)
    payload = Column(Text, nullable=False) # JSON payload
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

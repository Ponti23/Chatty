import uuid
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base


class Source(Base):
    __tablename__ = "sources"

    source_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    filename = Column(Text, nullable=False)
    source_type = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="indexing")
    chunk_count = Column(Integer)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Tenant(Base):
    __tablename__ = "tenants"

    tenant_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    slug = Column(Text, nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    email = Column(Text, nullable=False, unique=True)
    hashed_password = Column(Text, nullable=False)
    role = Column(String(20), nullable=False, default="user")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Conversation(Base):
    __tablename__ = "conversations"

    conversation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    title = Column(Text, nullable=False, default="New conversation")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Message(Base):
    __tablename__ = "messages"

    message_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.conversation_id"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

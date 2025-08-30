from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base


node_tags = Table(
    "node_tags",
    Base.metadata,
    Column("node_id", UUID(as_uuid=True), ForeignKey("nodes.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)
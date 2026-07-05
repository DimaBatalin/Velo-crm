from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import UniqueConstraint

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.db.base import Base


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
    )

    person_tags = relationship(
        "PersonTag",
        back_populates="tag",
        cascade="all, delete-orphan",
    )


class PersonTag(Base):
    """Многие-ко-многим между Person и Tag."""
    __tablename__ = "person_tags"
    __table_args__ = (
        UniqueConstraint("person_id", "tag_id", name="uq_person_tag"),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    person_id: Mapped[int] = mapped_column(
        ForeignKey("people.id", ondelete="CASCADE")
    )

    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE")
    )

    person = relationship(
        "Person",
        back_populates="person_tags",
    )

    tag = relationship(
        "Tag",
        back_populates="person_tags",
    )

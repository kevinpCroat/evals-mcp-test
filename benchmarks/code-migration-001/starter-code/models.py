"""
Database models using SQLAlchemy 2.0 patterns.
"""
from typing import Optional
from sqlalchemy import create_engine, String, Integer, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    posts = relationship("Post", back_populates="author")

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"


class Post(Base):
    __tablename__ = 'posts'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(String(5000), nullable=True)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))

    author = relationship("User", back_populates="posts")

    def __repr__(self):
        return f"<Post(title='{self.title}')>"


def get_engine(database_url='sqlite:///test.db'):
    """Create database engine (SQLAlchemy 2.0 style)."""
    return create_engine(database_url)


def get_session(engine):
    """Create session using sessionmaker (SQLAlchemy 2.0)."""
    Session = sessionmaker(bind=engine)
    return Session()

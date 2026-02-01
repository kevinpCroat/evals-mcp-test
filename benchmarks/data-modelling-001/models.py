"""
Blog platform SQLAlchemy 2.0 models.
User, Article, Category, Tag, Comment, ArticleTag, UserFollow.
"""
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    String, Integer, Text, DateTime, ForeignKey, UniqueConstraint,
    CheckConstraint, Index, Enum as SQLEnum,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    bio: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='active')

    articles: Mapped[List["Article"]] = relationship("Article", back_populates="author", foreign_keys="Article.author_id")
    comments: Mapped[List["Comment"]] = relationship("Comment", back_populates="user", foreign_keys="Comment.user_id")
    following: Mapped[List["UserFollow"]] = relationship(
        "UserFollow", back_populates="follower", foreign_keys="UserFollow.follower_id"
    )
    followers: Mapped[List["UserFollow"]] = relationship(
        "UserFollow", back_populates="followed", foreign_keys="UserFollow.followed_id"
    )

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class Category(Base):
    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    slug: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('categories.id', ondelete='SET NULL'), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    parent: Mapped[Optional["Category"]] = relationship("Category", remote_side=[id], back_populates="subcategories")
    subcategories: Mapped[List["Category"]] = relationship("Category", back_populates="parent")
    articles: Mapped[List["Article"]] = relationship("Article", back_populates="category")

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"


class Article(Base):
    __tablename__ = 'articles'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    excerpt: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='draft')
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('categories.id', ondelete='SET NULL'), nullable=True, index=True)

    author: Mapped["User"] = relationship("User", back_populates="articles", foreign_keys=[author_id])
    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="articles")
    comments: Mapped[List["Comment"]] = relationship("Comment", back_populates="article", foreign_keys="Comment.article_id")
    tags: Mapped[List["Tag"]] = relationship("Tag", secondary="article_tags", back_populates="articles")
    article_tags: Mapped[List["ArticleTag"]] = relationship("ArticleTag", back_populates="article")

    __table_args__ = (
        Index('ix_articles_author_status', 'author_id', 'status'),
        Index('ix_articles_category_status', 'category_id', 'status'),
    )

    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title}')>"


class Tag(Base):
    __tablename__ = 'tags'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(30), nullable=False, unique=True, index=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)

    articles: Mapped[List["Article"]] = relationship("Article", secondary="article_tags", back_populates="tags")
    article_tags: Mapped[List["ArticleTag"]] = relationship("ArticleTag", back_populates="tag")

    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}')>"


class Comment(Base):
    __tablename__ = 'comments'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(String(2000), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='pending')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    edited_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    article_id: Mapped[int] = mapped_column(Integer, ForeignKey('articles.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('comments.id', ondelete='CASCADE'), nullable=True, index=True)

    article: Mapped["Article"] = relationship("Article", back_populates="comments", foreign_keys=[article_id])
    user: Mapped["User"] = relationship("User", back_populates="comments", foreign_keys=[user_id])
    parent: Mapped[Optional["Comment"]] = relationship("Comment", remote_side=[id], back_populates="replies")
    replies: Mapped[List["Comment"]] = relationship("Comment", back_populates="parent")

    __table_args__ = (
        Index('ix_comments_article_created', 'article_id', 'created_at'),
    )

    def __repr__(self):
        return f"<Comment(id={self.id})>"


class ArticleTag(Base):
    __tablename__ = 'article_tags'

    article_id: Mapped[int] = mapped_column(Integer, ForeignKey('articles.id', ondelete='CASCADE'), primary_key=True)
    tag_id: Mapped[int] = mapped_column(Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    article: Mapped["Article"] = relationship("Article", back_populates="article_tags")
    tag: Mapped["Tag"] = relationship("Tag", back_populates="article_tags")

    def __repr__(self):
        return f"<ArticleTag(article_id={self.article_id}, tag_id={self.tag_id})>"


class UserFollow(Base):
    __tablename__ = 'user_follows'

    follower_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    followed_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint('follower_id != followed_id', name='no_self_follow'),
        Index('ix_user_follows_followed_id', 'followed_id'),
        Index('ix_user_follows_follower_id', 'follower_id'),
    )

    follower: Mapped["User"] = relationship("User", back_populates="following", foreign_keys=[follower_id])
    followed: Mapped["User"] = relationship("User", back_populates="followers", foreign_keys=[followed_id])

    def __repr__(self):
        return f"<UserFollow(follower_id={self.follower_id}, followed_id={self.followed_id})>"

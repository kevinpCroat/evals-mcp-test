"""
Database operations using SQLAlchemy 2.0 select() and execute patterns.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session
from models import User, Post


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all_users(self):
        """Get all users using select() and scalars()."""
        return list(self.session.scalars(select(User)))

    def get_user_by_id(self, user_id: int):
        """Get user by ID."""
        return self.session.scalars(select(User).where(User.id == user_id)).first()

    def get_user_by_username(self, username: str):
        """Get user by username."""
        return self.session.scalars(select(User).where(User.username == username)).first()

    def create_user(self, username: str, email: str, full_name: str = None):
        """Create a new user."""
        user = User(username=username, email=email, full_name=full_name)
        self.session.add(user)
        self.session.commit()
        return user

    def update_user_email(self, user_id: int, new_email: str):
        """Update user email."""
        user = self.session.scalars(select(User).where(User.id == user_id)).first()
        if user:
            user.email = new_email
            self.session.commit()
        return user

    def delete_user(self, user_id: int):
        """Delete user."""
        user = self.session.scalars(select(User).where(User.id == user_id)).first()
        if user:
            self.session.delete(user)
            self.session.commit()
            return True
        return False

    def search_users(self, search_term: str):
        """Search users by username or email."""
        stmt = select(User).where(
            (User.username.like(f'%{search_term}%')) |
            (User.email.like(f'%{search_term}%'))
        )
        return list(self.session.scalars(stmt))


class PostRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all_posts(self):
        """Get all posts using select()."""
        return list(self.session.scalars(select(Post)))

    def get_post_by_id(self, post_id: int):
        """Get post by ID."""
        return self.session.scalars(select(Post).where(Post.id == post_id)).first()

    def get_posts_by_user(self, user_id: int):
        """Get all posts by a specific user."""
        return list(self.session.scalars(select(Post).where(Post.author_id == user_id)))

    def create_post(self, title: str, content: str, author_id: int):
        """Create a new post."""
        post = Post(title=title, content=content, author_id=author_id)
        self.session.add(post)
        self.session.commit()
        return post

    def update_post(self, post_id: int, title: str = None, content: str = None):
        """Update post."""
        post = self.session.scalars(select(Post).where(Post.id == post_id)).first()
        if post:
            if title:
                post.title = title
            if content:
                post.content = content
            self.session.commit()
        return post

    def delete_post(self, post_id: int):
        """Delete post."""
        post = self.session.scalars(select(Post).where(Post.id == post_id)).first()
        if post:
            self.session.delete(post)
            self.session.commit()
            return True
        return False

    def get_posts_with_authors(self):
        """Get posts with joined author data."""
        return list(self.session.scalars(select(Post).join(User)))

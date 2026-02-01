"""Initial blog schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00

"""
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('bio', sa.String(500), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)

    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('slug', sa.String(50), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['parent_id'], ['categories.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('slug'),
    )
    op.create_index('ix_categories_slug', 'categories', ['slug'], unique=True)

    op.create_table(
        'articles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('excerpt', sa.String(500), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('view_count', sa.Integer(), nullable=True),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('slug'),
    )
    op.create_index('ix_articles_author_id', 'articles', ['author_id'])
    op.create_index('ix_articles_category_id', 'articles', ['category_id'])
    op.create_index('ix_articles_slug', 'articles', ['slug'], unique=True)
    op.create_index('ix_articles_author_status', 'articles', ['author_id', 'status'])
    op.create_index('ix_articles_category_status', 'articles', ['category_id', 'status'])

    op.create_table(
        'tags',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(30), nullable=False),
        sa.Column('usage_count', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_index('ix_tags_name', 'tags', ['name'], unique=True)

    op.create_table(
        'comments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('content', sa.String(2000), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('edited_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['comments.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_comments_article_id', 'comments', ['article_id'])
    op.create_index('ix_comments_user_id', 'comments', ['user_id'])
    op.create_index('ix_comments_parent_id', 'comments', ['parent_id'])
    op.create_index('ix_comments_article_created', 'comments', ['article_id', 'created_at'])

    op.create_table(
        'article_tags',
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('article_id', 'tag_id'),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
    )

    op.create_table(
        'user_follows',
        sa.Column('follower_id', sa.Integer(), nullable=False),
        sa.Column('followed_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('follower_id', 'followed_id'),
        sa.ForeignKeyConstraint(['follower_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['followed_id'], ['users.id'], ondelete='CASCADE'),
        sa.CheckConstraint('follower_id != followed_id', name='no_self_follow'),
    )
    op.create_index('ix_user_follows_followed_id', 'user_follows', ['followed_id'])
    op.create_index('ix_user_follows_follower_id', 'user_follows', ['follower_id'])


def downgrade():
    op.drop_table('user_follows')
    op.drop_table('article_tags')
    op.drop_table('comments')
    op.drop_table('tags')
    op.drop_table('articles')
    op.drop_table('categories')
    op.drop_table('users')

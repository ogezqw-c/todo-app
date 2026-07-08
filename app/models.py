import uuid
from datetime import date, datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db


# ---------------------------------------------------------------------------
# 关联表
# ---------------------------------------------------------------------------

task_categories = db.Table(
    'task_categories',
    db.Column('task_id', db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id', ondelete='CASCADE'), primary_key=True),
)


# ---------------------------------------------------------------------------
# 用户
# ---------------------------------------------------------------------------

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    session_token = db.Column(db.String(64), nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # 关联
    tasks = db.relationship('Task', backref='user', lazy='select')
    categories = db.relationship('Category', backref='user', lazy='select')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_session_token(self):
        self.session_token = uuid.uuid4().hex
        return self.session_token

    def __repr__(self):
        return f'<User {self.id}: {self.username}>'


# ---------------------------------------------------------------------------
# 任务
# ---------------------------------------------------------------------------

class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    priority = db.Column(db.String(10), nullable=False, default='medium')
    due_date = db.Column(db.Date, nullable=True)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    categories = db.relationship(
        'Category',
        secondary=task_categories,
        backref=db.backref('tasks', lazy='select'),
        lazy='select',
    )

    @property
    def is_overdue(self):
        if self.due_date is None or self.completed:
            return False
        return self.due_date < date.today()

    @property
    def priority_badge_class(self):
        return {
            'high': 'bg-danger',
            'medium': 'bg-warning text-dark',
            'low': 'bg-success',
        }.get(self.priority, 'bg-secondary')

    def __repr__(self):
        return f'<Task {self.id}: {self.title}>'


# ---------------------------------------------------------------------------
# 分类
# ---------------------------------------------------------------------------

class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(7), nullable=False, default='#6c757d')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    @property
    def task_count(self):
        return len(self.tasks)

    def __repr__(self):
        return f'<Category {self.id}: {self.name}>'

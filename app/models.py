from datetime import date, datetime
from app import db


task_categories = db.Table(
    'task_categories',
    db.Column('task_id', db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id', ondelete='CASCADE'), primary_key=True),
)


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


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    color = db.Column(db.String(7), nullable=False, default='#6c757d')

    @property
    def task_count(self):
        return len(self.tasks)

    def __repr__(self):
        return f'<Category {self.id}: {self.name}>'

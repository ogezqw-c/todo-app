from datetime import datetime, date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import case

from app import db
from app.models import Category, Task


main = Blueprint('main', __name__)


# ---------------------------------------------------------------------------
# 仪表盘
# ---------------------------------------------------------------------------

@main.route('/')
def index():
    tasks = Task.query.all()
    from app.stats import completion_rate, overdue_count, recent_tasks, tasks_by_category, tasks_by_priority
    return render_template(
        'index.html',
        total=len(tasks),
        completed=sum(1 for t in tasks if t.completed),
        overdue=overdue_count(tasks),
        completion_rate=completion_rate(tasks),
        by_priority=tasks_by_priority(tasks),
        by_category=tasks_by_category(tasks),
        recent=recent_tasks(tasks),
    )


# ---------------------------------------------------------------------------
# 任务 – 页面路由
# ---------------------------------------------------------------------------

@main.route('/tasks')
def task_list():
    status = request.args.get('status', 'all')
    priority = request.args.get('priority')
    category_id = request.args.get('category', type=int)
    sort = request.args.get('sort', 'created')

    query = Task.query

    if status == 'active':
        query = query.filter_by(completed=False)
    elif status == 'completed':
        query = query.filter_by(completed=True)

    if priority:
        query = query.filter_by(priority=priority)

    if category_id:
        query = query.join(Task.categories).filter(Category.id == category_id)

    if sort == 'due_date':
        query = query.order_by(Task.due_date.asc().nullsfirst())
    elif sort == 'priority':
        priority_order = case(
            (Task.priority == 'high', 0),
            (Task.priority == 'medium', 1),
            (Task.priority == 'low', 2),
        )
        query = query.order_by(priority_order)
    else:
        query = query.order_by(Task.created_at.desc())

    tasks = query.all()
    categories = Category.query.order_by(Category.name).all()

    return render_template(
        'tasks/list.html',
        tasks=tasks,
        categories=categories,
        current_filters={'status': status, 'priority': priority, 'category': category_id, 'sort': sort},
    )


@main.route('/tasks/new')
def task_new():
    categories = Category.query.order_by(Category.name).all()
    return render_template('tasks/form.html', task=None, categories=categories)


@main.route('/tasks/<int:id>')
def task_detail(id):
    task = Task.query.get_or_404(id)
    return render_template('tasks/detail.html', task=task)


@main.route('/tasks/<int:id>/edit')
def task_edit(id):
    task = Task.query.get_or_404(id)
    categories = Category.query.order_by(Category.name).all()
    selected_category_ids = [c.id for c in task.categories]
    return render_template(
        'tasks/form.html',
        task=task,
        categories=categories,
        selected_category_ids=selected_category_ids,
    )


# ---------------------------------------------------------------------------
# 任务 – 操作路由
# ---------------------------------------------------------------------------

@main.route('/tasks', methods=['POST'])
def task_create():
    title = request.form.get('title', '').strip()
    if not title:
        flash('任务标题不能为空。', 'danger')
        return redirect(url_for('main.task_new'))

    description = request.form.get('description', '').strip() or None
    priority = request.form.get('priority', 'medium')
    due_date_str = request.form.get('due_date', '').strip()

    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('日期格式无效。', 'danger')
            return redirect(url_for('main.task_new'))

    task = Task(
        title=title,
        description=description,
        priority=priority,
        due_date=due_date,
    )

    # 处理分类关联
    selected_ids = request.form.getlist('categories', type=int)
    if selected_ids:
        task.categories = Category.query.filter(Category.id.in_(selected_ids)).all()

    db.session.add(task)
    db.session.commit()
    flash('任务已创建！', 'success')
    return redirect(url_for('main.task_list'))


@main.route('/tasks/<int:id>/update', methods=['POST'])
def task_update(id):
    task = Task.query.get_or_404(id)
    title = request.form.get('title', '').strip()
    if not title:
        flash('任务标题不能为空。', 'danger')
        return redirect(url_for('main.task_edit', id=id))

    task.title = title
    task.description = request.form.get('description', '').strip() or None
    task.priority = request.form.get('priority', 'medium')

    due_date_str = request.form.get('due_date', '').strip()
    if due_date_str:
        try:
            task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('日期格式无效。', 'danger')
            return redirect(url_for('main.task_edit', id=id))
    else:
        task.due_date = None

    # 处理分类关联
    selected_ids = request.form.getlist('categories', type=int)
    task.categories = Category.query.filter(Category.id.in_(selected_ids)).all()

    db.session.commit()
    flash('任务已更新！', 'success')
    return redirect(url_for('main.task_list'))


@main.route('/tasks/<int:id>/delete', methods=['POST'])
def task_delete(id):
    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()
    flash('任务已删除。', 'info')
    return redirect(url_for('main.task_list'))


@main.route('/tasks/<int:id>/toggle', methods=['POST'])
def task_toggle(id):
    task = Task.query.get_or_404(id)
    task.completed = not task.completed
    task.completed_at = datetime.utcnow() if task.completed else None
    db.session.commit()
    status_text = '已完成' if task.completed else '未完成'
    flash(f'任务已标记为「{status_text}」。', 'success')
    return redirect(request.referrer or url_for('main.task_list'))


# ---------------------------------------------------------------------------
# 分类 – 页面路由
# ---------------------------------------------------------------------------

@main.route('/categories')
def category_list():
    categories = Category.query.order_by(Category.name).all()
    return render_template('categories/list.html', categories=categories)


@main.route('/categories/new')
def category_new():
    return render_template('categories/form.html', category=None)


@main.route('/categories/<int:id>/edit')
def category_edit(id):
    category = Category.query.get_or_404(id)
    return render_template('categories/form.html', category=category)


# ---------------------------------------------------------------------------
# 分类 – 操作路由
# ---------------------------------------------------------------------------

@main.route('/categories', methods=['POST'])
def category_create():
    name = request.form.get('name', '').strip()
    if not name:
        flash('分类名称不能为空。', 'danger')
        return redirect(url_for('main.category_new'))

    if Category.query.filter_by(name=name).first():
        flash('该分类名称已存在。', 'danger')
        return redirect(url_for('main.category_new'))

    color = request.form.get('color', '#6c757d').strip()
    category = Category(name=name, color=color)
    db.session.add(category)
    db.session.commit()
    flash('分类已创建！', 'success')
    return redirect(url_for('main.category_list'))


@main.route('/categories/<int:id>/update', methods=['POST'])
def category_update(id):
    category = Category.query.get_or_404(id)
    name = request.form.get('name', '').strip()
    if not name:
        flash('分类名称不能为空。', 'danger')
        return redirect(url_for('main.category_edit', id=id))

    existing = Category.query.filter_by(name=name).first()
    if existing and existing.id != id:
        flash('该分类名称已存在。', 'danger')
        return redirect(url_for('main.category_edit', id=id))

    category.name = name
    category.color = request.form.get('color', '#6c757d').strip()
    db.session.commit()
    flash('分类已更新！', 'success')
    return redirect(url_for('main.category_list'))


@main.route('/categories/<int:id>/delete', methods=['POST'])
def category_delete(id):
    category = Category.query.get_or_404(id)
    if category.task_count > 0:
        flash(f'分类「{category.name}」下有 {category.task_count} 个任务，无法删除。', 'warning')
    else:
        db.session.delete(category)
        db.session.commit()
        flash('分类已删除。', 'info')
    return redirect(url_for('main.category_list'))


# ---------------------------------------------------------------------------
# 变更日志
# ---------------------------------------------------------------------------

@main.route('/changelog')
def changelog():
    """查看所有开发变更记录。"""
    from app.audit import get_all, get_requirements
    entries = get_all()
    requirements = get_requirements()
    return render_template('changelog.html', entries=entries, requirements=requirements)


@main.route('/changelog', methods=['POST'])
def changelog_add():
    """添加一条变更记录。"""
    from app.audit import add_entry
    entry_type = request.form.get('type', '代码变更')
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    files_str = request.form.get('files', '').strip()
    relates_to_str = request.form.get('relates_to', '').strip()

    if not title or not description:
        flash('标题和描述不能为空。', 'danger')
        return redirect(url_for('main.changelog'))

    files = [f.strip() for f in files_str.split('\n') if f.strip()] if files_str else []
    relates_to = int(relates_to_str) if relates_to_str else None

    add_entry(entry_type, title, description, files, relates_to)
    flash('变更记录已添加！', 'success')
    return redirect(url_for('main.changelog'))


@main.route('/changelog/<int:id>/delete', methods=['POST'])
def changelog_delete(id):
    """删除一条变更记录。"""
    from app.audit import delete_entry
    if delete_entry(id):
        flash('记录已删除。', 'info')
    else:
        flash('记录不存在。', 'warning')
    return redirect(url_for('main.changelog'))

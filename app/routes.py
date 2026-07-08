from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import case

from app import db
from app.models import Category, Task, User

main = Blueprint('main', __name__)


# ===========================================================================
# 认证路由（公开）
# ===========================================================================

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            if not user.is_active:
                flash('该账户已被禁用。', 'danger')
                return render_template('auth/login.html')

            token = user.generate_session_token()
            db.session.commit()
            session['_session_token'] = token

            login_user(user, remember=request.form.get('remember') == 'on')
            user.last_login = datetime.utcnow()
            db.session.commit()

            flash(f'欢迎回来，{user.username}！', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        else:
            flash('用户名或密码错误。', 'danger')

    return render_template('auth/login.html')


@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        password2 = request.form.get('password2', '')

        errors = []
        if not username or len(username) < 2:
            errors.append('用户名至少 2 个字符。')
        if not email or '@' not in email:
            errors.append('请输入有效的邮箱地址。')
        if len(password) < 6:
            errors.append('密码至少 6 个字符。')
        if password != password2:
            errors.append('两次输入的密码不一致。')
        if User.query.filter_by(username=username).first():
            errors.append('该用户名已被注册。')
        if User.query.filter_by(email=email).first():
            errors.append('该邮箱已被注册。')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('auth/register.html')

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('注册成功！请登录。', 'success')
        return redirect(url_for('main.login'))

    return render_template('auth/register.html')


@main.route('/logout')
@login_required
def logout():
    if current_user.session_token:
        current_user.session_token = None
        db.session.commit()
    logout_user()
    flash('已退出登录。', 'info')
    return redirect(url_for('main.login'))


# ===========================================================================
# 仪表盘
# ===========================================================================

@main.route('/')
@login_required
def index():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
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


# ===========================================================================
# 任务 – 页面路由
# ===========================================================================

@main.route('/tasks')
@login_required
def task_list():
    status = request.args.get('status', 'all')
    priority = request.args.get('priority')
    category_id = request.args.get('category', type=int)
    sort = request.args.get('sort', 'created')

    query = Task.query.filter_by(user_id=current_user.id)

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
    categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name).all()

    return render_template(
        'tasks/list.html',
        tasks=tasks,
        categories=categories,
        current_filters={'status': status, 'priority': priority, 'category': category_id, 'sort': sort},
    )


@main.route('/tasks/new')
@login_required
def task_new():
    categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name).all()
    return render_template('tasks/form.html', task=None, categories=categories)


@main.route('/tasks/<int:id>')
@login_required
def task_detail(id):
    task = Task.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    return render_template('tasks/detail.html', task=task)


@main.route('/tasks/<int:id>/edit')
@login_required
def task_edit(id):
    task = Task.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name).all()
    selected_category_ids = [c.id for c in task.categories]
    return render_template(
        'tasks/form.html',
        task=task,
        categories=categories,
        selected_category_ids=selected_category_ids,
    )


# ===========================================================================
# 任务 – 操作路由
# ===========================================================================

@main.route('/tasks', methods=['POST'])
@login_required
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
        user_id=current_user.id,
    )

    selected_ids = request.form.getlist('categories', type=int)
    if selected_ids:
        task.categories = Category.query.filter(
            Category.id.in_(selected_ids), Category.user_id == current_user.id
        ).all()

    db.session.add(task)
    db.session.commit()
    flash('任务已创建！', 'success')
    return redirect(url_for('main.task_list'))


@main.route('/tasks/<int:id>/update', methods=['POST'])
@login_required
def task_update(id):
    task = Task.query.filter_by(id=id, user_id=current_user.id).first_or_404()
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

    selected_ids = request.form.getlist('categories', type=int)
    task.categories = Category.query.filter(
        Category.id.in_(selected_ids), Category.user_id == current_user.id
    ).all()

    db.session.commit()
    flash('任务已更新！', 'success')
    return redirect(url_for('main.task_list'))


@main.route('/tasks/<int:id>/delete', methods=['POST'])
@login_required
def task_delete(id):
    task = Task.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(task)
    db.session.commit()
    flash('任务已删除。', 'info')
    return redirect(url_for('main.task_list'))


@main.route('/tasks/<int:id>/toggle', methods=['POST'])
@login_required
def task_toggle(id):
    task = Task.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    task.completed = not task.completed
    task.completed_at = datetime.utcnow() if task.completed else None
    db.session.commit()
    status_text = '已完成' if task.completed else '未完成'
    flash(f'任务已标记为「{status_text}」。', 'success')
    return redirect(request.referrer or url_for('main.task_list'))


# ===========================================================================
# 分类 – 页面路由
# ===========================================================================

@main.route('/categories')
@login_required
def category_list():
    categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name).all()
    return render_template('categories/list.html', categories=categories)


@main.route('/categories/new')
@login_required
def category_new():
    return render_template('categories/form.html', category=None)


@main.route('/categories/<int:id>/edit')
@login_required
def category_edit(id):
    category = Category.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    return render_template('categories/form.html', category=category)


# ===========================================================================
# 分类 – 操作路由
# ===========================================================================

@main.route('/categories', methods=['POST'])
@login_required
def category_create():
    name = request.form.get('name', '').strip()
    if not name:
        flash('分类名称不能为空。', 'danger')
        return redirect(url_for('main.category_new'))

    if Category.query.filter_by(name=name, user_id=current_user.id).first():
        flash('该分类名称已存在。', 'danger')
        return redirect(url_for('main.category_new'))

    color = request.form.get('color', '#6c757d').strip()
    category = Category(name=name, color=color, user_id=current_user.id)
    db.session.add(category)
    db.session.commit()
    flash('分类已创建！', 'success')
    return redirect(url_for('main.category_list'))


@main.route('/categories/<int:id>/update', methods=['POST'])
@login_required
def category_update(id):
    category = Category.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    name = request.form.get('name', '').strip()
    if not name:
        flash('分类名称不能为空。', 'danger')
        return redirect(url_for('main.category_edit', id=id))

    existing = Category.query.filter_by(name=name, user_id=current_user.id).first()
    if existing and existing.id != id:
        flash('该分类名称已存在。', 'danger')
        return redirect(url_for('main.category_edit', id=id))

    category.name = name
    category.color = request.form.get('color', '#6c757d').strip()
    db.session.commit()
    flash('分类已更新！', 'success')
    return redirect(url_for('main.category_list'))


@main.route('/categories/<int:id>/delete', methods=['POST'])
@login_required
def category_delete(id):
    category = Category.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    if category.task_count > 0:
        flash(f'分类「{category.name}」下有 {category.task_count} 个任务，无法删除。', 'warning')
    else:
        db.session.delete(category)
        db.session.commit()
        flash('分类已删除。', 'info')
    return redirect(url_for('main.category_list'))


# ===========================================================================
# 架构文档（开发者工具，无登录要求）
# ===========================================================================

@main.route('/architecture')
def architecture():
    return render_template('architecture.html')


# ===========================================================================
# 通知中心
# ===========================================================================

@main.route('/notifications')
@login_required
def notification_list():
    from app.notifications import Notification
    notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc()).all()
    return render_template('notifications.html', notifications=notifications)


@main.route('/notifications/read-all', methods=['POST'])
@login_required
def notification_read_all():
    from app.notifications import Notification
    Notification.query.filter_by(is_read=False, user_id=current_user.id)\
        .update({'is_read': True})
    db.session.commit()
    flash('所有通知已标记为已读。', 'success')
    return redirect(url_for('main.notification_list'))


@main.route('/notifications/<int:id>/read', methods=['POST'])
@login_required
def notification_read(id):
    from app.notifications import Notification
    notif = Notification.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    notif.is_read = True
    db.session.commit()
    return redirect(request.referrer or url_for('main.notification_list'))


# ===========================================================================
# 变更日志（开发者工具，无登录要求）
# ===========================================================================

@main.route('/changelog')
def changelog():
    from app.audit import get_all, get_requirements
    entries = get_all()
    requirements = get_requirements()
    return render_template('changelog.html', entries=entries, requirements=requirements)


@main.route('/changelog', methods=['POST'])
def changelog_add():
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
    from app.audit import delete_entry
    if delete_entry(id):
        flash('记录已删除。', 'info')
    else:
        flash('记录不存在。', 'warning')
    return redirect(url_for('main.changelog'))

import os
from flask import Flask, redirect, session, url_for
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app():
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'),
    )
    app.config.from_object('config.Config')

    # 确保 instance 目录存在
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message = '请先登录后再访问该页面。'
    login_manager.login_message_category = 'warning'

    # Flask-Login 用户加载器
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    # 注册自定义 Jinja 过滤器
    from app.utils import format_date, priority_badge_class, is_overdue
    from app.audit import get_by_id as audit_get_by_id
    app.add_template_filter(format_date)
    app.add_template_filter(priority_badge_class)
    app.add_template_filter(is_overdue)
    app.add_template_global(audit_get_by_id, 'get_related')

    # 注册蓝图
    from app.routes import main
    app.register_blueprint(main)

    # 全局上下文：通知未读数（仅当前用户）
    @app.context_processor
    def inject_notification_count():
        if current_user.is_authenticated:
            from app.notifications import Notification
            count = Notification.query.filter_by(
                is_read=False, user_id=current_user.id
            ).count()
        else:
            count = 0
        return {'notification_count': count}

    # 启动定期逾期检查（APScheduler，避免 debug 双进程）
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        from apscheduler.schedulers.background import BackgroundScheduler
        from app.notifications import check_and_notify
        scheduler = BackgroundScheduler()
        check_interval = app.config.get('NOTIFY_CHECK_MINUTES', 10)
        scheduler.add_job(
            lambda: check_and_notify(),
            'interval',
            minutes=check_interval,
            id='overdue_check',
        )
        scheduler.start()

    return app

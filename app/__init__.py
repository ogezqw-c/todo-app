import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


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

    # 首次运行时创建数据库表
    with app.app_context():
        db.create_all()

    return app

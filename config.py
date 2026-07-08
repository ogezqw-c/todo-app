import os


# ⚠️ 必须在 Config 类之前加载 .env，因为类属性在定义时求值
def _load_env():
    basedir = os.path.abspath(os.path.dirname(__file__))
    env_path = os.path.join(basedir, '.env')
    if not os.path.exists(env_path):
        return
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            key, value = key.strip(), value.strip().strip('"').strip("'")
            if key not in os.environ:
                os.environ[key] = value


_load_env()


class Config:
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')

    # 数据库
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'todo.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # QQ 邮箱 SMTP 配置
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.qq.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 465))
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', '')

    # 通知邮件接收地址
    NOTIFY_EMAIL = os.environ.get('NOTIFY_EMAIL', '')

    # APScheduler 检查间隔（分钟）
    NOTIFY_CHECK_MINUTES = int(os.environ.get('NOTIFY_CHECK_MINUTES', 10))

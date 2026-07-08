"""任务逾期通知 —— 模型、邮件发送、定期检查。"""
import smtplib
from datetime import date, datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from flask import current_app

from app import db


# ---------------------------------------------------------------------------
# 模型
# ---------------------------------------------------------------------------

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(500), nullable=False)
    type = db.Column(db.String(20), nullable=False, default='overdue')
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id', ondelete='SET NULL'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    task = db.relationship('Task', backref=db.backref('notifications', lazy='select'))

    def __repr__(self):
        return f'<Notification {self.id}: {self.type}>'


# ---------------------------------------------------------------------------
# 邮件发送
# ---------------------------------------------------------------------------

def send_email(to_email, subject, html_body):
    """通过 QQ SMTP 发送 HTML 邮件。
    配置项来自 Flask config：
      MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER
    """
    sender = current_app.config.get('MAIL_DEFAULT_SENDER', current_app.config['MAIL_USERNAME'])
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to_email
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    port = current_app.config['MAIL_PORT']
    server = None
    try:
        if port == 587:
            server = smtplib.SMTP(current_app.config['MAIL_SERVER'], port, timeout=15)
            server.ehlo()
            server.starttls()
            server.ehlo()
        else:
            server = smtplib.SMTP_SSL(current_app.config['MAIL_SERVER'], port, timeout=15)
        server.login(current_app.config['MAIL_USERNAME'], current_app.config['MAIL_PASSWORD'])
        server.sendmail(sender, [to_email], msg.as_string())
        server.quit()
        return True, None
    except Exception as e:
        if server:
            try:
                server.quit()
            except Exception:
                pass
        return False, str(e)


def build_overdue_email(tasks):
    """生成逾期任务邮件 HTML。"""
    rows = ''
    for task in tasks:
        overdue_days = (date.today() - task.due_date).days
        rows += f'''
        <tr>
            <td style="padding:10px;border-bottom:1px solid #333;">{task.title}</td>
            <td style="padding:10px;border-bottom:1px solid #333;color:#7C5CFC;">{task.priority}</td>
            <td style="padding:10px;border-bottom:1px solid #333;">{task.due_date.strftime('%Y年%m月%d日')}</td>
            <td style="padding:10px;border-bottom:1px solid #333;color:#FF5252;font-weight:bold;">逾期 {overdue_days} 天</td>
        </tr>'''

    return f'''
    <div style="max-width:600px;margin:0 auto;font-family:sans-serif;">
        <h2 style="color:#7C5CFC;">📋 TaskFlow 逾期提醒</h2>
        <p>以下任务已超过截止日期，请及时处理：</p>
        <table style="width:100%;border-collapse:collapse;background:#1a1a2e;color:#EAEAF0;">
            <thead>
                <tr style="background:#0f0f1a;">
                    <th style="padding:10px;text-align:left;">任务</th>
                    <th style="padding:10px;text-align:left;">优先级</th>
                    <th style="padding:10px;text-align:left;">截止日期</th>
                    <th style="padding:10px;text-align:left;">状态</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
        <p style="margin-top:20px;color:#8888A0;font-size:12px;">
            此邮件由 TaskFlow 自动发送。共 {len(tasks)} 个逾期任务。
        </p>
    </div>'''


# ---------------------------------------------------------------------------
# 定期检查（供 APScheduler 调用）
# ---------------------------------------------------------------------------

def check_and_notify():
    """检查逾期任务，生成通知并发送邮件。"""
    from app.models import Task

    app = current_app._get_current_object()
    with app.app_context():
        overdue_tasks = Task.query.filter(
            Task.completed == False,
            Task.due_date != None,
            Task.due_date < date.today(),
        ).all()

        if not overdue_tasks:
            return

        # 已通知过的逾期任务 ID（避免重复通知）
        already_notified = set(
            row[0] for row in db.session.query(Notification.task_id)
            .filter(
                Notification.type == 'overdue',
                Notification.task_id.in_([t.id for t in overdue_tasks]),
            ).all()
        )

        new_overdue = [t for t in overdue_tasks if t.id not in already_notified]

        for task in new_overdue:
            overdue_days = (date.today() - task.due_date).days
            msg = f'「{task.title}」已逾期 {overdue_days} 天'
            notif = Notification(message=msg, type='overdue', task_id=task.id)
            db.session.add(notif)

        if new_overdue:
            db.session.commit()

            # 发送邮件
            recipient = app.config.get('NOTIFY_EMAIL')
            if recipient:
                success, error = send_email(
                    recipient,
                    f'[TaskFlow] {len(new_overdue)} 个任务已逾期',
                    build_overdue_email(new_overdue),
                )
                if not success:
                    app.logger.warning(f'邮件发送失败: {error}')

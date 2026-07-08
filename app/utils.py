from datetime import date, datetime


def format_date(value, fmt='%Y年%m月%d日'):
    """格式化日期对象用于显示。若为 None 则返回 '—'。"""
    if value is None:
        return '—'
    if isinstance(value, datetime):
        value = value.date()
    return value.strftime(fmt)


def priority_badge_class(priority):
    """返回对应优先级的 Bootstrap 5 徽章样式类。"""
    return {
        'high': 'bg-danger',
        'medium': 'bg-warning text-dark',
        'low': 'bg-success',
    }.get(priority, 'bg-secondary')


def is_overdue(task):
    """检查任务是否逾期；可在模板中使用 `task|is_overdue` 过滤器。"""
    if task.due_date is None or task.completed:
        return False
    return task.due_date < date.today()

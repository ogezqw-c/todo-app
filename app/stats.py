from collections import Counter


def completion_rate(tasks):
    """返回 0 到 100 之间的完成率。"""
    total = len(tasks)
    if total == 0:
        return 0.0
    completed = sum(1 for t in tasks if t.completed)
    return round((completed / total) * 100, 1)


def overdue_count(tasks):
    """返回逾期任务数量（未完成且已过截止日期）。"""
    return sum(1 for t in tasks if t.is_overdue)


def tasks_by_priority(tasks):
    """返回 {优先级: 数量} 字典。"""
    counts = {'high': 0, 'medium': 0, 'low': 0}
    for t in tasks:
        if t.priority in counts:
            counts[t.priority] += 1
    return counts


def tasks_by_category(tasks):
    """返回按数量降序排列的 (分类名称, 数量, 颜色) 列表。"""
    cat_counter = Counter()
    cat_colors = {}
    for t in tasks:
        for cat in t.categories:
            cat_counter[cat.name] += 1
            cat_colors[cat.name] = cat.color
    return [(name, count, cat_colors[name]) for name, count in cat_counter.most_common()]


def recent_tasks(tasks, limit=5):
    """返回最近创建的任务。"""
    return sorted(tasks, key=lambda t: t.created_at, reverse=True)[:limit]

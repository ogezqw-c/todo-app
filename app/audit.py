"""开发审计日志 — 读写 changelog.json"""
import json
import os
from datetime import datetime

CHANGELOG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'changelog.json')


def _load():
    """加载全部条目，按 id 升序返回。"""
    if not os.path.exists(CHANGELOG_PATH):
        return []
    with open(CHANGELOG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save(entries):
    """保存条目列表到文件。"""
    os.makedirs(os.path.dirname(CHANGELOG_PATH), exist_ok=True)
    with open(CHANGELOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def get_all():
    """返回所有条目，按时间倒序。"""
    entries = _load()
    entries.sort(key=lambda e: e.get('timestamp', ''), reverse=True)
    return entries


def get_requirements():
    """仅返回需求变更条目，供表单下拉选择关联。"""
    return [e for e in _load() if e.get('type') == '需求变更']


def get_by_id(entry_id):
    """按 id 获取单条记录。"""
    for e in _load():
        if e.get('id') == entry_id:
            return e
    return None


def add_entry(entry_type, title, description, files=None, relates_to=None):
    """添加一条变更记录，返回新条目。"""
    entries = _load()
    new_id = max((e.get('id', 0) for e in entries), default=0) + 1

    new_entry = {
        'id': new_id,
        'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S'),
        'type': entry_type,
        'title': title.strip(),
        'description': description.strip(),
        'files': files or [],
        'relates_to': relates_to,
    }
    entries.append(new_entry)
    _save(entries)
    return new_entry


def delete_entry(entry_id):
    """删除指定条目，返回是否成功。"""
    entries = _load()
    filtered = [e for e in entries if e.get('id') != entry_id]
    if len(filtered) == len(entries):
        return False
    _save(filtered)
    return True


def get_related_entries(entry_id):
    """获取关联到指定需求的所有代码变更条目。"""
    return [e for e in _load() if e.get('relates_to') == entry_id]

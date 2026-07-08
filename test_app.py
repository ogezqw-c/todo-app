"""Todo App 冒烟测试（多用户版）。"""
import os
from app import create_app

# 确保测试数据库存在
os.makedirs('instance', exist_ok=True)
if os.path.exists('instance/todo.db'):
    os.remove('instance/todo.db')

# 应用迁移
from flask_migrate import upgrade as migrate_upgrade
app = create_app()
with app.app_context():
    migrate_upgrade(directory='migrations')

with app.test_client() as client:
    # 1. 注册
    r = client.post('/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': '123456',
        'password2': '123456',
    }, follow_redirects=True)
    assert r.status_code == 200
    assert '登录' in r.data.decode('utf-8')
    print('POST /register => 200 OK (已重定向到登录)')

    # 2. 登录
    r = client.post('/login', data={
        'username': 'testuser',
        'password': '123456',
    }, follow_redirects=True)
    assert r.status_code == 200
    assert '仪表盘' in r.data.decode('utf-8')
    print('POST /login => 200 OK (已登录)')

    # 3. 仪表盘
    r = client.get('/')
    assert r.status_code == 200
    print('GET / => 200 OK')

    # 4. 任务页面
    r = client.get('/tasks')
    assert r.status_code == 200, f'GET /tasks => {r.status_code}'
    print('GET /tasks => 200 OK')

    r = client.get('/tasks/new')
    assert r.status_code == 200
    print('GET /tasks/new => 200 OK')

    # 5. 分类页面
    r = client.get('/categories')
    assert r.status_code == 200
    print('GET /categories => 200 OK')

    r = client.get('/categories/new')
    assert r.status_code == 200
    print('GET /categories/new => 200 OK')

    # 6. 创建分类（用户隔离版）
    r = client.post('/categories', data={'name': '工作', 'color': '#0d6efd'}, follow_redirects=True)
    assert r.status_code == 200
    print('POST /categories (工作) => 200 OK')

    # 7. 创建任务（用户隔离版）
    r = client.post('/tasks', data={
        'title': '测试任务',
        'priority': 'high',
        'due_date': '2026-07-10',
    }, follow_redirects=True)
    assert r.status_code == 200
    print('POST /tasks => 200 OK')

    # 8. 任务详情
    r = client.get('/tasks/1')
    assert r.status_code == 200
    print('GET /tasks/1 => 200 OK')

    # 9. toggle
    r = client.post('/tasks/1/toggle', follow_redirects=True)
    assert r.status_code == 200
    print('POST /tasks/1/toggle => 200 OK')

    # 10. 编辑页面
    r = client.get('/tasks/1/edit')
    assert r.status_code == 200
    print('GET /tasks/1/edit => 200 OK')

    r = client.get('/categories/1/edit')
    assert r.status_code == 200
    print('GET /categories/1/edit => 200 OK')

    # 11. 删除
    r = client.post('/tasks/1/delete', follow_redirects=True)
    assert r.status_code == 200
    print('POST /tasks/1/delete => 200 OK')

    # 12. 登出
    r = client.get('/logout', follow_redirects=True)
    assert r.status_code == 200
    assert '登录' in r.data.decode('utf-8')
    print('GET /logout => 200 OK (已登出)')

    # 13. 验证未登录保护（应该重定向到登录页）
    r = client.get('/tasks', follow_redirects=True)
    assert r.status_code == 200
    assert '登录' in r.data.decode('utf-8')
    print('GET /tasks (未登录) => 200 OK (跳转登录)')

    print('\n=== 所有冒烟测试通过！ ===')

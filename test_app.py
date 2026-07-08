"""Todo App 冒烟测试。"""
from app import create_app

app = create_app()

with app.test_client() as client:
    # 仪表盘
    r = client.get('/')
    assert r.status_code == 200, f'GET / => {r.status_code}'
    print('GET / => 200 OK')

    # 任务页面
    r = client.get('/tasks')
    assert r.status_code == 200, f'GET /tasks => {r.status_code}'
    print('GET /tasks => 200 OK')

    r = client.get('/tasks/new')
    assert r.status_code == 200, f'GET /tasks/new => {r.status_code}'
    print('GET /tasks/new => 200 OK')

    # 分类页面
    r = client.get('/categories')
    assert r.status_code == 200, f'GET /categories => {r.status_code}'
    print('GET /categories => 200 OK')

    r = client.get('/categories/new')
    assert r.status_code == 200, f'GET /categories/new => {r.status_code}'
    print('GET /categories/new => 200 OK')

    # 创建分类
    r = client.post('/categories', data={'name': '工作', 'color': '#0d6efd'}, follow_redirects=True)
    assert r.status_code == 200, f'POST /categories => {r.status_code}'
    print('POST /categories (工作) => 200 OK')

    # 创建任务
    r = client.post('/tasks', data={
        'title': '测试任务',
        'priority': 'high',
        'due_date': '2026-07-10',
    }, follow_redirects=True)
    assert r.status_code == 200, f'POST /tasks => {r.status_code}'
    print('POST /tasks => 200 OK')

    # 任务详情
    r = client.get('/tasks/1')
    assert r.status_code == 200, f'GET /tasks/1 => {r.status_code}'
    print('GET /tasks/1 => 200 OK')

    # 切换完成状态
    r = client.post('/tasks/1/toggle', follow_redirects=True)
    assert r.status_code == 200, f'POST /tasks/1/toggle => {r.status_code}'
    print('POST /tasks/1/toggle => 200 OK')

    # 编辑页面
    r = client.get('/tasks/1/edit')
    assert r.status_code == 200, f'GET /tasks/1/edit => {r.status_code}'
    print('GET /tasks/1/edit => 200 OK')

    r = client.get('/categories/1/edit')
    assert r.status_code == 200, f'GET /categories/1/edit => {r.status_code}'
    print('GET /categories/1/edit => 200 OK')

    # 删除任务
    r = client.post('/tasks/1/delete', follow_redirects=True)
    assert r.status_code == 200, f'POST /tasks/1/delete => {r.status_code}'
    print('POST /tasks/1/delete => 200 OK')

    print('\n=== 所有冒烟测试通过！ ===')

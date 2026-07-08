# Todo App

一个基于 **Flask + SQLite + Bootstrap 5** 的 Web Todo 应用。

## 功能

- ✅ 任务增删改查 (CRUD)
- 🔴🟡🟢 三级优先级 (高/中/低)，颜色区分
- 📅 截止日期，逾期自动高亮
- 🏷️ 分类/标签系统（多对多），自定义颜色
- 📊 统计仪表盘（完成率、分类分布、优先级分布、最近任务）
- 🔍 任务列表过滤和排序（状态/优先级/分类/日期）

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 启动应用
python app.py

# 浏览器访问
http://127.0.0.1:5000
```

## 项目结构

```
todo-app/
├── app.py                 # 入口
├── config.py              # 配置
├── requirements.txt       # 依赖
├── app/
│   ├── __init__.py        # Flask 工厂
│   ├── models.py          # 数据模型
│   ├── routes.py          # 路由处理
│   ├── stats.py           # 统计函数
│   └── utils.py           # 模板过滤器
├── static/
│   ├── css/style.css      # 自定义样式
│   └── js/app.js          # 交互脚本
└── templates/
    ├── base.html          # 基础布局
    ├── index.html         # 仪表盘
    ├── tasks/             # 任务模板
    └── categories/        # 分类模板
```

## 技术栈

- **后端**: Flask 3.x + Flask-SQLAlchemy 3.x
- **数据库**: SQLite (自动创建于 `instance/todo.db`)
- **前端**: Bootstrap 5 (CDN) + Jinja2 模板 + Vanilla JS
- **图标**: Bootstrap Icons

## 重置数据库

删除 `instance/todo.db` 文件后重启应用即可自动重建。

## 运行测试

```bash
python test_app.py
```

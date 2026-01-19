# 企业百科知识库（FastAPI + MySQL + 前端）

## 设计架构（高层）

1. **前端交互层**：纯静态页面（HTML/CSS/JS），通过 API 获取文档清单、分类与文件预览。  
2. **后端服务层**：FastAPI 提供文档管理、上传、微信文章抓取、文件分发等 API。  
3. **存储层**：MySQL 保存元数据（标题、领域、路径、类型）；文件落盘到对象存储目录（可替换为云对象存储）。  
4. **扩展性**：新增文件/URL 通过 API 写入数据库与存储，前端自动读取最新清单。

## 代码结构

```
.
├── backend
│   ├── app
│   │   ├── __init__.py
│   │   ├── config.py        # 环境与配置
│   │   ├── crud.py          # 数据库 CRUD
│   │   ├── db.py            # 数据库连接
│   │   ├── main.py          # FastAPI 入口
│   │   ├── models.py        # SQLAlchemy 模型
│   │   ├── schemas.py       # Pydantic Schema
│   │   ├── storage.py       # 文件存储工具
│   │   └── wechat.py        # 微信文章抓取
│   ├── .env.example
│   ├── README.md
│   └── requirements.txt
└── frontend
    ├── app.js
    ├── index.html
    └── styles.css
```

## 环境配置（Windows + Anaconda）

1. **Python 环境**
   - 安装 Anaconda
   - 创建环境：`conda create -n kb python=3.11 -y`
   - 激活环境：`conda activate kb`

2. **数据库**
   - 使用 Navicat 创建数据库：`knowledge_base`
   - 连接信息填写至 `backend/.env`

3. **后端依赖**
   - `pip install -r backend/requirements.txt`

4. **前端**
   - 直接使用静态页面，使用浏览器打开 `frontend/index.html`
   - 将 API 地址指向后端（默认 `http://localhost:8000`）

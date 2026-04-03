# 基于 MongoDB 的简化版在线问卷系统（第一阶段）

- 前端：Vue3 + Vite + TailwindCSS + Pinia + Vue Router
- 后端：Django + Django REST Framework（业务数据使用 `pymongo` 直连 MongoDB）
- 数据库：MongoDB

## 目录结构

```text
Project1/
├─ backend/
│  ├─ apps/
│  │  └─ core/
│  │     ├─ authentication.py        # JWT 认证
│  │     ├─ mongodb.py               # MongoDB 连接与集合访问
│  │     ├─ serializers.py           # 请求参数与数据校验
│  │     ├─ views.py                 # API 入口
│  │     └─ services/
│  │        ├─ auth_service.py       # 注册登录业务
│  │        └─ survey_service.py     # 问卷、跳转、提交、统计核心逻辑
│  ├─ questionnaire/                 # Django 项目配置
│  ├─ tests/
│  │  └─ run_api_test_suite.py       # 自动化 API 回归脚本
│  ├─ manage.py
│  └─ requirements.txt
├─ frontend/
│  ├─ src/
│  │  ├─ api/
│  │  │  ├─ http.js                  # Axios 封装
│  │  │  ├─ auth.js                  # 认证接口
│  │  │  └─ survey.js                # 问卷相关接口
│  │  ├─ views/
│  │  │  ├─ auth/                    # 登录/注册页面
│  │  │  └─ survey/                  # 列表、编辑、填写、统计页面
│  │  ├─ router/
│  │  ├─ stores/
│  │  └─ components/
│  ├─ package.json
│  └─ vite.config.js
├─ docs/                             # 作业交付文档
│  ├─ 01-Architecture.md
│  ├─ 02-MongoDB-Design.md
│  ├─ 03-Deployment.md
│  ├─ 04-API.md
│  ├─ 05-TestCases.md
│  ├─ 06-AI-Usage-Log.md
│  └─ 项目完成报告.md
└─ README.md
```

## 快速开始

### 1) 启动 MongoDB

确保本机 MongoDB 已运行（默认 `mongodb://localhost:27017/`）。

### 2) 启动后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python manage.py runserver 0.0.0.0:8000
```

### 3) 启动前端

```powershell
cd frontend
npm install
copy .env.example .env
npm run dev
```

## 核心特性

- 用户注册/登录/JWT 鉴权
- 问卷创建、编辑、发布、关闭、删除
- 题目管理：单选/多选/填空（文本与数字校验）
- 跳转逻辑：单选、多选、数字条件跳转，规则可配置
- 问卷填写：实时校验、自动跳转、可匿名提交
- 统计分析：整卷统计 + 单题统计

## 文档索引

- 架构说明：[docs/01-Architecture.md](docs/01-Architecture.md)
- MongoDB 设计：[docs/02-MongoDB-Design.md](docs/02-MongoDB-Design.md)
- 部署文档：[docs/03-Deployment.md](docs/03-Deployment.md)
- API 文档：[docs/04-API.md](docs/04-API.md)
- 测试用例：[docs/05-TestCases.md](docs/05-TestCases.md)
- AI 使用日志模板：[docs/06-AI-Usage-Log.md](docs/06-AI-Usage-Log.md)
- 项目完成报告：[docs/项目完成报告.md](docs/项目完成报告.md)

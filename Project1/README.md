# 基于 MongoDB 的简化版在线问卷系统（第一阶段）

- 前端：Vue3 + Vite + TailwindCSS + Pinia + Vue Router
- 后端：Django + Django REST Framework（业务数据使用 `pymongo` 直连 MongoDB）
- 数据库：MongoDB

## 目录结构

```text
Project1/
  backend/                 # Django + DRF API
  frontend/                # Vue3 + Vite 前端
  docs/                    # 数据库/API/测试/部署/报告文档
  README.md
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

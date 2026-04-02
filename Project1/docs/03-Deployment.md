# 3. 运行、部署与打包说明

## 3.1 环境要求

1. Python 3.10+。
2. Node.js 18+。
3. MongoDB 6.0+。
4. Windows PowerShell（命令示例基于此环境）。

## 3.2 本地开发部署

### 3.2.1 启动 MongoDB

确保 MongoDB 服务已运行，默认地址：

mongodb://localhost:27017/

### 3.2.2 启动后端

```powershell
Set-Location Project1/backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py runserver 0.0.0.0:8000
```

后端服务地址：

http://localhost:8000

后端关键环境变量：

1. MONGODB_URI
2. MONGODB_DB_NAME
3. JWT_SECRET
4. FRONTEND_BASE_URL

### 3.2.3 启动前端

```powershell
Set-Location Project1/frontend
npm install
Copy-Item .env.example .env
npm run dev
```

前端地址：

http://localhost:5173

前端关键环境变量：

1. VITE_API_BASE_URL，默认 http://localhost:8000/api。

## 3.3 前端生产构建

```powershell
Set-Location Project1/frontend
npm run build
npm run preview
```

构建产物目录：

frontend/dist

# 3. 项目运行部署文档

## 3.1 环境要求

- Python 3.10+
- Node.js 18+
- MongoDB 6.0+
- Windows PowerShell（本文示例）

## 3.2 后端部署（Django）

### 1) 进入后端目录

```powershell
cd Project1/backend
```

### 2) 创建并激活虚拟环境

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3) 安装依赖

```powershell
pip install -r requirements.txt
```

### 4) 配置环境变量

```powershell
copy .env.example .env
```

根据实际修改 `.env`：

- `MONGODB_URI`
- `MONGODB_DB_NAME`
- `JWT_SECRET`

### 5) 启动后端

```powershell
python manage.py runserver 0.0.0.0:8000
```

后端地址：`http://localhost:8000`

## 3.3 前端部署（Vue3）

### 1) 进入前端目录

```powershell
cd Project1/frontend
```

### 2) 安装依赖

```powershell
npm install
```

### 3) 配置环境变量

```powershell
copy .env.example .env
```

默认：`VITE_API_BASE_URL=http://localhost:8000/api`

### 4) 启动开发环境

```powershell
npm run dev
```

前端地址：`http://localhost:5173`

### 5) 生产打包

```powershell
npm run build
npm run preview
```

## 3.4 联调检查

1. 打开前端 `/login` 完成注册登录。
2. 创建问卷并新增题目。
3. 配置跳转规则并发布问卷。
4. 打开填写链接完成提交。
5. 回到统计页查看数据。

## 3.5 常见问题

- MongoDB 连接失败：检查 `MONGODB_URI` 与服务是否启动。
- 跨域失败：后端已开启 `CORS_ALLOW_ALL_ORIGINS=True`。
- Token 鉴权失败：检查请求头 `Authorization: Bearer <token>`。

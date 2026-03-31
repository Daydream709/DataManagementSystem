# 后端服务（Django + DRF + MongoDB）

## 启动说明

1. 创建并激活虚拟环境
2. 安装依赖：`pip install -r requirements.txt`
3. 复制环境变量：`copy .env.example .env`
4. 启动服务：`python manage.py runserver 0.0.0.0:8000`

## 说明

- 所有业务数据使用 `pymongo` 直接写入 MongoDB。
- 未使用关系型数据库与 ORM 映射关系结构。
- API 前缀统一为 `/api/`。

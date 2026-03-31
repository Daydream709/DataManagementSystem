# 4. API 接口文档

统一前缀：`/api`

统一响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

失败时 `code=1`，`message` 为错误说明。

## 4.1 认证模块

### 注册

- `POST /api/auth/register`
- 请求体：

```json
{
  "username": "alice",
  "password": "123456"
}
```

- 返回：用户信息 + token

### 登录

- `POST /api/auth/login`
- 请求体：

```json
{
  "username": "alice",
  "password": "123456"
}
```

- 返回：用户信息 + token

## 4.2 问卷模块

### 获取我的问卷列表

- `GET /api/surveys`
- 鉴权：Bearer Token

### 创建问卷

- `POST /api/surveys`
- 请求体：

```json
{
  "title": "校园饮食习惯",
  "description": "用于课程调研",
  "allow_anonymous": true,
  "deadline": "2026-04-01T12:00:00Z"
}
```

### 获取问卷详情

- `GET /api/surveys/{survey_id}`

### 更新问卷

- `PUT /api/surveys/{survey_id}`

### 删除问卷

- `DELETE /api/surveys/{survey_id}`

### 发布问卷

- `POST /api/surveys/{survey_id}/publish`

### 关闭问卷

- `POST /api/surveys/{survey_id}/close`

### 设为草稿

- `POST /api/surveys/{survey_id}/draft`

## 4.3 题目模块

### 获取问卷题目

- `GET /api/surveys/{survey_id}/questions`

### 新增题目

- `POST /api/surveys/{survey_id}/questions`
- 单选示例：

```json
{
  "order": 1,
  "type": "single_choice",
  "title": "你的年级",
  "required": true,
  "options": [
    { "key": "A", "label": "大一" },
    { "key": "B", "label": "大二" }
  ]
}
```

- 多选示例：

```json
{
  "order": 2,
  "type": "multi_choice",
  "title": "喜欢的水果",
  "required": true,
  "options": [
    { "key": "A", "label": "苹果" },
    { "key": "B", "label": "香蕉" },
    { "key": "C", "label": "西瓜" }
  ],
  "validation": { "min_select": 1, "max_select": 2 }
}
```

- 填空数字示例：

```json
{
  "order": 3,
  "type": "fill_blank",
  "title": "你的年龄",
  "required": true,
  "validation": { "value_type": "number", "min_value": 0, "max_value": 120, "is_integer": true }
}
```

### 更新题目

- `PUT /api/questions/{question_id}`

### 删除题目

- `DELETE /api/questions/{question_id}`

## 4.4 跳转规则模块

### 查询问卷跳转规则

- `GET /api/surveys/{survey_id}/jump-rules`

### 创建跳转规则

- `POST /api/surveys/{survey_id}/jump-rules`
- 示例：

```json
{
  "question_id": "67ff...",
  "rule_type": "single_choice",
  "operator": "eq",
  "value": "A",
  "target_question_id": "67aa...",
  "priority": 1
}
```

### 删除跳转规则

- `DELETE /api/jump-rules/{rule_id}`

## 4.5 填写问卷模块

### 获取公开问卷

- `GET /api/public/surveys/{slug}`
- 鉴权：Bearer Token（填写前必须登录）
- 说明：返回问卷、题目、跳转规则

### 计算下一题（动态跳转）

- `POST /api/public/surveys/{slug}/next-question`
- 鉴权：Bearer Token（填写前必须登录）
- 请求体：

```json
{
  "current_question_id": "67ff...",
  "answer": "A"
}
```

- 返回：

```json
{
  "next_question": {
    "id": "67aa...",
    "order": 5,
    "type": "fill_blank",
    "title": "..."
  }
}
```

若无下一题：`"next_question": null`

### 提交问卷

- `POST /api/public/surveys/{slug}/submit`
- 鉴权：Bearer Token（填写前必须登录）
- 请求体：

```json
{
  "is_anonymous": false,
  "client_fingerprint": "client-01",
  "answers": [
    { "question_id": "67ff...", "answer": "A" },
    { "question_id": "67aa...", "answer": 20 }
  ]
}
```

## 4.6 统计模块

### 整卷统计

- `GET /api/surveys/{survey_id}/stats`
- 返回包含：提交总数、每题统计结果

### 单题统计

- `GET /api/questions/{question_id}/stats`
- 返回包含：
  - 单选：选项计数 + 回答人数
  - 多选：选项被选次数
  - 填空：所有文本/数字列表，数字含平均值

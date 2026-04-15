# 4. API 文档

## 4.1 统一约定

基础前缀：

/api

统一成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

统一失败响应：

```json
{
  "code": 1,
  "message": "错误说明",
  "data": null
}
```

鉴权方式：

Authorization: Bearer <token>

## 4.2 全局业务约束

1. 除注册、登录外，接口默认需要登录。
2. 填写问卷相关接口需要登录用户身份。
3. 编辑类接口仅草稿问卷可用。
4. 发布和关闭状态不能回退为草稿。

## 4.3 认证接口

### 4.3.1 注册

1. 方法与路径：POST /api/auth/register。
2. 请求体：

```json
{
  "username": "alice",
  "password": "123456"
}
```

3. 返回：用户信息与 token。

### 4.3.2 登录

1. 方法与路径：POST /api/auth/login。
2. 请求体：

```json
{
  "username": "alice",
  "password": "123456"
}
```

3. 返回：用户信息与 token。

## 4.4 问卷接口

### 4.4.1 查询我的问卷

1. GET /api/surveys。
2. 返回当前用户创建的问卷列表。

### 4.4.2 创建问卷

1. POST /api/surveys。
2. 请求示例：

```json
{
  "title": "校园饮食习惯",
  "description": "用于课程调研",
  "allow_anonymous": true,
  "allow_multiple_submissions": true,
  "deadline": "2026-04-01T12:00:00Z"
}
```

### 4.4.3 获取问卷详情

1. GET /api/surveys/{survey_id}。

### 4.4.4 更新问卷

1. PUT /api/surveys/{survey_id}。
2. 约束：仅草稿可编辑，非草稿返回错误。

### 4.4.5 删除问卷

1. DELETE /api/surveys/{survey_id}。
2. 删除问卷时会级联删除题目、跳转规则和提交记录。

### 4.4.6 状态流转

1. 发布：POST /api/surveys/{survey_id}/publish。
2. 关闭：POST /api/surveys/{survey_id}/close。
3. 草稿：POST /api/surveys/{survey_id}/draft。
4. 约束：发布或关闭后不可回退草稿。

## 4.5 题目接口

### 4.5.1 查询题目

1. GET /api/surveys/{survey_id}/questions。

### 4.5.2 新增题目

1. POST /api/surveys/{survey_id}/questions。
2. 约束：仅草稿问卷可新增。

单选示例：

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

多选示例：

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
  "validation": {
    "min_select": 1,
    "max_select": 2
  }
}
```

填空数字示例：

```json
{
  "order": 3,
  "type": "fill_blank",
  "title": "你的年龄",
  "required": true,
  "validation": {
    "value_type": "number",
    "min_value": 0,
    "max_value": 120,
    "is_integer": true
  }
}
```

### 4.5.3 更新题目

1. PUT /api/questions/{question_id}。
2. 约束：仅草稿问卷可更新。

### 4.5.4 删除题目

1. DELETE /api/questions/{question_id}。
2. 约束：仅草稿问卷可删除。

## 4.6 跳转规则接口

### 4.6.1 查询规则

1. GET /api/surveys/{survey_id}/jump-rules。

### 4.6.2 创建规则

1. POST /api/surveys/{survey_id}/jump-rules。
2. 约束：仅草稿问卷可配置。

示例：

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

### 4.6.3 删除规则

1. DELETE /api/jump-rules/{rule_id}。
2. 约束：仅草稿问卷可删除。

## 4.7 问卷填写接口

### 4.7.1 获取可填写问卷

1. GET /api/public/surveys/{slug}。
2. 仅发布状态且未过截止时间可访问。

### 4.7.2 计算下一题

1. POST /api/public/surveys/{slug}/next-question。

请求示例：

```json
{
  "current_question_id": "67ff...",
  "answer": "A"
}
```

返回示例：

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

无下一题时 next_question 为 null。

### 4.7.3 提交问卷

1. POST /api/public/surveys/{slug}/submit。
2. 请求示例：

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

3. 业务校验：

- 必答题不可为空。
- 答案必须满足题型校验。
- 答案必须位于本次真实跳转路径中。
- allow_multiple_submissions=false 时禁止重复提交。

## 4.8 统计接口

### 4.8.1 整卷统计

1. GET /api/surveys/{survey_id}/stats。
2. 返回提交总数、每题统计、提交用户记录。

整卷统计响应中的 submissions 字段说明：

- submission_id: 提交记录 ID。
- submitted_at: 提交时间。
- is_anonymous: 是否匿名提交。
- respondent_id: 提交用户 ID（仅用于系统内部关联）。
- respondent_username: 提交用户名；当 is_anonymous=true 时返回 null。

示例：

```json
{
  "submission_count": 2,
  "submissions": [
    {
      "submission_id": "6800...",
      "submitted_at": "2026-04-02T08:23:00+00:00",
      "is_anonymous": false,
      "respondent_id": "67ff...",
      "respondent_username": "alice"
    },
    {
      "submission_id": "6801...",
      "submitted_at": "2026-04-02T08:25:00+00:00",
      "is_anonymous": true,
      "respondent_id": "67aa...",
      "respondent_username": null
    }
  ]
}
```

### 4.8.2 单题统计

1. GET /api/questions/{question_id}/stats。
2. 返回按题型聚合结果：

- 单选：选项计数与作答人数。
- 多选：选项被选择次数。
- 填空：值列表，数字题额外返回平均值。

## 4.9 【第二阶段新增】题库接口（常用题目）

### 4.9.1 查询我的题库

1. GET /api/question-bank。
2. 返回当前用户保存的常用题目列表（仅最新版本）。

### 4.9.2 保存题目到题库

1. POST /api/question-bank。
2. 请求示例：

```json
{
  "type": "single_choice",
  "title": "你的年级",
  "options": [
    { "key": "A", "label": "大一" },
    { "key": "B", "label": "大二" },
    { "key": "C", "label": "大三" },
    { "key": "D", "label": "大四" }
  ],
  "is_public": false,
  "version_note": "初始版本"
}
```

3. 校验规则与题目接口一致（选择题至少2选项、填空题需 value_type 等）。

### 4.9.3 删除题库题目

1. DELETE /api/question-bank/{item_id}。
2. 删除单个版本。若删除的是最新版本，前一版本自动成为最新。
3. 查询参数 ?chain=true 可删除整个版本链。

### 4.9.4 从题库导入到问卷

1. POST /api/surveys/{survey_id}/questions/import。
2. 约束：仅草稿问卷可导入。
3. 请求示例：

```json
{
  "item_id": "680a...",
  "order": 3,
  "required": true
}
```

4. 支持导入自己题库、他人共享、或公开题目。导入时记录 bank_item_id、bank_chain_id、bank_version 到 questions 文档。

### 4.9.5 查看共享给我的题目

1. GET /api/question-bank/shared。
2. 返回其他用户共享给当前用户的题目（最新版本）。

### 4.9.6 查看公开题目

1. GET /api/question-bank/public。
2. 返回所有公开题目（排除自己的，最新版本）。

### 4.9.7 版本管理

1. 查看版本历史：GET /api/question-bank/{item_id}/versions。
2. 创建新版本：POST /api/question-bank/{item_id}/new-version。

请求示例：

```json
{
  "title": "修改后的标题",
  "version_note": "增加了选项E"
}
```

3. 恢复旧版本：POST /api/question-bank/{item_id}/restore。

请求示例：

```json
{
  "version_item_id": "681b..."
}
```

### 4.9.8 共享管理

1. 共享给指定用户：POST /api/question-bank/{item_id}/share。

```json
{
  "usernames": ["alice", "bob"]
}
```

2. 设置公开/私有：POST /api/question-bank/{item_id}/public。

```json
{
  "is_public": true
}
```

### 4.9.9 使用情况

1. GET /api/question-bank/{item_id}/usage。
2. 返回使用该题目（任何版本）的问卷列表。

### 4.9.10 跨问卷统计

1. GET /api/question-bank/{item_id}/cross-stats。
2. 返回该题目在所有问卷中的聚合统计结果，包括涉及问卷数、总回答数、按题型聚合统计。

## 4.10 常见错误示例

1. 401：未登录或 token 无效。
2. 404：问卷、题目、规则不存在。
3. 400：参数校验失败或业务约束不满足。

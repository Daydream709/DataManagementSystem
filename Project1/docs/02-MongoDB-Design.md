# 2. MongoDB 完整数据库设计

## 2.1 设计原则

1. 分集合存储，避免单集合聚合所有实体。
2. 使用 ObjectId 与文档嵌套结构表达业务关系。
3. 仅在必要处冗余，提高查询效率并控制一致性成本。
4. 跳转逻辑数据化，不写死在后端代码中。

## 2.2 集合设计总览

| 集合       | 作用               |
| ---------- | ------------------ |
| users      | 用户账号信息       |
| surveys    | 问卷主体信息       |
| questions  | 题目信息与校验规则 |
| jump_rules | 题目跳转规则       |
| answers    | 问卷提交答案       |

## 2.3 users 集合

### 字段设计

| 字段          | 类型     | 说明               |
| ------------- | -------- | ------------------ |
| \_id          | ObjectId | 用户主键           |
| username      | string   | 用户名，唯一       |
| password_hash | string   | 密码哈希（bcrypt） |
| created_at    | datetime | 注册时间           |

### 索引

- `uq_username`：`{ username: 1 }` unique

## 2.4 surveys 集合

### 字段设计

| 字段            | 类型          | 说明                   |
| --------------- | ------------- | ---------------------- |
| \_id            | ObjectId      | 问卷主键               |
| owner_id        | ObjectId      | 创建者用户ID           |
| title           | string        | 问卷标题               |
| description     | string        | 问卷说明               |
| allow_anonymous | bool          | 是否允许匿名提交       |
| deadline        | datetime/null | 截止时间               |
| status          | string        | draft/published/closed |
| slug            | string        | 问卷访问唯一标识       |
| created_at      | datetime      | 创建时间               |
| updated_at      | datetime      | 更新时间               |

### 索引

- `uq_survey_slug`：`{ slug: 1 }` unique
- `idx_survey_owner`：`{ owner_id: 1, created_at: 1 }`

## 2.5 questions 集合

### 字段设计

| 字段       | 类型     | 说明                                      |
| ---------- | -------- | ----------------------------------------- |
| \_id       | ObjectId | 题目主键                                  |
| survey_id  | ObjectId | 所属问卷ID                                |
| owner_id   | ObjectId | 问卷创建者ID（权限校验）                  |
| order      | int      | 题目顺序                                  |
| type       | string   | single_choice / multi_choice / fill_blank |
| title      | string   | 题目标题                                  |
| required   | bool     | 是否必答                                  |
| options    | array    | 选择题选项数组 `{key,label}`              |
| validation | object   | 校验规则，按题型解释                      |
| created_at | datetime | 创建时间                                  |
| updated_at | datetime | 更新时间                                  |

### validation 规则示例

- 单选：`{}`
- 多选：`{"min_select":1,"max_select":3}`
- 填空文本：`{"value_type":"text","min_length":1,"max_length":50}`
- 填空数字：`{"value_type":"number","min_value":0,"max_value":120,"is_integer":true}`

### 索引

- `idx_question_survey_order`：`{ survey_id: 1, order: 1 }`
- `idx_question_owner_survey`：`{ owner_id: 1, survey_id: 1 }`

## 2.6 jump_rules 集合

### 字段设计

| 字段               | 类型          | 说明                                                |
| ------------------ | ------------- | --------------------------------------------------- |
| \_id               | ObjectId      | 规则主键                                            |
| survey_id          | ObjectId      | 所属问卷ID                                          |
| owner_id           | ObjectId      | 规则创建者                                          |
| question_id        | ObjectId      | 源题目ID                                            |
| rule_type          | string        | single_choice / multi_choice / number               |
| operator           | string        | eq/in/contains_any/contains_all/gt/gte/lt/lte/range |
| value              | any           | 比较值                                              |
| target_question_id | ObjectId/null | 跳转到目标题目                                      |
| target_order       | int/null      | 或按顺序号跳转                                      |
| priority           | int           | 优先级，越小越先匹配                                |
| created_at         | datetime      | 创建时间                                            |

### 索引

- `idx_rule_survey_question_priority`：`{ survey_id: 1, question_id: 1, priority: 1 }`

## 2.7 answers 集合

### 字段设计

| 字段                  | 类型        | 说明                            |
| --------------------- | ----------- | ------------------------------- |
| \_id                  | ObjectId    | 提交记录主键                    |
| survey_id             | ObjectId    | 所属问卷ID                      |
| respondent_id         | ObjectId    | 提交者用户ID（填写前必须登录）  |
| is_anonymous          | bool        | 是否匿名提交                    |
| answers               | array       | 答案数组                        |
| answers[].question_id | ObjectId    | 题目ID                          |
| answers[].answer      | any         | 题目答案（string/array/number） |
| answers[].answered_at | datetime    | 作答时间                        |
| submitted_at          | datetime    | 提交时间                        |
| client_fingerprint    | string/null | 客户端标识（可选）              |

### 索引

- `idx_answer_survey_submitted`：`{ survey_id: 1, submitted_at: 1 }`
- `idx_answer_respondent`：`{ respondent_id: 1 }`
- `idx_answer_survey_respondent`：`{ survey_id: 1, respondent_id: 1 }`

## 2.8 为什么不使用关系型结构

1. 题目类型与校验规则差异大，Mongo 文档模型更灵活。
2. 跳转规则 `operator + value` 具有半结构化特点，关系表会导致拆表过多。
3. 提交答案可自然嵌套在单条提交文档中，便于整体读取与统计。
4. 第二阶段迭代会持续变化，Mongo schema 演进成本更低。

## 2.9 为什么适配 MongoDB

- 文档模型与问卷结构天然匹配（问卷-题目-规则-答案）。
- 支持快速演进与字段增量扩展，适合教学项目迭代。
- 查询模式以 owner_id、survey_id 为主，索引可直接覆盖核心路径。

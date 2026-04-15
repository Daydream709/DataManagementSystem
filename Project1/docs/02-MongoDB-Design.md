# 2. MongoDB 数据库设计说明

## 2.1 设计目标

1. 问卷结构变化快，题型和规则具备半结构化特征。
2. 提交流程依赖跳转路径，校验逻辑必须由数据驱动。

## 2.2 设计原则

1. 分集合建模：按业务域拆分，避免单集合过度耦合。
2. 最小必要冗余：仅在查询或权限校验需要处增加冗余字段。
3. 规则数据化：跳转条件通过字段表达，不写死在代码。
4. 索引优先：围绕 owner_id、survey_id、slug、submitted_at 设计索引。

## 2.3 集合总览

| 集合          | 说明                         | 典型访问模式                                   |
| ------------- | ---------------------------- | ---------------------------------------------- |
| users         | 用户账号信息                 | username 精确查询                              |
| surveys       | 问卷元信息                   | owner_id 列表、slug 公开访问                   |
| questions     | 题目与校验规则               | survey_id + order 顺序读取                     |
| jump_rules    | 跳转规则                     | survey_id + question_id 按 priority 匹配       |
| answers       | 提交结果                     | survey_id 统计、survey_id + respondent_id 判重 |
| question_bank | 【第二阶段新增】常用题目题库 | owner_id 列表查询、版本链管理、共享与公开查询  |

## 2.4 结构关系

1. users 1:N surveys。
2. surveys 1:N questions。
3. surveys 1:N jump_rules。
4. surveys 1:N answers。
5. answers.answers[] 内嵌每个题目的作答项。
6. 【第二阶段新增】users 1:N question_bank（常用题库，独立于问卷，按版本链组织）。
7. 【第二阶段新增】question_bank 通过导入操作复用到多个 surveys 的 questions 中，导入时在 questions 文档记录 bank_chain_id 以追踪来源。

说明：
questions 与 jump_rules 分离，避免将规则嵌入题目导致频繁整体更新。

## 2.5 集合字段设计

### 2.5.1 users

| 字段          | 类型     | 说明         |
| ------------- | -------- | ------------ |
| \_id          | ObjectId | 用户主键     |
| username      | string   | 用户名，唯一 |
| password_hash | string   | bcrypt 哈希  |
| created_at    | datetime | 注册时间     |

索引：

1. uq_username: { username: 1 } unique。

### 2.5.2 surveys

| 字段                       | 类型          | 说明                     |
| -------------------------- | ------------- | ------------------------ |
| \_id                       | ObjectId      | 问卷主键                 |
| owner_id                   | ObjectId      | 创建者                   |
| title                      | string        | 标题                     |
| description                | string        | 说明                     |
| allow_anonymous            | bool          | 是否允许匿名提交         |
| allow_multiple_submissions | bool          | 是否允许同一用户多次提交 |
| deadline                   | datetime/null | 截止时间                 |
| status                     | string        | draft/published/closed   |
| slug                       | string        | 对外访问标识             |
| created_at                 | datetime      | 创建时间                 |
| updated_at                 | datetime      | 更新时间                 |

索引：

1. uq_survey_slug: { slug: 1 } unique。
2. idx_survey_owner: { owner_id: 1, created_at: 1 }。

### 2.5.3 questions

| 字段          | 类型          | 说明                                  |
| ------------- | ------------- | ------------------------------------- |
| \_id          | ObjectId      | 题目主键                              |
| survey_id     | ObjectId      | 所属问卷                              |
| owner_id      | ObjectId      | 创建者（权限隔离）                    |
| order         | int           | 显示顺序                              |
| type          | string        | single_choice/multi_choice/fill_blank |
| title         | string        | 题干                                  |
| required      | bool          | 必答标记                              |
| options       | array         | 选择题选项，元素为 {key,label}        |
| validation    | object        | 按题型定义的校验规则                  |
| created_at    | datetime      | 创建时间                              |
| updated_at    | datetime      | 更新时间                              |
| bank_item_id  | ObjectId/null | 【第二阶段新增】导入来源的题库条目 ID |
| bank_chain_id | ObjectId/null | 【第二阶段新增】导入来源的版本链标识  |
| bank_version  | int/null      | 【第二阶段新增】导入时的题库版本号    |

validation 示例：

1. 单选: {}。
2. 多选: {"min_select": 1, "max_select": 3}。
3. 填空文本: {"value_type": "text", "min_length": 1, "max_length": 100}。
4. 填空数字: {"value_type": "number", "min_value": 0, "max_value": 120, "is_integer": true}。

索引：

1. idx_question_survey_order: { survey_id: 1, order: 1 }。
2. idx_question_owner_survey: { owner_id: 1, survey_id: 1 }。
3. 【第二阶段新增】idx_question_bank_chain: { bank_chain_id: 1 }。

### 2.5.4 jump_rules

| 字段               | 类型          | 说明                                                |
| ------------------ | ------------- | --------------------------------------------------- |
| \_id               | ObjectId      | 规则主键                                            |
| survey_id          | ObjectId      | 所属问卷                                            |
| owner_id           | ObjectId      | 创建者                                              |
| question_id        | ObjectId      | 源题目                                              |
| rule_type          | string        | single_choice/multi_choice/number                   |
| operator           | string        | eq/in/contains_any/contains_all/gt/gte/lt/lte/range |
| value              | any           | 比较值                                              |
| target_question_id | ObjectId/null | 跳转目标题目                                        |
| target_order       | int/null      | 或跳转到目标序号                                    |
| priority           | int           | 优先级（越小越先）                                  |
| created_at         | datetime      | 创建时间                                            |

索引：

1. idx_rule_survey_question_priority: { survey_id: 1, question_id: 1, priority: 1 }。

### 2.5.5 answers

| 字段                  | 类型        | 说明               |
| --------------------- | ----------- | ------------------ |
| \_id                  | ObjectId    | 提交主键           |
| survey_id             | ObjectId    | 所属问卷           |
| respondent_id         | ObjectId    | 提交者（登录用户） |
| is_anonymous          | bool        | 匿名展示标记       |
| answers               | array       | 作答明细           |
| answers[].question_id | ObjectId    | 题目ID             |
| answers[].answer      | any         | 作答内容           |
| answers[].answered_at | datetime    | 作答时间           |
| submitted_at          | datetime    | 提交时间           |
| client_fingerprint    | string/null | 可选客户端标识     |

索引：

1. idx_answer_survey_submitted: { survey_id: 1, submitted_at: 1 }。
2. idx_answer_respondent: { respondent_id: 1 }。
3. idx_answer_survey_respondent: { survey_id: 1, respondent_id: 1 }。

### 2.5.6 【第二阶段新增】question_bank

| 字段         | 类型          | 说明                                  |
| ------------ | ------------- | ------------------------------------- |
| \_id         | ObjectId      | 题目主键                              |
| owner_id     | ObjectId      | 所属用户                              |
| type         | string        | single_choice/multi_choice/fill_blank |
| title        | string        | 题干                                  |
| options      | array         | 选择题选项，元素为 {key,label}        |
| validation   | object        | 按题型定义的校验规则                  |
| chain_id     | ObjectId      | 版本链标识，首版本 chain_id = \_id    |
| parent_id    | ObjectId/null | 直接前驱版本，首版本为 null           |
| version      | int           | 版本号，从 1 递增                     |
| version_note | string        | 版本说明                              |
| shared_with  | array         | 共享目标用户 ID 列表                  |
| is_public    | bool          | 是否公开（所有登录用户可见）          |
| is_latest    | bool          | 是否为版本链中的最新版本              |
| created_at   | datetime      | 创建时间                              |
| updated_at   | datetime      | 更新时间                              |

版本链示例：

1. v1: chain_id = v1.\_id, parent_id = null, version = 1, is_latest = true。
2. 创建 v2: v1.is_latest 设为 false; v2: chain_id = v1.\_id, parent_id = v1.\_id, version = 2, is_latest = true。
3. 恢复 v1: 创建 v3，内容同 v1，chain_id = v1.\_id, parent_id = v2.\_id, version = 3。

索引：

1. idx_qbank_owner_latest_created: { owner_id: 1, is_latest: 1, created_at: 1 }。
2. idx_qbank_chain_version: { chain_id: 1, version: 1 }。
3. idx_qbank_shared_latest: { shared_with: 1, is_latest: 1 }。
4. idx_qbank_public_latest_created: { is_public: 1, is_latest: 1, created_at: 1 }。

## 2.6 核心查询与索引匹配

1. 我的问卷列表：surveys.find({owner_id}).sort(created_at) -> idx_survey_owner。
2. 按链接访问问卷：surveys.findOne({slug}) -> uq_survey_slug。
3. 按问卷读取题目：questions.find({survey_id}).sort(order) -> idx_question_survey_order。
4. 跳转计算：jump_rules.find({survey_id}).sort(priority) -> idx_rule_survey_question_priority。
5. 判定重复提交：answers.findOne({survey_id, respondent_id}) -> idx_answer_survey_respondent。
6. 问卷统计：answers.find({survey_id}) -> idx_answer_survey_submitted。
7. 【第二阶段新增】题库列表（最新版本）：question_bank.find({owner_id, is_latest:true}).sort(created_at) -> idx_qbank_owner_latest_created。
8. 【第二阶段新增】题库版本链：question_bank.find({chain_id}).sort(version) -> idx_qbank_chain_version。
9. 【第二阶段新增】共享给我的题目：question_bank.find({shared_with, is_latest:true}) -> idx_qbank_shared_latest。
10. 【第二阶段新增】公开题目：question_bank.find({is_public:true, is_latest:true}).sort(created_at) -> idx_qbank_public_latest_created。
11. 【第二阶段新增】跨问卷统计：questions.find({bank_chain_id}) -> idx_question_bank_chain。

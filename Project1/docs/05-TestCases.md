# 5. 测试用例文档（手动测试 + API测试 + 自动化脚本）

## 5.1 覆盖目标

本测试文档完整覆盖课程作业第一阶段要求功能，并为每项测试提供两套方法：

1. 手动测试方法。
2. API测试方法。

覆盖项：

1. 用户注册与登录测试。
2. 创建问卷测试。
3. 添加题目测试。
4. 跳转逻辑测试。
5. 校验测试。
6. 提交问卷测试。
7. 统计测试。
8. 非草稿编辑拦截。
9. 发布/关闭不可回草稿。
10. 统计用户名可见性（匿名隐藏）。

## 5.2 测试环境

1. 前端地址: http://localhost:5173
2. 后端地址: http://localhost:8000
3. API前缀: http://localhost:8000/api
4. 数据库: MongoDB 本地实例，DB: survey_system
5. 鉴权: Authorization: Bearer <token>

## 5.3 统一测试数据

1. 用户A(问卷创建者): owner_xxx
2. 用户B(实名填写者): user1_xxx
3. 用户C(匿名填写者): user2_xxx
4. 用户D(鉴权测试账号): auth_xxx
5. 问卷配置:

- allow_anonymous = true
- allow_multiple_submissions = false

6. 题目配置:

- Q1: 单选，必答，A=是，B=否
- Q2: 多选，必答，min_select=1, max_select=2
- Q3: 数字填空，必答，is_integer=true, 0-120

7. 跳转规则:

- Q1=A -> Q3
- Q1=B -> Q2

## 5.4 用例矩阵

| 用例ID | 用例名称         | 作业要求覆盖 |
| ------ | ---------------- | ------------ |
| TC-01  | 用户注册与登录   | 回归与约束   |
| TC-02  | 创建问卷         | 创建问卷     |
| TC-03  | 添加题目         | 添加题目     |
| TC-04  | 跳转逻辑         | 跳转逻辑     |
| TC-05  | 校验拦截         | 校验测试     |
| TC-06  | 提交问卷         | 提交测试     |
| TC-07  | 统计结果         | 统计测试     |
| TC-08  | 非草稿编辑拦截   | 回归与约束   |
| TC-09  | 状态不可回草稿   | 回归与约束   |
| TC-10  | 统计用户名可见性 | 回归与约束   |

## 5.5 自动化 API 测试脚本

脚本路径:

1. backend/tests/run_api_test_suite.py

运行命令:

```powershell
cd backend
python tests/run_api_test_suite.py --base-url http://127.0.0.1:8000/api
```

脚本覆盖范围:

1. TC-01 到 TC-10 全部覆盖。
2. 自动创建测试用户与测试问卷。
3. 自动执行并输出 PASS/FAIL。
4. 每一步打印 API 方法、路径、请求体和服务器实际响应（状态码与响应体）。
5. 执行结束输出按用例维度的通过汇总。
6. 自动清理测试问卷数据。

判定规则:

1. 终端输出“失败: 0”视为与预期一致。
2. 进程退出码为 0 视为全部通过。

## 5.6 本地自动化测试执行记录

1. 执行时间: 2026-04-02（本地环境）
2. 执行命令: python tests/run_api_test_suite.py --base-url http://127.0.0.1:8000/api
3. 输出摘要: 全部用例执行完成，覆盖 TC-01 到 TC-10，并完成清理测试问卷。
4. 通过数: 55
5. 失败数: 0
6. 结论: 通过

## 5.7 详细测试方法

### TC-01 用户注册与登录

#### A. 手动测试方法

步骤:

1. 打开登录页并切换到注册表单。
2. 使用新用户名和合法密码注册。
3. 使用同账号登录并确认进入系统。
4. 使用同用户名再次注册。
5. 尝试注册用户名长度小于 3 的账号。
6. 尝试注册密码长度小于 6 的账号。
7. 使用错误密码登录已存在账号。

输入:

1. 合法注册: username=auth_xxx, password=Passw0rd!
2. 重复注册: username=auth_xxx, password=Passw0rd!
3. 短用户名注册: username=ab, password=Passw0rd!
4. 短密码注册: username=weak_xxx, password=12345
5. 错误密码登录: username=auth_xxx, password=wrong_pass_123

预期输出:

1. 合法注册成功。
2. 合法登录成功并获取 token。
3. 重复注册失败。
4. 短用户名注册失败。
5. 短密码注册失败。
6. 错误密码登录失败。

#### B. API测试方法

步骤:

1. POST /api/auth/register 注册新用户。
2. POST /api/auth/login 使用正确密码登录。
3. POST /api/auth/register 使用同用户名重复注册。
4. POST /api/auth/register 提交短用户名。
5. POST /api/auth/register 提交短密码。
6. POST /api/auth/login 使用错误密码登录。
7. POST /api/auth/login 使用不存在用户名登录。

每一步输入:

1. 步骤1 输入:

- 方法与路径: POST /api/auth/register
- Header: Content-Type: application/json
- Body:

```json
{
  "username": "auth_xxx",
  "password": "Passw0rd!"
}
```

2. 步骤2 输入:

- 方法与路径: POST /api/auth/login
- Header: Content-Type: application/json
- Body:

```json
{
  "username": "auth_xxx",
  "password": "Passw0rd!"
}
```

3. 步骤3 输入:

- 方法与路径: POST /api/auth/register
- Header: Content-Type: application/json
- Body（与步骤1相同，用于验证重复注册）:

```json
{
  "username": "auth_xxx",
  "password": "Passw0rd!"
}
```

4. 步骤4 输入:

- 方法与路径: POST /api/auth/register
- Header: Content-Type: application/json
- Body:

```json
{
  "username": "ab",
  "password": "Passw0rd!"
}
```

5. 步骤5 输入:

- 方法与路径: POST /api/auth/register
- Header: Content-Type: application/json
- Body:

```json
{
  "username": "weak_xxx",
  "password": "12345"
}
```

6. 步骤6 输入:

- 方法与路径: POST /api/auth/login
- Header: Content-Type: application/json
- Body:

```json
{
  "username": "auth_xxx",
  "password": "wrong_pass_123"
}
```

7. 步骤7 输入:

- 方法与路径: POST /api/auth/login
- Header: Content-Type: application/json
- Body:

```json
{
  "username": "missing_xxx",
  "password": "Passw0rd!"
}
```

预期输出:

1. 注册成功: HTTP 201, code=0。
2. 登录成功: HTTP 200, code=0, data.token 非空。
3. 重复注册: HTTP >= 400, code=1。
4. 短用户名注册: HTTP >= 400, code=1。
5. 短密码注册: HTTP >= 400, code=1。
6. 错误密码登录: HTTP >= 400, code=1。
7. 不存在用户登录: HTTP >= 400, code=1。

### TC-02 创建问卷

#### A. 手动测试方法

前置条件:

1. 用户A已注册并登录。

步骤:

1. 打开问卷列表页，填写标题、描述、匿名选项、重复提交选项。
2. 点击创建问卷。
3. 在列表中刷新查看新问卷。

输入:

1. title: 自动化测试问卷
2. description: API自动测试
3. allow_anonymous: true
4. allow_multiple_submissions: false

预期输出:

1. 页面提示创建成功。
2. 问卷出现在列表中，状态为 draft。

#### B. API测试方法

步骤:

1. POST /api/surveys 创建问卷。
2. GET /api/surveys 查询列表。

每一步输入:

1. 步骤1 输入:

- 方法与路径: POST /api/surveys
- Header:
  - Content-Type: application/json
  - Authorization: Bearer <owner_token>

- Body:

```json
{
  "title": "自动化测试问卷",
  "description": "API自动测试",
  "allow_anonymous": true,
  "allow_multiple_submissions": false
}
```

2. 步骤2 输入:

- 方法与路径: GET /api/surveys
- Header: Authorization: Bearer <owner_token>
- Body: 无

预期输出:

1. 创建接口 HTTP 201，code=0。
2. 响应 data.status=draft，返回 survey_id、slug。
3. 列表查询中可找到该问卷。

### TC-03 添加题目

#### A. 手动测试方法

前置条件:

1. TC-02 已通过，问卷处于 draft。

步骤:

1. 进入问卷编辑页。
2. 新增 Q1 单选题。
3. 新增 Q2 多选题并设置 min/max。
4. 新增 Q3 数字填空题并设置整数限制。
5. 返回题目列表确认顺序。

输入:

1. Q1 options: A/B
2. Q2 options: A/B/C, min=1, max=2
3. Q3 validation: number, min=0, max=120, is_integer=true

预期输出:

1. 三道题新增成功。
2. 题目顺序为 Q1/Q2/Q3。

#### B. API测试方法

步骤:

1. POST /api/surveys/{survey_id}/questions 三次创建题目。
2. GET /api/surveys/{survey_id}/questions 查询列表。

每一步输入:

1. 步骤1 输入（第1次创建 Q1）:

- 方法与路径: POST /api/surveys/{survey_id}/questions
- 路径参数: survey_id=TC-02 返回的 survey_id
- Header:
  - Content-Type: application/json
  - Authorization: Bearer <owner_token>

- Body:

```json
{
  "order": 1,
  "type": "single_choice",
  "title": "你是否每天运动？",
  "required": true,
  "options": [
    { "key": "A", "label": "是" },
    { "key": "B", "label": "否" }
  ]
}
```

2. 步骤1 输入（第2次创建 Q2）:

- 方法与路径: POST /api/surveys/{survey_id}/questions
- 路径参数: survey_id=TC-02 返回的 survey_id
- Header:
  - Content-Type: application/json
  - Authorization: Bearer <owner_token>

- Body:

```json
{
  "order": 2,
  "type": "multi_choice",
  "title": "你常做的运动项目？",
  "required": true,
  "options": [
    { "key": "A", "label": "跑步" },
    { "key": "B", "label": "游泳" },
    { "key": "C", "label": "健身" }
  ],
  "validation": { "min_select": 1, "max_select": 2 }
}
```

3. 步骤1 输入（第3次创建 Q3）:

- 方法与路径: POST /api/surveys/{survey_id}/questions
- 路径参数: survey_id=TC-02 返回的 survey_id
- Header:
  - Content-Type: application/json
  - Authorization: Bearer <owner_token>

- Body:

```json
{
  "order": 3,
  "type": "fill_blank",
  "title": "你每周运动几次？",
  "required": true,
  "validation": {
    "value_type": "number",
    "min_value": 0,
    "max_value": 120,
    "is_integer": true
  }
}
```

4. 步骤2 输入:

- 方法与路径: GET /api/surveys/{survey_id}/questions
- 路径参数: survey_id=TC-02 返回的 survey_id
- Header: Authorization: Bearer <owner_token>
- Body: 无

预期输出:

1. 三次创建均 HTTP 201，code=0。
2. 列表返回 3 条记录，order 升序。

### TC-04 跳转逻辑

#### A. 手动测试方法

前置条件:

1. 题目已创建。

步骤:

1. 在规则配置中设置 Q1=A 跳转 Q3。
2. 设置 Q1=B 跳转 Q2。
3. 发布问卷后进入填写页。
4. 选择 A，观察下一题是否为 Q3。
5. 重新填写选择 B，观察下一题是否为 Q2。

输入:

1. rule1: eq A -> Q3
2. rule2: eq B -> Q2

预期输出:

1. A 路径进入 Q3。
2. B 路径进入 Q2。

#### B. API测试方法

步骤:

1. POST /api/surveys/{survey_id}/jump-rules 创建两条规则。
2. POST /api/surveys/{survey_id}/publish 发布问卷。
3. POST /api/public/surveys/{slug}/next-question 测试 A/B。

每一步输入:

1. 步骤1 输入（规则1）:

- 方法与路径: POST /api/surveys/{survey_id}/jump-rules
- 路径参数: survey_id=TC-02 返回的 survey_id
- Header:
  - Content-Type: application/json
  - Authorization: Bearer <owner_token>

- Body:

```json
{
  "question_id": "Q1_ID",
  "rule_type": "single_choice",
  "operator": "eq",
  "value": "A",
  "target_question_id": "Q3_ID",
  "priority": 1
}
```

2. 步骤1 输入（规则2）:

- 方法与路径: POST /api/surveys/{survey_id}/jump-rules
- 路径参数: survey_id=TC-02 返回的 survey_id
- Header:
  - Content-Type: application/json
  - Authorization: Bearer <owner_token>

- Body:

```json
{
  "question_id": "Q1_ID",
  "rule_type": "single_choice",
  "operator": "eq",
  "value": "B",
  "target_question_id": "Q2_ID",
  "priority": 2
}
```

3. 步骤2 输入:

- 方法与路径: POST /api/surveys/{survey_id}/publish
- 路径参数: survey_id=TC-02 返回的 survey_id
- Header: Authorization: Bearer <owner_token>
- Body: 无

4. 步骤3 输入（测试 A 路径）:

- 方法与路径: POST /api/public/surveys/{slug}/next-question
- 路径参数: slug=TC-02 返回的 slug
- Header:
  - Content-Type: application/json
  - Authorization: Bearer <user1_token>

- Body:

```json
{
  "current_question_id": "Q1_ID",
  "answer": "A"
}
```

5. 步骤3 输入（测试 B 路径）:

- 方法与路径: POST /api/public/surveys/{slug}/next-question
- 路径参数: slug=TC-02 返回的 slug
- Header:
  - Content-Type: application/json
  - Authorization: Bearer <user1_token>

- Body:

```json
{
  "current_question_id": "Q1_ID",
  "answer": "B"
}
```

预期输出:

1. A 返回 next_question.id = Q3_ID。
2. B 返回 next_question.id = Q2_ID。

### TC-05 校验拦截

#### A. 手动测试方法

步骤:

1. 填写 Q1=A 后不填写 Q3 直接提交。
2. 填写 Q1=B，Q2 选择 3 项提交。
3. 在数字题输入 3.14（要求整数）。

输入:

1. 缺失必答题。
2. 多选超上限。
3. 非整数数值。

预期输出:

1. 均被拦截并提示校验错误。
2. 不写入非法提交。

#### B. API测试方法

步骤:

1. POST /submit 提交缺失必答答案。
2. POST /submit 提交多选超上限答案。
3. POST /next-question 对 Q3 提交 3.14。

每一步输入:

1. 步骤1 输入（缺失必答）:

- 方法与路径: POST /api/public/surveys/{slug}/submit
- 路径参数: slug=TC-02 返回的 slug
- Header:
  - Content-Type: application/json
  - Authorization: Bearer <user1_token>

- Body:

```json
{
  "is_anonymous": false,
  "answers": [{ "question_id": "Q1_ID", "answer": "A" }]
}
```

2. 步骤2 输入（多选超上限）:

- 方法与路径: POST /api/public/surveys/{slug}/submit
- 路径参数: slug=TC-02 返回的 slug
- Header:
  - Content-Type: application/json
  - Authorization: Bearer <user1_token>

- Body:

```json
{
  "is_anonymous": false,
  "answers": [
    { "question_id": "Q1_ID", "answer": "B" },
    { "question_id": "Q2_ID", "answer": ["A", "B", "C"] },
    { "question_id": "Q3_ID", "answer": 10 }
  ]
}
```

3. 步骤3 输入（整数校验失败）:

- 方法与路径: POST /api/public/surveys/{slug}/next-question
- 路径参数: slug=TC-02 返回的 slug
- Header:
  - Content-Type: application/json
  - Authorization: Bearer <user1_token>

- Body:

```json
{
  "current_question_id": "Q3_ID",
  "answer": 3.14
}
```

预期输出:

1. HTTP >= 400，code=1。
2. message 为校验失败信息。

### TC-06 提交问卷

#### A. 手动测试方法

步骤:

1. 用户B实名填写并提交。
2. 用户C匿名填写并提交。
3. 用户B再次提交同问卷。

输入:

1. 用户B: Q1=A, Q3=20, is_anonymous=false
2. 用户C: Q1=B, Q2=[A,B], Q3=22, is_anonymous=true

预期输出:

1. 前两次提交成功。
2. 第三次被拦截（不允许重复提交）。

#### B. API测试方法

步骤:

1. POST /submit 使用用户B token 提交实名答案。
2. POST /submit 使用用户C token 提交匿名答案。
3. 再次使用用户B token 提交。

每一步输入:

1. 步骤1 输入（实名提交）:

- 方法与路径: POST /api/public/surveys/{slug}/submit
- 路径参数: slug=TC-02 返回的 slug
- Header:
  - Content-Type: application/json
  - Authorization: Bearer <user1_token>

- Body:

```json
{
  "is_anonymous": false,
  "answers": [
    { "question_id": "Q1_ID", "answer": "A" },
    { "question_id": "Q3_ID", "answer": 20 }
  ]
}
```

2. 步骤2 输入（匿名提交）:

- 方法与路径: POST /api/public/surveys/{slug}/submit
- 路径参数: slug=TC-02 返回的 slug
- Header:
  - Content-Type: application/json
  - Authorization: Bearer <user2_token>

- Body:

```json
{
  "is_anonymous": true,
  "answers": [
    { "question_id": "Q1_ID", "answer": "B" },
    { "question_id": "Q2_ID", "answer": ["A", "B"] },
    { "question_id": "Q3_ID", "answer": 22 }
  ]
}
```

3. 步骤3 输入（重复提交）:

- 方法与路径: POST /api/public/surveys/{slug}/submit
- 路径参数: slug=TC-02 返回的 slug
- Header:
  - Content-Type: application/json
  - Authorization: Bearer <user1_token>

- Body（与步骤1相同）:

```json
{
  "is_anonymous": false,
  "answers": [
    { "question_id": "Q1_ID", "answer": "A" },
    { "question_id": "Q3_ID", "answer": 20 }
  ]
}
```

预期输出:

1. 前两次 HTTP 201，code=0，返回 submission_id。
2. 第三次 HTTP >= 400，code=1。

### TC-07 统计结果

#### A. 手动测试方法

步骤:

1. 打开统计页查看整卷统计。
2. 在单题下拉中选择 Q1、Q2、Q3 逐一核对。

输入:

1. 两份有效提交（来自 TC-06）。

预期输出:

1. submission_count = 2。
2. Q1 统计: A=1, B=1。
3. Q2 统计: A=1, B=1, C=0。
4. Q3 平均值: 21。

#### B. API测试方法

步骤:

1. GET /api/surveys/{survey_id}/stats。
2. GET /api/questions/{q1_id}/stats。

每一步输入:

1. 步骤1 输入:

- 方法与路径: GET /api/surveys/{survey_id}/stats
- 路径参数: survey_id=TC-02 返回的 survey_id
- Header: Authorization: Bearer <owner_token>
- Body: 无

2. 步骤2 输入:

- 方法与路径: GET /api/questions/{q1_id}/stats
- 路径参数: q1_id=TC-03 创建的 Q1_ID
- Header: Authorization: Bearer <owner_token>
- Body: 无

预期输出:

1. 整卷统计包含 submission_count=2。
2. 每题统计值与手动预期一致。

### TC-08 非草稿编辑拦截

#### A. 手动测试方法

步骤:

1. 发布问卷后进入编辑页。
2. 尝试修改问卷信息、题目、规则。

预期输出:

1. 前端显示仅可查看。
2. 无法执行编辑操作。

#### B. API测试方法

步骤:

1. 发布后调用 POST /api/surveys/{survey_id}/questions。

每一步输入:

1. 步骤1 输入:

- 方法与路径: POST /api/surveys/{survey_id}/questions
- 路径参数: survey_id=TC-02 返回的 survey_id（状态应为 published）
- Header:
  - Content-Type: application/json
  - Authorization: Bearer <owner_token>

- Body:

```json
{
  "order": 10,
  "type": "single_choice",
  "title": "发布后不应允许新增",
  "required": false,
  "options": [
    { "key": "A", "label": "是" },
    { "key": "B", "label": "否" }
  ]
}
```

预期输出:

1. HTTP >= 400，code=1。
2. message 表示仅草稿可操作。

### TC-09 发布/关闭不可回草稿

#### A. 手动测试方法

步骤:

1. 将问卷发布或关闭。
2. 尝试点击“设为草稿”。

预期输出:

1. 操作失败，状态不回退。

#### B. API测试方法

步骤:

1. POST /api/surveys/{survey_id}/draft。

每一步输入:

1. 步骤1 输入:

- 方法与路径: POST /api/surveys/{survey_id}/draft
- 路径参数: survey_id=TC-02 返回的 survey_id（状态应为 published 或 closed）
- Header: Authorization: Bearer <owner_token>
- Body: 无

预期输出:

1. HTTP >= 400，code=1。
2. message 包含“不能改回草稿”。

### TC-10 统计用户名可见性

#### A. 手动测试方法

步骤:

1. 进入统计页“填写用户记录”区块。
2. 对比实名提交和匿名提交展示内容。

输入:

1. 一条实名提交，一条匿名提交。

预期输出:

1. 实名提交显示用户名。
2. 匿名提交显示“匿名提交”，不显示真实用户名。

#### B. API测试方法

步骤:

1. GET /api/surveys/{survey_id}/stats。
2. 检查 data.submissions 每条记录。

每一步输入:

1. 步骤1 输入:

- 方法与路径: GET /api/surveys/{survey_id}/stats
- 路径参数: survey_id=TC-02 返回的 survey_id
- Header: Authorization: Bearer <owner_token>
- Body: 无

2. 步骤2 输入:

- 在步骤1返回体中读取 data.submissions。
- 逐条检查字段:
  - is_anonymous
  - respondent_username

预期输出:

1. is_anonymous=false 的记录有 respondent_username。
2. is_anonymous=true 的记录 respondent_username 为 null。

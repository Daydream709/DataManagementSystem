# 1. 系统说明与架构设计

## 1.1 项目目标与评分对齐

本项目实现一个简化版在线问卷系统，核心目标与评分点对齐如下：

1. MongoDB 数据库设计能力：采用多集合建模并给出索引与设计理由。
2. 后端程序设计能力：实现注册登录、问卷管理、填写提交、统计分析。
3. 数据结构与业务建模能力：清晰化业务模型，准确设计数据库。
4. 条件逻辑与跳转逻辑能力：支持单选、多选、数字条件跳转。
5. AI 工具使用规范：提供 AI 使用日志与报告总结。

## 1.2 项目文件结构

为便于阅读代码与定位功能模块，项目目录结构如下（省略无关缓存文件）：

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
│  │     └─ survey/
│  │        ├─ QuestionBuilder.vue       # 题目配置组件
│  │        ├─ JumpRuleBuilder.vue       # 跳转规则组件
│  │        ├─ FillQuestionCard.vue      # 填写卡片组件
│  │        └─ QuestionBankPanel.vue     # 【第二阶段新增】题库面板组件
│  ├─ package.json
│  └─ vite.config.js
├─ docs/
│  ├─ 01-Architecture.md
│  ├─ 02-MongoDB-Design.md
│  ├─ 03-Deployment.md
│  ├─ 04-API.md
│  ├─ 05-TestCases.md
│  ├─ 06-AI-Usage-Log.md
│  └─ 项目完成报告.md
└─ README.md
```

目录设计思路：

1. backend 按“接口层 + 服务层 + 数据访问层”组织，便于业务聚合与复用。
2. frontend 按“页面视图 + 接口封装 + 路由状态”组织，便于功能拆分与维护。
3. docs 独立维护课程交付文档，确保实现与文档可追溯。

## 1.3 技术方案

1. 前端：Vue3 + Vite + Pinia + Vue Router + Axios + TailwindCSS
2. 后端：Django + DRF + PyMongo
3. 数据库：MongoDB
4. 鉴权：JWT（Bearer Token）

## 1.4 总体架构

采用前后端分离架构：

1. 前端负责页面交互与接口调用。
2. 后端负责权限、校验、跳转、统计等业务规则。
3. MongoDB 负责持久化，按业务域拆分集合。

请求链路：

1. 用户登录获取 JWT。
2. 前端在请求头附带 Authorization: Bearer token。
3. 后端认证用户后进入服务层。
4. 服务层执行规则校验并读写 MongoDB。
5. 返回统一 JSON 响应。

## 1.5 功能模块

### 前端模块

1. 认证模块：注册、登录、会话状态维护。
2. 问卷管理模块：创建、发布、关闭、删除、复制链接。
3. 编辑模块：题目管理与跳转规则可视化配置。
4. 填写模块：按规则跳题、进度展示、提交锁定。
5. 统计模块：整卷统计与单题统计可视化。
6. 【第二阶段新增】题库模块：常用题目保存、版本管理、共享、跨问卷统计。

### 后端模块

1. 用户模块：注册登录、密码哈希、JWT 签发。
2. 问卷模块：问卷 CRUD 与状态流转。
3. 题目模块：单选/多选/填空题校验。
4. 跳转模块：规则增删查与规则引擎。
5. 提交模块：真实路径计算、必答校验、提交写入。
6. 统计模块：按题型聚合统计。
7. 【第二阶段新增】题库模块：题目保存、版本链管理、共享、使用追踪、跨问卷统计。

## 1.6 关键业务约束

1. 所有业务数据存储在 MongoDB。
2. 填写问卷前必须登录。
3. 编辑类操作仅允许草稿问卷。
4. 发布或关闭后不可回退为草稿。
5. 是否允许同一用户重复填写由问卷配置控制。

## 1.7 后端关键逻辑实现说明

### 1.7.1 MongoDB 连接与访问方式

后端采用 PyMongo 直连 MongoDB，不通过关系型 ORM。连接层的职责是：

1. 从环境变量读取 MONGODB_URI 与 MONGODB_DB_NAME。
2. 初始化全局 MongoClient 并复用连接池。
3. 通过统一的 get_collection 方法按集合名获取 users、surveys、questions、jump_rules、answers。
4. 在启动阶段确保关键索引存在，例如 username 唯一索引、survey_id 相关查询索引。

这样设计的好处是：

1. 避免每次请求重复建连，减少连接开销。
2. 集中管理集合与索引，便于排查问题。
3. 保留文档模型灵活性，适配题型与规则扩展。

### 1.7.2 跳转逻辑如何实现

跳转逻辑由规则数据驱动，而不是写死在代码里。每条规则核心字段包括：question_id、rule_type、operator、value、target_question_id、priority。

执行流程如下：

1. 前端调用 next-question 接口并提交 current_question_id 与当前答案 answer。
2. 后端读取该问卷该题的所有规则，按 priority 从小到大排序。
3. 逐条执行条件匹配：
   - 单选常用 eq。
   - 多选常用 contains_any、contains_all。
   - 数字题常用 gt、gte、lt、lte、range。

4. 命中第一条规则后，返回该规则指向的下一题。
5. 如果没有命中规则，则按题目 order 顺序进入下一题；若已到末题则返回 next_question=null。

该机制保证了：

1. 同一题可配置多条条件分支。
2. 分支优先级可控，行为可预测。
3. 新增条件类型时只需扩展规则匹配器，不必改前端流程。

### 1.7.3 提交时如何保证路径与答案合法

submit 接口不是直接落库，而是先进行完整校验：

1. 检查问卷状态是否可提交（已发布、未过期）。
2. 基于用户作答顺序重新执行一次跳转，计算“真实可达题目路径”。
3. 校验提交答案必须来自该路径，防止伪造跳题提交。
4. 按题型做值校验：
   - 单选值必须在 options 中。
   - 多选数量满足 min_select/max_select。
   - 填空数字满足 min/max 与 is_integer。

5. 校验必答题是否全部作答。
6. 若问卷不允许重复提交，则用 survey_id + respondent_id 判重。
7. 全部通过后写入 answers 集合并记录 submitted_at。

该流程可以同时防止：

1. 绕过前端校验直接提交非法值。
2. 提交未经过路径的题目答案。
3. 同一用户重复提交（在关闭重复提交时）。

### 1.7.4 统计模块如何聚合

统计接口分整卷和单题两个粒度：

1. 整卷统计读取该 survey 的所有提交，计算 submission_count 与每题统计结果。
2. 单选题聚合 option_counts。
3. 多选题累计每个选项被选择次数。
4. 数字填空题计算平均值与样本值列表。
5. 提交记录摘要支持显示 respondent_username；当 is_anonymous=true 时用户名返回 null。

这样可以同时满足：

1. 业务分析需求（分题统计）。
2. 隐私要求（匿名不泄露用户名）。
3. 前端展示需求（整卷总览 + 单题下钻）。

### 1.7.5 【第二阶段新增】题库版本链如何实现

题库采用版本链模式管理题目变更历史。每条题库记录包含 chain_id、parent_id、version、is_latest 四个版本字段，形成有向链：

1. 用户首次保存题目到题库时，创建版本 v1，chain_id 等于自身 _id，is_latest=true。
2. 用户点击「新版本」时，系统将当前最新版本的 is_latest 置为 false，然后插入一条新记录，chain_id 不变，parent_id 指向前一版本，version 递增。
3. 用户恢复旧版本时，将旧版本的 is_latest 标志切换为 true，当前最新版本的 is_latest 切换为 false，不创建新版本记录。
4. 删除某个版本时，若被删版本是最新版，前一版本自动恢复 is_latest=true。

导入到问卷时，系统在 questions 文档中记录 bank_item_id、bank_chain_id、bank_version，用于追踪来源。后续查询使用情况和跨问卷统计时，通过 bank_chain_id 关联所有使用该题链的问卷。

共享机制在版本链级别生效：共享操作将目标用户 ID 写入链上所有版本的 shared_with 数组，新版本自动继承。

该设计保证了：

1. 修改题库题目不影响已导入问卷（独立副本）。
2. 完整保留所有历史版本，支持查看与恢复。
3. 同一题目的不同版本可同时被不同问卷使用。
4. 跨问卷统计可聚合同一题链在所有问卷中的回答数据。

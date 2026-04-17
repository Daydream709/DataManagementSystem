import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass
class HttpResult:
    status: int
    body: dict[str, Any] | None
    raw: str


class ApiClient:
    def __init__(self, base_url: str, verbose: bool = False):
        self.base_url = base_url.rstrip("/")
        self.verbose = verbose
        self.request_no = 0

    @staticmethod
    def _mask_token(token: str | None) -> str:
        if not token:
            return ""
        if len(token) <= 10:
            return "***"
        return f"{token[:8]}...{token[-4:]}"

    def request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        token: str | None = None,
    ) -> HttpResult:
        self.request_no += 1
        req_no = self.request_no
        url = f"{self.base_url}{path}"
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        if self.verbose:
            print(f"\n[HTTP-{req_no}] {method} {path}")
            if token:
                print(f"  token: Bearer {self._mask_token(token)}")
            if payload is not None:
                print("  request:", json.dumps(payload, ensure_ascii=False))
            else:
                print("  request: <empty>")

        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")

        request = urllib.request.Request(url=url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                raw = response.read().decode("utf-8")
                body = json.loads(raw) if raw else None
                if self.verbose:
                    print(f"  response_status: {response.status}")
                    print("  response_body:", raw if raw else "<empty>")
                return HttpResult(status=response.status, body=body, raw=raw)
        except urllib.error.HTTPError as error:
            raw = error.read().decode("utf-8")
            body = None
            try:
                body = json.loads(raw) if raw else None
            except Exception:
                pass
            if self.verbose:
                print(f"  response_status: {error.code}")
                print("  response_body:", raw if raw else "<empty>")
            return HttpResult(status=error.code, body=body, raw=raw)


class TestRunner:
    def __init__(self, base_url: str):
        self.client = ApiClient(base_url, verbose=True)
        self.passed = 0
        self.failed = 0
        self.current_case: dict[str, Any] | None = None
        self.case_results: list[dict[str, Any]] = []

        self.seed = int(time.time())
        self.owner_username = f"owner_{self.seed}"
        self.user1_username = f"user1_{self.seed}"
        self.user2_username = f"user2_{self.seed}"
        self.auth_username = f"auth_{self.seed}"
        self.sharee_username = f"sharee_{self.seed}"
        self.password = "Passw0rd!"

        self.owner_token = ""
        self.user1_token = ""
        self.user2_token = ""
        self.sharee_token = ""

        self.survey_id = ""
        self.survey_slug = ""
        self.q1_id = ""
        self.q2_id = ""
        self.q3_id = ""

        # 第二阶段题库测试数据
        self.bank_item_id = ""
        self.bank_chain_id = ""
        self.bank_v2_id = ""
        self.bank_v1_id = ""
        self.sharee_survey_id = ""

    def check(self, condition: bool, message: str) -> None:
        if condition:
            self.passed += 1
            if self.current_case is not None:
                self.current_case["passed"] += 1
            print(f"[PASS] {message}")
            return
        self.failed += 1
        if self.current_case is not None:
            self.current_case["failed"] += 1
        print(f"[FAIL] {message}")

    def run_case(self, case_id: str, case_title: str, case_func: Any) -> None:
        print(f"\n=== {case_id} {case_title} ===")
        case = {"id": case_id, "title": case_title, "passed": 0, "failed": 0}
        self.case_results.append(case)
        self.current_case = case
        case_func()
        status = "PASS" if case["failed"] == 0 else "FAIL"
        print(f"--- {case_id} 结果: {status} (通过 {case['passed']} / 失败 {case['failed']}) ---")
        self.current_case = None

    def print_case_summary(self) -> None:
        print("\n=== 用例通过总结 ===")
        passed_cases: list[str] = []
        failed_cases: list[str] = []
        for case in self.case_results:
            case_name = f"{case['id']} {case['title']}"
            if case["failed"] == 0:
                passed_cases.append(case_name)
                status = "通过"
            else:
                failed_cases.append(case_name)
                status = "失败"
            print(f"- {case_name}: {status} (通过 {case['passed']} / 失败 {case['failed']})")

        print("通过样例:")
        if passed_cases:
            for item in passed_cases:
                print(f"- {item}")
        else:
            print("- 无")

        if failed_cases:
            print("未通过样例:")
            for item in failed_cases:
                print(f"- {item}")

    def check_success(self, result: HttpResult, message: str, expected_status: int = 200) -> None:
        ok = (
            result.status == expected_status
            and isinstance(result.body, dict)
            and result.body.get("code") == 0
        )
        if not ok:
            print("  -> status:", result.status)
            print("  -> body:", result.raw)
        self.check(ok, message)

    def check_fail(self, result: HttpResult, message: str) -> None:
        failed = result.status >= 400 and isinstance(result.body, dict) and result.body.get("code") == 1
        if not failed:
            print("  -> status:", result.status)
            print("  -> body:", result.raw)
        self.check(failed, message)

    def register_and_login(self, username: str) -> str:
        register_res = self.client.request(
            "POST",
            "/auth/register",
            payload={"username": username, "password": self.password},
        )
        self.check_success(register_res, f"注册用户 {username}", expected_status=201)

        login_res = self.client.request(
            "POST",
            "/auth/login",
            payload={"username": username, "password": self.password},
        )
        self.check_success(login_res, f"登录用户 {username}")
        token = ""
        if isinstance(login_res.body, dict):
            token = (login_res.body.get("data") or {}).get("token", "")
        self.check(bool(token), f"获取 {username} token")
        return token

    def tc_01_auth_register_login(self) -> None:
        register_payload = {"username": self.auth_username, "password": self.password}
        register_res = self.client.request("POST", "/auth/register", payload=register_payload)
        self.check_success(register_res, "新用户注册成功", expected_status=201)

        login_res = self.client.request("POST", "/auth/login", payload=register_payload)
        self.check_success(login_res, "新用户登录成功")
        token = ""
        if isinstance(login_res.body, dict):
            token = (login_res.body.get("data") or {}).get("token", "")
        self.check(bool(token), "新用户登录后返回 token")

        duplicate_register_res = self.client.request("POST", "/auth/register", payload=register_payload)
        self.check_fail(duplicate_register_res, "重复用户名注册被拦截")

        short_username_res = self.client.request(
            "POST",
            "/auth/register",
            payload={"username": "ab", "password": self.password},
        )
        self.check_fail(short_username_res, "用户名长度小于 3 被拦截")

        short_password_res = self.client.request(
            "POST",
            "/auth/register",
            payload={"username": f"weak_{self.seed}", "password": "12345"},
        )
        self.check_fail(short_password_res, "密码长度小于 6 被拦截")

        wrong_password_res = self.client.request(
            "POST",
            "/auth/login",
            payload={"username": self.auth_username, "password": "wrong_pass_123"},
        )
        self.check_fail(wrong_password_res, "错误密码登录被拦截")

        user_not_found_res = self.client.request(
            "POST",
            "/auth/login",
            payload={"username": f"missing_{self.seed}", "password": self.password},
        )
        self.check_fail(user_not_found_res, "不存在用户登录被拦截")

    def tc_02_create_survey(self) -> None:
        create_payload = {
            "title": "自动化测试问卷",
            "description": "API 自动测试",
            "allow_anonymous": True,
            "allow_multiple_submissions": False,
        }
        create_res = self.client.request("POST", "/surveys", payload=create_payload, token=self.owner_token)
        self.check_success(create_res, "创建问卷成功", expected_status=201)

        if isinstance(create_res.body, dict):
            data = create_res.body.get("data") or {}
            self.survey_id = data.get("id", "")
            self.survey_slug = data.get("slug", "")
        self.check(bool(self.survey_id), "创建返回 survey_id")
        self.check(bool(self.survey_slug), "创建返回 survey_slug")

        list_res = self.client.request("GET", "/surveys", token=self.owner_token)
        self.check_success(list_res, "查询问卷列表成功")
        surveys = []
        if isinstance(list_res.body, dict):
            surveys = list_res.body.get("data") or []
        found = any(item.get("id") == self.survey_id and item.get("status") == "draft" for item in surveys)
        self.check(found, "新问卷出现在列表且状态为 draft")

    def tc_03_add_questions(self) -> None:
        q1 = {
            "order": 1,
            "type": "single_choice",
            "title": "你是否每天运动？",
            "required": True,
            "options": [{"key": "A", "label": "是"}, {"key": "B", "label": "否"}],
        }
        q2 = {
            "order": 2,
            "type": "multi_choice",
            "title": "你常做的运动项目？",
            "required": True,
            "options": [
                {"key": "A", "label": "跑步"},
                {"key": "B", "label": "游泳"},
                {"key": "C", "label": "健身"},
            ],
            "validation": {"min_select": 1, "max_select": 2},
        }
        q3 = {
            "order": 3,
            "type": "fill_blank",
            "title": "你每周运动几次？",
            "required": True,
            "validation": {"value_type": "number", "min_value": 0, "max_value": 120, "is_integer": True},
        }

        q1_res = self.client.request(
            "POST", f"/surveys/{self.survey_id}/questions", payload=q1, token=self.owner_token
        )
        q2_res = self.client.request(
            "POST", f"/surveys/{self.survey_id}/questions", payload=q2, token=self.owner_token
        )
        q3_res = self.client.request(
            "POST", f"/surveys/{self.survey_id}/questions", payload=q3, token=self.owner_token
        )
        self.check_success(q1_res, "创建 Q1 成功", expected_status=201)
        self.check_success(q2_res, "创建 Q2 成功", expected_status=201)
        self.check_success(q3_res, "创建 Q3 成功", expected_status=201)

        if isinstance(q1_res.body, dict):
            self.q1_id = (q1_res.body.get("data") or {}).get("id", "")
        if isinstance(q2_res.body, dict):
            self.q2_id = (q2_res.body.get("data") or {}).get("id", "")
        if isinstance(q3_res.body, dict):
            self.q3_id = (q3_res.body.get("data") or {}).get("id", "")

        self.check(bool(self.q1_id and self.q2_id and self.q3_id), "三道题目 ID 均获取成功")

        list_res = self.client.request("GET", f"/surveys/{self.survey_id}/questions", token=self.owner_token)
        self.check_success(list_res, "查询题目列表成功")
        questions = []
        if isinstance(list_res.body, dict):
            questions = list_res.body.get("data") or []
        orders = [item.get("order") for item in questions]
        self.check(orders == sorted(orders) and len(orders) == 3, "题目按 order 返回且数量为 3")

    def tc_04_jump_logic(self) -> None:
        rule_a = {
            "question_id": self.q1_id,
            "rule_type": "single_choice",
            "operator": "eq",
            "value": "A",
            "target_question_id": self.q3_id,
            "priority": 1,
        }
        rule_b = {
            "question_id": self.q1_id,
            "rule_type": "single_choice",
            "operator": "eq",
            "value": "B",
            "target_question_id": self.q2_id,
            "priority": 2,
        }
        rule_a_res = self.client.request(
            "POST", f"/surveys/{self.survey_id}/jump-rules", payload=rule_a, token=self.owner_token
        )
        rule_b_res = self.client.request(
            "POST", f"/surveys/{self.survey_id}/jump-rules", payload=rule_b, token=self.owner_token
        )
        self.check_success(rule_a_res, "创建规则 A->Q3 成功", expected_status=201)
        self.check_success(rule_b_res, "创建规则 B->Q2 成功", expected_status=201)

        publish_res = self.client.request(
            "POST", f"/surveys/{self.survey_id}/publish", token=self.owner_token
        )
        self.check_success(publish_res, "发布问卷成功")

        next_a_res = self.client.request(
            "POST",
            f"/public/surveys/{self.survey_slug}/next-question",
            payload={"current_question_id": self.q1_id, "answer": "A"},
            token=self.user1_token,
        )
        self.check_success(next_a_res, "Q1=A 计算下一题成功")
        next_a_id = None
        if isinstance(next_a_res.body, dict):
            next_a_id = ((next_a_res.body.get("data") or {}).get("next_question") or {}).get("id")
        self.check(next_a_id == self.q3_id, "Q1=A 跳转到 Q3")

        next_b_res = self.client.request(
            "POST",
            f"/public/surveys/{self.survey_slug}/next-question",
            payload={"current_question_id": self.q1_id, "answer": "B"},
            token=self.user1_token,
        )
        self.check_success(next_b_res, "Q1=B 计算下一题成功")
        next_b_id = None
        if isinstance(next_b_res.body, dict):
            next_b_id = ((next_b_res.body.get("data") or {}).get("next_question") or {}).get("id")
        self.check(next_b_id == self.q2_id, "Q1=B 跳转到 Q2")

    def tc_05_validation(self) -> None:
        missing_required_payload = {
            "is_anonymous": False,
            "answers": [{"question_id": self.q1_id, "answer": "A"}],
        }
        missing_required_res = self.client.request(
            "POST",
            f"/public/surveys/{self.survey_slug}/submit",
            payload=missing_required_payload,
            token=self.user1_token,
        )
        self.check_fail(missing_required_res, "缺少必答题时提交被拦截")

        multi_over_payload = {
            "is_anonymous": False,
            "answers": [
                {"question_id": self.q1_id, "answer": "B"},
                {"question_id": self.q2_id, "answer": ["A", "B", "C"]},
                {"question_id": self.q3_id, "answer": 10},
            ],
        }
        multi_over_res = self.client.request(
            "POST",
            f"/public/surveys/{self.survey_slug}/submit",
            payload=multi_over_payload,
            token=self.user1_token,
        )
        self.check_fail(multi_over_res, "多选超出 max_select 被拦截")

        integer_fail_res = self.client.request(
            "POST",
            f"/public/surveys/{self.survey_slug}/next-question",
            payload={"current_question_id": self.q3_id, "answer": 3.14},
            token=self.user1_token,
        )
        self.check_fail(integer_fail_res, "数字题整数校验拦截 3.14")

    def tc_06_submit(self) -> None:
        submit_user1 = {
            "is_anonymous": False,
            "answers": [
                {"question_id": self.q1_id, "answer": "A"},
                {"question_id": self.q3_id, "answer": 20},
            ],
        }
        submit_user1_res = self.client.request(
            "POST",
            f"/public/surveys/{self.survey_slug}/submit",
            payload=submit_user1,
            token=self.user1_token,
        )
        self.check_success(submit_user1_res, "用户1提交成功", expected_status=201)

        submit_user2 = {
            "is_anonymous": True,
            "answers": [
                {"question_id": self.q1_id, "answer": "B"},
                {"question_id": self.q2_id, "answer": ["A", "B"]},
                {"question_id": self.q3_id, "answer": 22},
            ],
        }
        submit_user2_res = self.client.request(
            "POST",
            f"/public/surveys/{self.survey_slug}/submit",
            payload=submit_user2,
            token=self.user2_token,
        )
        self.check_success(submit_user2_res, "用户2匿名提交成功", expected_status=201)

        duplicate_submit_res = self.client.request(
            "POST",
            f"/public/surveys/{self.survey_slug}/submit",
            payload=submit_user1,
            token=self.user1_token,
        )
        self.check_fail(duplicate_submit_res, "重复提交被拦截（allow_multiple_submissions=false）")

    def tc_07_stats(self) -> None:
        survey_stats_res = self.client.request(
            "GET", f"/surveys/{self.survey_id}/stats", token=self.owner_token
        )
        self.check_success(survey_stats_res, "整卷统计获取成功")

        stats_data = (
            (survey_stats_res.body or {}).get("data") if isinstance(survey_stats_res.body, dict) else {}
        )
        questions = stats_data.get("questions", []) if isinstance(stats_data, dict) else []
        self.check((stats_data or {}).get("submission_count") == 2, "提交总数为 2")

        q1_stats = next((item for item in questions if item.get("question_id") == self.q1_id), None)
        q2_stats = next((item for item in questions if item.get("question_id") == self.q2_id), None)
        q3_stats = next((item for item in questions if item.get("question_id") == self.q3_id), None)

        self.check(bool(q1_stats and q2_stats and q3_stats), "三道题统计均存在")
        if q1_stats:
            option_counts = q1_stats.get("option_counts", {})
            self.check(option_counts.get("A") == 1 and option_counts.get("B") == 1, "单选统计 A=1, B=1")
        if q2_stats:
            option_counts = q2_stats.get("option_counts", {})
            self.check(
                option_counts.get("A") == 1 and option_counts.get("B") == 1 and option_counts.get("C") == 0,
                "多选统计 A=1, B=1, C=0",
            )
        if q3_stats:
            average = q3_stats.get("average")
            self.check(average == 21, "数字填空平均值为 21")

        single_q_stats_res = self.client.request(
            "GET", f"/questions/{self.q1_id}/stats", token=self.owner_token
        )
        self.check_success(single_q_stats_res, "单题统计获取成功")

    def tc_08_non_draft_edit_block(self) -> None:
        create_question_payload = {
            "order": 10,
            "type": "single_choice",
            "title": "发布后不应允许新增",
            "required": False,
            "options": [{"key": "A", "label": "是"}, {"key": "B", "label": "否"}],
        }
        blocked_res = self.client.request(
            "POST",
            f"/surveys/{self.survey_id}/questions",
            payload=create_question_payload,
            token=self.owner_token,
        )
        self.check_fail(blocked_res, "发布后新增题目被拦截")

    def tc_09_no_back_to_draft(self) -> None:
        draft_res = self.client.request("POST", f"/surveys/{self.survey_id}/draft", token=self.owner_token)
        self.check_fail(draft_res, "发布状态调用 /draft 被拦截")

    def tc_10_username_visibility(self) -> None:
        stats_res = self.client.request("GET", f"/surveys/{self.survey_id}/stats", token=self.owner_token)
        self.check_success(stats_res, "整卷统计再次获取成功")

        submissions = []
        if isinstance(stats_res.body, dict):
            submissions = (stats_res.body.get("data") or {}).get("submissions") or []

        self.check(len(submissions) == 2, "submissions 返回 2 条记录")
        anonymous_ok = False
        named_ok = False
        for item in submissions:
            if item.get("is_anonymous"):
                anonymous_ok = item.get("respondent_username") is None
            else:
                named_ok = bool(item.get("respondent_username"))
        self.check(anonymous_ok, "匿名提交不返回用户名")
        self.check(named_ok, "非匿名提交返回用户名")

    # ── 第二阶段新增用例 TC-11 ~ TC-18 ──

    def tc_11_bank_save_and_list(self) -> None:
        payload = {
            "type": "single_choice",
            "title": "你的年级",
            "options": [
                {"key": "A", "label": "大一"},
                {"key": "B", "label": "大二"},
                {"key": "C", "label": "大三"},
                {"key": "D", "label": "大四"},
            ],
            "version_note": "初始版本",
        }
        save_res = self.client.request("POST", "/question-bank", payload=payload, token=self.owner_token)
        self.check_success(save_res, "保存题目到题库成功", expected_status=201)

        data: dict[str, Any] = {}
        if isinstance(save_res.body, dict):
            data = save_res.body.get("data") or {}
        self.bank_item_id = data.get("id", "")
        self.bank_chain_id = data.get("chain_id", "")
        self.bank_v1_id = self.bank_item_id
        self.check(bool(self.bank_item_id), "题库条目 ID 获取成功")
        self.check(data.get("version") == 1, "初始版本号为 1")
        self.check(data.get("is_latest") is True, "初始版本 is_latest=true")

        list_res = self.client.request("GET", "/question-bank", token=self.owner_token)
        self.check_success(list_res, "查询我的题库成功")
        items: list[Any] = []
        if isinstance(list_res.body, dict):
            items = list_res.body.get("data") or []
        found = any(item.get("id") == self.bank_item_id for item in items)
        self.check(found, "题库列表中包含刚保存的题目")

    def tc_12_bank_import_to_survey(self) -> None:
        create_res = self.client.request("POST", "/surveys", payload={
            "title": "题库导入测试问卷",
            "description": "第二阶段测试",
            "allow_anonymous": True,
            "allow_multiple_submissions": True,
        }, token=self.owner_token)
        self.check_success(create_res, "创建导入目标问卷成功", expected_status=201)
        import_survey_id = ""
        if isinstance(create_res.body, dict):
            import_survey_id = ((create_res.body.get("data") or {}).get("id", ""))
        self.check(bool(import_survey_id), "导入目标问卷 ID 获取成功")

        import_res = self.client.request(
            "POST",
            f"/surveys/{import_survey_id}/questions/import",
            payload={"item_id": self.bank_item_id, "order": 1, "required": True},
            token=self.owner_token,
        )
        self.check_success(import_res, "从题库导入题目成功", expected_status=201)

        imported: dict[str, Any] = {}
        if isinstance(import_res.body, dict):
            imported = import_res.body.get("data") or {}
        self.check(imported.get("title") == "你的年级", "导入题目标题一致")
        self.check(imported.get("bank_item_id") == self.bank_item_id, "导入记录 bank_item_id 非空")
        self.check(imported.get("bank_version") == 1, "导入记录 bank_version=1")

        q_list_res = self.client.request("GET", f"/surveys/{import_survey_id}/questions", token=self.owner_token)
        self.check_success(q_list_res, "查询导入后题目列表成功")

    def tc_13_bank_version_management(self) -> None:
        new_ver_res = self.client.request(
            "POST",
            f"/question-bank/{self.bank_item_id}/new-version",
            payload={"title": "你的年级（含研究生）", "version_note": "增加研究生选项"},
            token=self.owner_token,
        )
        self.check_success(new_ver_res, "创建新版本 v2 成功", expected_status=201)
        new_ver_data: dict[str, Any] = {}
        if isinstance(new_ver_res.body, dict):
            new_ver_data = new_ver_res.body.get("data") or {}
        self.bank_v2_id = new_ver_data.get("id", "")
        self.check(new_ver_data.get("version") == 2, "新版本号为 2")
        self.check(new_ver_data.get("title") == "你的年级（含研究生）", "新版本标题正确")
        self.check(new_ver_data.get("is_latest") is True, "新版本 is_latest=true")

        versions_res = self.client.request("GET", f"/question-bank/{self.bank_item_id}/versions", token=self.owner_token)
        self.check_success(versions_res, "查询版本历史成功")
        versions: list[Any] = []
        if isinstance(versions_res.body, dict):
            versions = versions_res.body.get("data") or []
        self.check(len(versions) == 2, "版本历史返回 2 条记录")

        # 切换回 v1（直接切换，不创建新版本）
        restore_res = self.client.request(
            "POST",
            f"/question-bank/{self.bank_v2_id}/restore",
            payload={"version_item_id": self.bank_v1_id},
            token=self.owner_token,
        )
        self.check_success(restore_res, "切换回 v1 成功")
        restore_data: dict[str, Any] = {}
        if isinstance(restore_res.body, dict):
            restore_data = restore_res.body.get("data") or {}
        self.check(restore_data.get("version") == 1, "切换后版本号仍为 1（未创建新版本）")
        self.check(restore_data.get("title") == "你的年级", "切换后标题与 v1 一致")
        self.check(restore_data.get("is_latest") is True, "切换后 v1 的 is_latest=true")

        # 验证版本总数不变
        versions_res2 = self.client.request("GET", f"/question-bank/{self.bank_item_id}/versions", token=self.owner_token)
        self.check_success(versions_res2, "切换后再次查询版本历史成功")
        versions2: list[Any] = []
        if isinstance(versions_res2.body, dict):
            versions2 = versions_res2.body.get("data") or []
        self.check(len(versions2) == 2, "切换后版本总数仍为 2（未新增版本）")

        # 切换回 v2
        restore_res2 = self.client.request(
            "POST",
            f"/question-bank/{self.bank_v1_id}/restore",
            payload={"version_item_id": self.bank_v2_id},
            token=self.owner_token,
        )
        self.check_success(restore_res2, "切换回 v2 成功")
        restore_data2: dict[str, Any] = {}
        if isinstance(restore_res2.body, dict):
            restore_data2 = restore_res2.body.get("data") or {}
        self.check(restore_data2.get("version") == 2, "切换回 v2 后版本号为 2")
        self.check(restore_data2.get("is_latest") is True, "v2 的 is_latest=true")

    def tc_14_bank_share(self) -> None:
        share_res = self.client.request(
            "POST",
            f"/question-bank/{self.bank_item_id}/share",
            payload={"usernames": [self.sharee_username]},
            token=self.owner_token,
        )
        self.check_success(share_res, "共享题目给用户E成功")

        shared_list_res = self.client.request("GET", "/question-bank/shared", token=self.sharee_token)
        self.check_success(shared_list_res, "用户E查询共享题目成功")
        shared_items: list[Any] = []
        if isinstance(shared_list_res.body, dict):
            shared_items = shared_list_res.body.get("data") or []
        found = any(item.get("title") == "你的年级" for item in shared_items)
        self.check(found, "用户E在共享列表中看到该题目")

        create_res = self.client.request("POST", "/surveys", payload={
            "title": "用户E的问卷",
            "allow_anonymous": True,
            "allow_multiple_submissions": True,
        }, token=self.sharee_token)
        if isinstance(create_res.body, dict):
            self.sharee_survey_id = ((create_res.body.get("data") or {}).get("id", ""))

        import_res = self.client.request(
            "POST",
            f"/surveys/{self.sharee_survey_id}/questions/import",
            payload={"item_id": self.bank_item_id, "order": 1, "required": False},
            token=self.sharee_token,
        )
        self.check_success(import_res, "用户E导入共享题目成功", expected_status=201)

    def tc_15_bank_usage(self) -> None:
        usage_res = self.client.request(
            "GET",
            f"/question-bank/{self.bank_item_id}/usage",
            token=self.owner_token,
        )
        self.check_success(usage_res, "查询题库使用情况成功")
        usage_data: list[Any] = []
        if isinstance(usage_res.body, dict):
            raw = usage_res.body.get("data")
            if isinstance(raw, list):
                usage_data = raw
        self.check(isinstance(usage_data, list), "使用情况返回数组")
        self.check(len(usage_data) >= 1, "至少有一份问卷使用了该题目")
        if usage_data:
            first = usage_data[0]
            self.check("survey_id" in first and "survey_title" in first, "使用情况包含 survey_id 和 survey_title")
            self.check("bank_version" in first, "使用情况包含 bank_version")

    def tc_16_bank_cross_stats(self) -> None:
        cross_res = self.client.request(
            "GET",
            f"/question-bank/{self.bank_item_id}/cross-stats",
            token=self.owner_token,
        )
        self.check_success(cross_res, "查询跨问卷统计成功")
        cross_data: dict[str, Any] = {}
        if isinstance(cross_res.body, dict):
            cross_data = cross_res.body.get("data") or {}
        self.check(isinstance(cross_data.get("total_surveys"), int), "total_surveys 为整数")
        self.check(isinstance(cross_data.get("total_submissions"), int), "total_submissions 为整数")
        self.check("stats" in cross_data, "返回 stats 字段")

    def tc_17_bank_version_isolation(self) -> None:
        new_ver_res = self.client.request(
            "POST",
            f"/question-bank/{self.bank_item_id}/new-version",
            payload={"title": "版本隔离测试标题", "version_note": "测试版本隔离"},
            token=self.owner_token,
        )
        self.check_success(new_ver_res, "创建版本隔离测试的新版本成功", expected_status=201)
        new_ver_data: dict[str, Any] = {}
        if isinstance(new_ver_res.body, dict):
            new_ver_data = new_ver_res.body.get("data") or {}
        self.check(new_ver_data.get("title") == "版本隔离测试标题", "新版本标题已修改")

        q_list_res = self.client.request("GET", f"/surveys/{self.survey_id}/questions", token=self.owner_token)
        self.check_success(q_list_res, "查询已发布问卷题目成功")
        questions: list[Any] = []
        if isinstance(q_list_res.body, dict):
            questions = q_list_res.body.get("data") or []
        affected = any(q.get("title") == "版本隔离测试标题" for q in questions)
        self.check(not affected, "已发布问卷题目不受题库修改影响（版本隔离）")

    def cleanup(self) -> None:
        if not self.survey_id:
            return
        delete_res = self.client.request("DELETE", f"/surveys/{self.survey_id}", token=self.owner_token)
        self.check_success(delete_res, "清理测试问卷成功")
        if self.sharee_survey_id:
            cleanup_res = self.client.request("DELETE", f"/surveys/{self.sharee_survey_id}", token=self.sharee_token)
            self.check_success(cleanup_res, "清理用户E测试问卷成功")

    def run(self) -> int:
        print("=== API 自动化测试开始 ===")
        print("base_url:", self.client.base_url)

        print("\n=== 初始化测试账号 ===")

        self.owner_token = self.register_and_login(self.owner_username)
        self.user1_token = self.register_and_login(self.user1_username)
        self.user2_token = self.register_and_login(self.user2_username)
        self.sharee_token = self.register_and_login(self.sharee_username)

        self.run_case("TC-01", "用户注册与登录", self.tc_01_auth_register_login)
        self.run_case("TC-02", "创建问卷", self.tc_02_create_survey)
        self.run_case("TC-03", "添加题目", self.tc_03_add_questions)
        self.run_case("TC-04", "跳转逻辑", self.tc_04_jump_logic)
        self.run_case("TC-05", "校验拦截", self.tc_05_validation)
        self.run_case("TC-06", "提交流程", self.tc_06_submit)
        self.run_case("TC-07", "统计结果", self.tc_07_stats)
        self.run_case("TC-08", "非草稿编辑拦截", self.tc_08_non_draft_edit_block)
        self.run_case("TC-09", "发布关闭不可回草稿", self.tc_09_no_back_to_draft)
        self.run_case("TC-10", "统计用户名可见性", self.tc_10_username_visibility)

        # 第二阶段新增用例
        self.run_case("TC-11", "【第二阶段】题库保存与列表", self.tc_11_bank_save_and_list)
        self.run_case("TC-12", "【第二阶段】从题库导入到问卷", self.tc_12_bank_import_to_survey)
        self.run_case("TC-13", "【第二阶段】题库版本管理", self.tc_13_bank_version_management)
        self.run_case("TC-14", "【第二阶段】题目共享", self.tc_14_bank_share)
        self.run_case("TC-15", "【第二阶段】题库使用情况查询", self.tc_15_bank_usage)
        self.run_case("TC-16", "【第二阶段】跨问卷统计", self.tc_16_bank_cross_stats)
        self.run_case("TC-17", "【第二阶段】已发布问卷不受影响", self.tc_17_bank_version_isolation)
        self.cleanup()

        self.print_case_summary()

        print("\n=== API 自动化测试结束 ===")
        print(f"通过: {self.passed} 失败: {self.failed}")
        return 0 if self.failed == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="问卷系统 API 自动化测试")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/api", help="API 基地址")
    args = parser.parse_args()

    runner = TestRunner(args.base_url)
    return runner.run()


if __name__ == "__main__":
    raise SystemExit(main())

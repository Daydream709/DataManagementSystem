from datetime import datetime, timezone
from statistics import mean
from typing import Any
from uuid import uuid4

from bson import ObjectId
from django.conf import settings
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from ..mongodb import get_collection
from ..utils.helpers import serialize_doc, to_object_id


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _to_aware_datetime(value: Any) -> datetime | None:
    if value is None:
        return None

    dt_value = value
    if isinstance(dt_value, str):
        normalized = dt_value.replace("Z", "+00:00")
        try:
            dt_value = datetime.fromisoformat(normalized)
        except ValueError:
            return None

    if not isinstance(dt_value, datetime):
        return None

    if dt_value.tzinfo is None or dt_value.tzinfo.utcoffset(dt_value) is None:
        return dt_value.replace(tzinfo=timezone.utc)

    return dt_value


def _build_link(slug: str) -> str:
    return f"{settings.FRONTEND_BASE_URL.rstrip('/')}/survey/{slug}"


def _get_owned_survey(owner_id: str, survey_id: str) -> dict[str, Any]:
    surveys = get_collection("surveys")
    survey = surveys.find_one(
        {"_id": to_object_id(survey_id, "survey_id"), "owner_id": to_object_id(owner_id, "owner_id")}
    )
    if not survey:
        raise NotFound("问卷不存在")
    return survey


def _ensure_draft_editable(survey: dict[str, Any], action: str) -> None:
    if survey.get("status") != "draft":
        raise ValidationError(f"问卷当前状态不允许{action}，仅草稿状态可操作")


def _question_to_response(question: dict[str, Any]) -> dict[str, Any]:
    item = serialize_doc(question)
    item["id"] = item.pop("_id")
    return item


def _survey_to_response(survey: dict[str, Any]) -> dict[str, Any]:
    item = serialize_doc(survey)
    item["id"] = item.pop("_id")
    item["link"] = _build_link(item["slug"])
    return item


def create_survey(owner_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    surveys = get_collection("surveys")
    now = _now()
    data = {
        "owner_id": to_object_id(owner_id, "owner_id"),
        "title": payload["title"],
        "description": payload.get("description") or "",
        "allow_anonymous": bool(payload.get("allow_anonymous", False)),
        "allow_multiple_submissions": bool(payload.get("allow_multiple_submissions", True)),
        "deadline": payload.get("deadline"),
        "status": "draft",
        "slug": uuid4().hex[:12],
        "created_at": now,
        "updated_at": now,
    }
    result = surveys.insert_one(data)
    data["_id"] = result.inserted_id
    return _survey_to_response(data)


def list_surveys(owner_id: str) -> list[dict[str, Any]]:
    surveys = get_collection("surveys")
    docs = surveys.find({"owner_id": to_object_id(owner_id, "owner_id")}).sort("created_at", -1)
    return [_survey_to_response(doc) for doc in docs]


def get_survey(owner_id: str, survey_id: str) -> dict[str, Any]:
    survey = _get_owned_survey(owner_id, survey_id)
    return _survey_to_response(survey)


def update_survey(owner_id: str, survey_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    surveys = get_collection("surveys")
    survey = _get_owned_survey(owner_id, survey_id)
    _ensure_draft_editable(survey, "编辑问卷")

    update_payload = {**payload, "updated_at": _now()}
    surveys.update_one(
        {"_id": to_object_id(survey_id, "survey_id"), "owner_id": to_object_id(owner_id, "owner_id")},
        {"$set": update_payload},
    )
    return get_survey(owner_id, survey_id)


def delete_survey(owner_id: str, survey_id: str) -> None:
    surveys = get_collection("surveys")
    questions = get_collection("questions")
    jump_rules = get_collection("jump_rules")
    answers = get_collection("answers")

    survey = _get_owned_survey(owner_id, survey_id)
    survey_oid = survey["_id"]

    surveys.delete_one({"_id": survey_oid})
    questions.delete_many({"survey_id": survey_oid})
    jump_rules.delete_many({"survey_id": survey_oid})
    answers.delete_many({"survey_id": survey_oid})


def update_survey_status(owner_id: str, survey_id: str, status: str) -> dict[str, Any]:
    surveys = get_collection("surveys")
    if status not in ("published", "closed", "draft"):
        raise ValidationError("无效状态")

    survey = _get_owned_survey(owner_id, survey_id)
    current_status = survey.get("status")

    if status == "draft" and current_status in ("published", "closed"):
        raise ValidationError("发布和关闭状态不能改回草稿")

    if current_status == status:
        return _survey_to_response(survey)

    surveys.update_one(
        {"_id": survey["_id"]},
        {"$set": {"status": status, "updated_at": _now()}},
    )
    updated = surveys.find_one({"_id": survey["_id"]})
    if not updated:
        raise NotFound("问卷状态更新后未找到")
    return _survey_to_response(updated)


def list_questions(owner_id: str, survey_id: str) -> list[dict[str, Any]]:
    _get_owned_survey(owner_id, survey_id)
    questions = get_collection("questions")
    docs = questions.find(
        {"survey_id": to_object_id(survey_id, "survey_id"), "owner_id": to_object_id(owner_id, "owner_id")}
    ).sort("order", 1)
    return [_question_to_response(doc) for doc in docs]


def _ensure_order_unique(survey_oid: ObjectId, order: int, exclude_id: ObjectId | None = None) -> None:
    questions = get_collection("questions")
    query = {"survey_id": survey_oid, "order": order}
    if exclude_id:
        query["_id"] = {"$ne": exclude_id}
    existing = questions.find_one(query)
    if existing:
        raise ValidationError({"order": "该顺序已被使用"})


def create_question(owner_id: str, survey_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    survey = _get_owned_survey(owner_id, survey_id)
    _ensure_draft_editable(survey, "新增题目")

    survey_oid = survey["_id"]
    _ensure_order_unique(survey_oid, payload["order"])

    questions = get_collection("questions")
    now = _now()
    doc = {
        "survey_id": survey_oid,
        "owner_id": to_object_id(owner_id, "owner_id"),
        "order": payload["order"],
        "type": payload["type"],
        "title": payload["title"],
        "required": bool(payload.get("required", False)),
        "options": payload.get("options", []),
        "validation": payload.get("validation", {}),
        "created_at": now,
        "updated_at": now,
    }
    result = questions.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _question_to_response(doc)


def _get_owned_question(owner_id: str, question_id: str) -> dict[str, Any]:
    questions = get_collection("questions")
    doc = questions.find_one(
        {"_id": to_object_id(question_id, "question_id"), "owner_id": to_object_id(owner_id, "owner_id")}
    )
    if not doc:
        raise NotFound("题目不存在")
    return doc


def update_question(owner_id: str, question_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    questions = get_collection("questions")
    surveys = get_collection("surveys")
    current = _get_owned_question(owner_id, question_id)
    survey = surveys.find_one({"_id": current["survey_id"], "owner_id": to_object_id(owner_id, "owner_id")})
    if not survey:
        raise NotFound("问卷不存在")
    _ensure_draft_editable(survey, "编辑题目")

    merged = {**current, **payload}
    if "order" in payload:
        _ensure_order_unique(current["survey_id"], payload["order"], exclude_id=current["_id"])

    update_data = {
        "order": merged["order"],
        "type": merged["type"],
        "title": merged["title"],
        "required": merged.get("required", False),
        "options": merged.get("options", []),
        "validation": merged.get("validation", {}),
        "updated_at": _now(),
    }
    questions.update_one({"_id": current["_id"]}, {"$set": update_data})

    updated = questions.find_one({"_id": current["_id"]})
    if not updated:
        raise NotFound("题目更新后未找到")
    return _question_to_response(updated)


def delete_question(owner_id: str, question_id: str) -> None:
    questions = get_collection("questions")
    jump_rules = get_collection("jump_rules")
    surveys = get_collection("surveys")
    question = _get_owned_question(owner_id, question_id)
    survey = surveys.find_one({"_id": question["survey_id"], "owner_id": to_object_id(owner_id, "owner_id")})
    if not survey:
        raise NotFound("问卷不存在")
    _ensure_draft_editable(survey, "删除题目")

    questions.delete_one({"_id": question["_id"]})
    jump_rules.delete_many(
        {"$or": [{"question_id": question["_id"]}, {"target_question_id": question["_id"]}]}
    )


def _normalize_rule_type(question: dict[str, Any]) -> str:
    if question["type"] == "single_choice":
        return "single_choice"
    if question["type"] == "multi_choice":
        return "multi_choice"
    if question["type"] == "fill_blank" and question.get("validation", {}).get("value_type") == "number":
        return "number"
    raise ValidationError("当前题目类型不支持配置该跳转规则")


def create_jump_rule(owner_id: str, survey_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    survey = _get_owned_survey(owner_id, survey_id)
    _ensure_draft_editable(survey, "配置跳转规则")
    question = _get_owned_question(owner_id, payload["question_id"])
    if str(question["survey_id"]) != survey_id:
        raise PermissionDenied("题目不属于当前问卷")

    expected_rule_type = _normalize_rule_type(question)
    if payload["rule_type"] != expected_rule_type:
        raise ValidationError({"rule_type": f"该题目仅支持 {expected_rule_type} 规则"})

    target_question_oid = None
    if payload.get("target_question_id"):
        target_question = _get_owned_question(owner_id, payload["target_question_id"])
        if target_question["survey_id"] != question["survey_id"]:
            raise ValidationError({"target_question_id": "目标题目不属于当前问卷"})
        target_question_oid = target_question["_id"]

    jump_rules = get_collection("jump_rules")
    now = _now()
    doc = {
        "survey_id": question["survey_id"],
        "owner_id": to_object_id(owner_id, "owner_id"),
        "question_id": question["_id"],
        "rule_type": payload["rule_type"],
        "operator": payload["operator"],
        "value": payload["value"],
        "target_question_id": target_question_oid,
        "target_order": payload.get("target_order"),
        "priority": payload.get("priority", 100),
        "created_at": now,
    }
    result = jump_rules.insert_one(doc)
    doc["_id"] = result.inserted_id
    item = serialize_doc(doc)
    item["id"] = item.pop("_id")
    return item


def list_jump_rules(owner_id: str, survey_id: str) -> list[dict[str, Any]]:
    _get_owned_survey(owner_id, survey_id)
    jump_rules = get_collection("jump_rules")
    docs = jump_rules.find(
        {"survey_id": to_object_id(survey_id, "survey_id"), "owner_id": to_object_id(owner_id, "owner_id")}
    ).sort("priority", 1)
    result = []
    for doc in docs:
        item = serialize_doc(doc)
        item["id"] = item.pop("_id")
        result.append(item)
    return result


def delete_jump_rule(owner_id: str, rule_id: str) -> None:
    jump_rules = get_collection("jump_rules")
    surveys = get_collection("surveys")
    rule = jump_rules.find_one(
        {"_id": to_object_id(rule_id, "rule_id"), "owner_id": to_object_id(owner_id, "owner_id")}
    )
    if not rule:
        raise NotFound("跳转规则不存在")
    survey = surveys.find_one({"_id": rule["survey_id"], "owner_id": to_object_id(owner_id, "owner_id")})
    if not survey:
        raise NotFound("问卷不存在")
    _ensure_draft_editable(survey, "删除跳转规则")
    jump_rules.delete_one({"_id": rule["_id"]})


def _survey_public_base(slug: str) -> dict[str, Any]:
    surveys = get_collection("surveys")
    survey = surveys.find_one({"slug": slug})
    if not survey:
        raise NotFound("问卷不存在")

    if survey["status"] != "published":
        raise ValidationError("问卷未发布或已关闭")

    deadline = _to_aware_datetime(survey.get("deadline"))
    if deadline and deadline < _now():
        raise ValidationError("问卷已过截止时间")
    return survey


def get_public_survey(slug: str) -> dict[str, Any]:
    survey = _survey_public_base(slug)
    questions = get_collection("questions")
    jump_rules = get_collection("jump_rules")

    question_docs = list(questions.find({"survey_id": survey["_id"]}).sort("order", 1))
    rule_docs = list(jump_rules.find({"survey_id": survey["_id"]}).sort("priority", 1))

    response = _survey_to_response(survey)
    response["questions"] = [_question_to_response(doc) for doc in question_docs]
    response["jump_rules"] = [serialize_doc(doc) for doc in rule_docs]
    return response


def _evaluate_rule(operator: str, expected: Any, answer: Any) -> bool:
    if answer is None:
        return False

    if operator == "eq":
        return answer == expected

    if operator == "in":
        if isinstance(expected, list):
            return answer in expected
        return False

    if operator == "contains_any":
        if not isinstance(answer, list) or not isinstance(expected, list):
            return False
        return any(item in answer for item in expected)

    if operator == "contains_all":
        if not isinstance(answer, list) or not isinstance(expected, list):
            return False
        return all(item in answer for item in expected)

    if operator in ("gt", "gte", "lt", "lte"):
        try:
            answer_num = float(answer)
            expected_num = float(expected)
        except Exception:
            return False
        if operator == "gt":
            return answer_num > expected_num
        if operator == "gte":
            return answer_num >= expected_num
        if operator == "lt":
            return answer_num < expected_num
        return answer_num <= expected_num

    if operator == "range":
        if not isinstance(expected, list) or len(expected) != 2:
            return False
        try:
            answer_num = float(answer)
            left = float(expected[0])
            right = float(expected[1])
        except Exception:
            return False
        return left <= answer_num <= right

    return False


def _validate_single_choice(question: dict[str, Any], answer: Any) -> None:
    valid_keys = {opt["key"] for opt in question.get("options", [])}
    if not isinstance(answer, str) or answer not in valid_keys:
        raise ValidationError({str(question["_id"]): "单选答案非法"})


def _validate_multi_choice(question: dict[str, Any], answer: Any) -> None:
    if not isinstance(answer, list):
        raise ValidationError({str(question["_id"]): "多选答案必须是数组"})

    valid_keys = {opt["key"] for opt in question.get("options", [])}
    if len(set(answer)) != len(answer):
        raise ValidationError({str(question["_id"]): "多选答案不允许重复"})

    for item in answer:
        if item not in valid_keys:
            raise ValidationError({str(question["_id"]): f"非法选项: {item}"})

    rule = question.get("validation", {})
    if "min_select" in rule and len(answer) < int(rule["min_select"]):
        raise ValidationError({str(question["_id"]): f"至少选择 {rule['min_select']} 个"})
    if "max_select" in rule and len(answer) > int(rule["max_select"]):
        raise ValidationError({str(question["_id"]): f"最多选择 {rule['max_select']} 个"})


def _validate_fill_blank(question: dict[str, Any], answer: Any) -> None:
    rule = question.get("validation", {})
    value_type = rule.get("value_type")

    if value_type == "text":
        if not isinstance(answer, str):
            raise ValidationError({str(question["_id"]): "文本填空答案必须是字符串"})
        min_length = rule.get("min_length")
        max_length = rule.get("max_length")
        if min_length is not None and len(answer) < int(min_length):
            raise ValidationError({str(question["_id"]): f"文本长度不能小于 {min_length}"})
        if max_length is not None and len(answer) > int(max_length):
            raise ValidationError({str(question["_id"]): f"文本长度不能大于 {max_length}"})
        return

    if value_type == "number":
        try:
            num = float(answer)
        except Exception as exc:
            raise ValidationError({str(question["_id"]): "数字填空答案必须是数字"}) from exc

        if rule.get("is_integer") and not float(num).is_integer():
            raise ValidationError({str(question["_id"]): "该题要求整数"})

        min_value = rule.get("min_value")
        max_value = rule.get("max_value")
        if min_value is not None and num < float(min_value):
            raise ValidationError({str(question["_id"]): f"数值不能小于 {min_value}"})
        if max_value is not None and num > float(max_value):
            raise ValidationError({str(question["_id"]): f"数值不能大于 {max_value}"})
        return

    raise ValidationError({str(question["_id"]): "填空题缺少有效 value_type"})


def _validate_answer(question: dict[str, Any], answer: Any) -> None:
    q_type = question["type"]
    if q_type == "single_choice":
        _validate_single_choice(question, answer)
        return
    if q_type == "multi_choice":
        _validate_multi_choice(question, answer)
        return
    if q_type == "fill_blank":
        _validate_fill_blank(question, answer)
        return
    raise ValidationError({str(question["_id"]): "未知题型"})


def _next_by_order(sorted_questions: list[dict[str, Any]], current_order: int) -> dict[str, Any] | None:
    for q in sorted_questions:
        if q["order"] > current_order:
            return q
    return None


def _resolve_next_question(
    current_question: dict[str, Any],
    answer: Any,
    sorted_questions: list[dict[str, Any]],
    question_map: dict[str, dict[str, Any]],
    rule_map: dict[str, list[dict[str, Any]]],
) -> dict[str, Any] | None:
    qid = str(current_question["_id"])
    rules = rule_map.get(qid, [])

    for rule in rules:
        if _evaluate_rule(rule["operator"], rule["value"], answer):
            if rule.get("target_question_id"):
                target_id = str(rule["target_question_id"])
                target = question_map.get(target_id)
                if target:
                    return target
            if rule.get("target_order") is not None:
                for q in sorted_questions:
                    if q["order"] == rule["target_order"]:
                        return q
    return _next_by_order(sorted_questions, current_question["order"])


def compute_next_question(slug: str, current_question_id: str, answer: Any) -> dict[str, Any]:
    survey = _survey_public_base(slug)
    questions = get_collection("questions")
    jump_rules = get_collection("jump_rules")

    sorted_questions = list(questions.find({"survey_id": survey["_id"]}).sort("order", 1))
    question_map = {str(q["_id"]): q for q in sorted_questions}
    current = question_map.get(current_question_id)
    if not current:
        raise NotFound("当前题目不存在")

    if answer is not None and answer != "" and answer != []:
        _validate_answer(current, answer)

    rules = list(jump_rules.find({"survey_id": survey["_id"]}).sort("priority", 1))
    rule_map: dict[str, list[dict[str, Any]]] = {}
    for item in rules:
        key = str(item["question_id"])
        rule_map.setdefault(key, []).append(item)

    next_question = _resolve_next_question(current, answer, sorted_questions, question_map, rule_map)
    if not next_question:
        return {"next_question": None}

    return {
        "next_question": _question_to_response(next_question),
    }


def submit_survey(slug: str, respondent_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    survey = _survey_public_base(slug)
    if not respondent_id:
        raise ValidationError("填写问卷前请先登录")

    respondent_oid = to_object_id(respondent_id, "respondent_id")

    if payload.get("is_anonymous") and not survey.get("allow_anonymous"):
        raise ValidationError({"is_anonymous": "该问卷不允许匿名提交"})

    questions_col = get_collection("questions")
    rules_col = get_collection("jump_rules")
    answers_col = get_collection("answers")

    if not survey.get("allow_multiple_submissions", True):
        existing = answers_col.find_one({"survey_id": survey["_id"], "respondent_id": respondent_oid})
        if existing:
            raise ValidationError("该问卷不允许同一用户重复填写")

    sorted_questions = list(questions_col.find({"survey_id": survey["_id"]}).sort("order", 1))
    if not sorted_questions:
        raise ValidationError("问卷暂无题目，无法提交")

    question_map = {str(q["_id"]): q for q in sorted_questions}

    rules = list(rules_col.find({"survey_id": survey["_id"]}).sort("priority", 1))
    rule_map: dict[str, list[dict[str, Any]]] = {}
    for item in rules:
        rule_map.setdefault(str(item["question_id"]), []).append(item)

    raw_answer_map: dict[str, Any] = {}
    for item in payload["answers"]:
        qid = item["question_id"]
        if qid not in question_map:
            raise ValidationError({qid: "题目不属于当前问卷"})
        raw_answer_map[qid] = item.get("answer")

    # 根据跳转规则计算本次填写真实访问路径，并在路径上执行必答/合法性校验。
    traversed: list[dict[str, Any]] = []
    visited: set[str] = set()
    current = sorted_questions[0]

    while current and str(current["_id"]) not in visited:
        qid = str(current["_id"])
        visited.add(qid)
        traversed.append(current)

        answer = raw_answer_map.get(qid)
        if current.get("required") and (answer is None or answer == "" or answer == []):
            raise ValidationError({qid: "必答题未作答"})

        if answer is not None and answer != "" and answer != []:
            _validate_answer(current, answer)

        current = _resolve_next_question(current, answer, sorted_questions, question_map, rule_map)

    traversed_ids = {str(q["_id"]) for q in traversed}
    for qid in raw_answer_map:
        if qid not in traversed_ids:
            raise ValidationError({qid: "该题在当前跳转路径中不可达"})

    answer_list = []
    for q in traversed:
        qid = str(q["_id"])
        if qid in raw_answer_map:
            answer_list.append(
                {
                    "question_id": q["_id"],
                    "answer": raw_answer_map[qid],
                    "answered_at": _now(),
                }
            )

    doc = {
        "survey_id": survey["_id"],
        # 需要登录后填写：始终保留提交者ID，匿名仅控制展示层是否暴露身份。
        "respondent_id": respondent_oid,
        "is_anonymous": bool(payload.get("is_anonymous", False)),
        "answers": answer_list,
        "submitted_at": _now(),
        "client_fingerprint": payload.get("client_fingerprint") or None,
    }
    result = answers_col.insert_one(doc)
    return {
        "submission_id": str(result.inserted_id),
        "survey_id": str(survey["_id"]),
        "submitted_at": doc["submitted_at"].isoformat(),
    }


def _extract_question_answer(submission: dict[str, Any], question_oid: ObjectId) -> Any:
    for item in submission.get("answers", []):
        if item["question_id"] == question_oid:
            return item.get("answer")
    return None


def _stats_for_question(question: dict[str, Any], submissions: list[dict[str, Any]]) -> dict[str, Any]:
    qid = str(question["_id"])
    base = {
        "question_id": qid,
        "title": question["title"],
        "type": question["type"],
    }

    if question["type"] == "single_choice":
        counts = {opt["key"]: 0 for opt in question.get("options", [])}
        answered_count = 0
        for sub in submissions:
            answer = _extract_question_answer(sub, question["_id"])
            if isinstance(answer, str):
                answered_count += 1
                if answer in counts:
                    counts[answer] += 1
        base["option_counts"] = counts
        base["total_answered"] = answered_count
        return base

    if question["type"] == "multi_choice":
        counts = {opt["key"]: 0 for opt in question.get("options", [])}
        for sub in submissions:
            answer = _extract_question_answer(sub, question["_id"])
            if isinstance(answer, list):
                for item in answer:
                    if item in counts:
                        counts[item] += 1
        base["option_counts"] = counts
        return base

    if question["type"] == "fill_blank":
        values = []
        for sub in submissions:
            answer = _extract_question_answer(sub, question["_id"])
            if answer is not None and answer != "":
                values.append(answer)

        base["values"] = values
        if question.get("validation", {}).get("value_type") == "number":
            numeric_values = []
            for value in values:
                try:
                    numeric_values.append(float(value))
                except Exception:
                    continue
            base["average"] = mean(numeric_values) if numeric_values else None
        return base

    return base


def get_survey_stats(owner_id: str, survey_id: str) -> dict[str, Any]:
    survey = _get_owned_survey(owner_id, survey_id)
    questions_col = get_collection("questions")
    answers_col = get_collection("answers")

    question_docs = list(questions_col.find({"survey_id": survey["_id"]}).sort("order", 1))
    submissions = list(answers_col.find({"survey_id": survey["_id"]}))

    question_stats = [_stats_for_question(question, submissions) for question in question_docs]

    return {
        "survey": _survey_to_response(survey),
        "submission_count": len(submissions),
        "questions": question_stats,
    }


def get_question_stats(owner_id: str, question_id: str) -> dict[str, Any]:
    question = _get_owned_question(owner_id, question_id)
    answers_col = get_collection("answers")
    submissions = list(answers_col.find({"survey_id": question["survey_id"]}))
    return _stats_for_question(question, submissions)

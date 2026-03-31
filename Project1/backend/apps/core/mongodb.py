from threading import RLock

from django.conf import settings
from pymongo import ASCENDING, MongoClient

_client = None
_db = None
_lock = RLock()
_indexes_ready = False


def get_db():
    global _client, _db
    if _db is None:
        with _lock:
            if _db is None:
                _client = MongoClient(
                    settings.MONGODB["URI"],
                    serverSelectionTimeoutMS=3000,
                    connectTimeoutMS=3000,
                )
                _db = _client[settings.MONGODB["DB_NAME"]]
    return _db


def get_collection(name: str):
    return get_db()[name]


def ensure_indexes() -> None:
    global _indexes_ready
    if _indexes_ready:
        return

    with _lock:
        if _indexes_ready:
            return

        users = get_collection("users")
        surveys = get_collection("surveys")
        questions = get_collection("questions")
        jump_rules = get_collection("jump_rules")
        answers = get_collection("answers")

        users.create_index([("username", ASCENDING)], unique=True, name="uq_username")
        surveys.create_index([("owner_id", ASCENDING), ("created_at", ASCENDING)], name="idx_survey_owner")
        surveys.create_index([("slug", ASCENDING)], unique=True, name="uq_survey_slug")
        questions.create_index(
            [("survey_id", ASCENDING), ("order", ASCENDING)], name="idx_question_survey_order"
        )
        questions.create_index(
            [("owner_id", ASCENDING), ("survey_id", ASCENDING)], name="idx_question_owner_survey"
        )
        jump_rules.create_index(
            [("survey_id", ASCENDING), ("question_id", ASCENDING), ("priority", ASCENDING)],
            name="idx_rule_survey_question_priority",
        )
        answers.create_index(
            [("survey_id", ASCENDING), ("submitted_at", ASCENDING)], name="idx_answer_survey_submitted"
        )
        answers.create_index([("respondent_id", ASCENDING)], name="idx_answer_respondent")
        answers.create_index(
            [("survey_id", ASCENDING), ("respondent_id", ASCENDING)],
            name="idx_answer_survey_respondent",
        )

        _indexes_ready = True

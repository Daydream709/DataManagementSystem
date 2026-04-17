from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from .mongodb import get_collection
from .serializers import (
    JumpRuleCreateSerializer,
    LoginSerializer,
    NextQuestionSerializer,
    QuestionBankCreateSerializer,
    QuestionBankImportSerializer,
    QuestionBankNewVersionSerializer,
    QuestionBankRestoreSerializer,
    QuestionBankShareSerializer,
    QuestionBankUpdateSerializer,
    QuestionCreateSerializer,
    QuestionUpdateSerializer,
    RegisterSerializer,
    SubmitAnswerSerializer,
    SurveyCreateSerializer,
    SurveyUpdateSerializer,
)
from .services.auth_service import login_user, register_user
from .services.survey_service import (
    compute_next_question,
    create_jump_rule,
    create_new_bank_version,
    create_question,
    create_question_bank_item,
    create_survey,
    delete_jump_rule,
    delete_question,
    delete_question_bank_chain,
    delete_question_bank_item,
    delete_survey,
    get_bank_cross_stats,
    get_bank_item_usage,
    get_public_survey,
    get_question_stats,
    get_survey,
    get_survey_stats,
    import_question_from_bank,
    list_bank_versions,
    list_jump_rules,
    list_question_bank,
    list_questions,
    list_shared_bank_items,
    list_surveys,
    restore_bank_version,
    share_bank_item,
    submit_survey,
    update_bank_item,
    update_question,
    update_survey,
    update_survey_status,
)
from .utils.helpers import to_object_id
from .utils.response import ok


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = register_user(**serializer.validated_data)
        return ok(data=data, message="注册成功", status_code=201)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = login_user(**serializer.validated_data)
        return ok(data=data, message="登录成功")


class SurveyListCreateView(APIView):
    def get(self, request):
        data = list_surveys(request.user.id)
        return ok(data=data)

    def post(self, request):
        serializer = SurveyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = create_survey(request.user.id, serializer.validated_data)
        return ok(data=data, message="创建成功", status_code=201)


class SurveyDetailView(APIView):
    def get(self, request, survey_id: str):
        data = get_survey(request.user.id, survey_id)
        return ok(data=data)

    def put(self, request, survey_id: str):
        serializer = SurveyUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = update_survey(request.user.id, survey_id, serializer.validated_data)
        return ok(data=data, message="更新成功")

    def delete(self, request, survey_id: str):
        delete_survey(request.user.id, survey_id)
        return ok(message="删除成功")


class SurveyPublishView(APIView):
    def post(self, request, survey_id: str):
        data = update_survey_status(request.user.id, survey_id, "published")
        return ok(data=data, message="发布成功")


class SurveyCloseView(APIView):
    def post(self, request, survey_id: str):
        data = update_survey_status(request.user.id, survey_id, "closed")
        return ok(data=data, message="关闭成功")


class SurveyDraftView(APIView):
    def post(self, request, survey_id: str):
        data = update_survey_status(request.user.id, survey_id, "draft")
        return ok(data=data, message="已设为草稿")


class QuestionListCreateView(APIView):
    def get(self, request, survey_id: str):
        data = list_questions(request.user.id, survey_id)
        return ok(data=data)

    def post(self, request, survey_id: str):
        serializer = QuestionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = create_question(request.user.id, survey_id, serializer.validated_data)
        return ok(data=data, message="题目创建成功", status_code=201)


class QuestionDetailView(APIView):
    def put(self, request, question_id: str):
        questions = get_collection("questions")
        current = questions.find_one(
            {
                "_id": to_object_id(question_id, "question_id"),
                "owner_id": to_object_id(request.user.id, "owner_id"),
            }
        )
        context = (
            {
                "current_type": current["type"],
                "current_options": current.get("options", []),
                "current_validation": current.get("validation", {}),
            }
            if current
            else {}
        )

        serializer = QuestionUpdateSerializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        data = update_question(request.user.id, question_id, serializer.validated_data)
        return ok(data=data, message="题目更新成功")

    def delete(self, request, question_id: str):
        delete_question(request.user.id, question_id)
        return ok(message="题目删除成功")


class JumpRuleListCreateView(APIView):
    def get(self, request, survey_id: str):
        data = list_jump_rules(request.user.id, survey_id)
        return ok(data=data)

    def post(self, request, survey_id: str):
        serializer = JumpRuleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = create_jump_rule(request.user.id, survey_id, serializer.validated_data)
        return ok(data=data, message="跳转规则创建成功", status_code=201)


class JumpRuleDetailView(APIView):
    def delete(self, request, rule_id: str):
        delete_jump_rule(request.user.id, rule_id)
        return ok(message="跳转规则删除成功")


class PublicSurveyView(APIView):
    def get(self, request, slug: str):
        data = get_public_survey(slug)
        return ok(data=data)


class NextQuestionView(APIView):
    def post(self, request, slug: str):
        serializer = NextQuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = compute_next_question(
            slug, serializer.validated_data["current_question_id"], serializer.validated_data.get("answer")
        )
        return ok(data=data)


class SubmitSurveyView(APIView):
    def post(self, request, slug: str):
        serializer = SubmitAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = submit_survey(slug, request.user.id, serializer.validated_data)
        return ok(data=data, message="提交成功", status_code=201)


class SurveyStatsView(APIView):
    def get(self, request, survey_id: str):
        data = get_survey_stats(request.user.id, survey_id)
        return ok(data=data)


class QuestionStatsView(APIView):
    def get(self, request, question_id: str):
        data = get_question_stats(request.user.id, question_id)
        return ok(data=data)


class QuestionBankListCreateView(APIView):
    def get(self, request):
        data = list_question_bank(request.user.id)
        return ok(data=data)

    def post(self, request):
        serializer = QuestionBankCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = create_question_bank_item(request.user.id, serializer.validated_data)
        return ok(data=data, message="已保存到题库", status_code=201)


class QuestionBankDetailView(APIView):
    def delete(self, request, item_id: str):
        delete_chain = request.query_params.get("chain") == "true"
        if delete_chain:
            delete_question_bank_chain(request.user.id, item_id)
        else:
            delete_question_bank_item(request.user.id, item_id)
        return ok(message="已删除")


class QuestionImportView(APIView):
    def post(self, request, survey_id: str):
        serializer = QuestionBankImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = import_question_from_bank(request.user.id, survey_id, serializer.validated_data)
        return ok(data=data, message="从题库导入成功", status_code=201)


class QuestionBankNewVersionView(APIView):
    def post(self, request, item_id: str):
        serializer = QuestionBankNewVersionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = create_new_bank_version(request.user.id, item_id, serializer.validated_data)
        return ok(data=data, message="新版本已创建", status_code=201)


class QuestionBankVersionsView(APIView):
    def get(self, request, item_id: str):
        data = list_bank_versions(request.user.id, item_id)
        return ok(data=data)


class QuestionBankRestoreView(APIView):
    def post(self, request, item_id: str):
        serializer = QuestionBankRestoreSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = restore_bank_version(request.user.id, item_id, serializer.validated_data["version_item_id"])
        return ok(data=data, message="版本已恢复")


class QuestionBankShareView(APIView):
    def post(self, request, item_id: str):
        serializer = QuestionBankShareSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = share_bank_item(request.user.id, item_id, serializer.validated_data["usernames"])
        return ok(data=data, message="共享成功")


class QuestionBankSharedView(APIView):
    def get(self, request):
        data = list_shared_bank_items(request.user.id)
        return ok(data=data)


class QuestionBankUsageView(APIView):
    def get(self, request, item_id: str):
        data = get_bank_item_usage(request.user.id, item_id)
        return ok(data=data)


class QuestionBankUpdateView(APIView):
    def put(self, request, item_id: str):
        serializer = QuestionBankUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = update_bank_item(request.user.id, item_id, serializer.validated_data)
        return ok(data=data, message="题库题目已更新")


class QuestionBankCrossStatsView(APIView):
    def get(self, request, item_id: str):
        version_item_id = request.query_params.get("version_item_id")
        data = get_bank_cross_stats(request.user.id, item_id, version_item_id)
        return ok(data=data)

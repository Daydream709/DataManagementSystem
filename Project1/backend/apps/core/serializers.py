from datetime import datetime

from rest_framework import serializers

QUESTION_TYPES = (
    "single_choice",
    "multi_choice",
    "fill_blank",
)

FILL_VALUE_TYPES = (
    "text",
    "number",
)

RULE_OPERATORS = (
    "eq",
    "in",
    "contains_any",
    "contains_all",
    "gt",
    "gte",
    "lt",
    "lte",
    "range",
)


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(min_length=3, max_length=50)
    password = serializers.CharField(min_length=6, max_length=128)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class SurveyCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True, default="")
    allow_anonymous = serializers.BooleanField(default=False)
    allow_multiple_submissions = serializers.BooleanField(default=True)
    deadline = serializers.DateTimeField(required=False, allow_null=True)


class SurveyUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200, required=False)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    allow_anonymous = serializers.BooleanField(required=False)
    allow_multiple_submissions = serializers.BooleanField(required=False)
    deadline = serializers.DateTimeField(required=False, allow_null=True)


class OptionSerializer(serializers.Serializer):
    key = serializers.CharField(max_length=30)
    label = serializers.CharField(max_length=200)


class QuestionCreateSerializer(serializers.Serializer):
    order = serializers.IntegerField(min_value=1)
    type = serializers.ChoiceField(choices=QUESTION_TYPES)
    title = serializers.CharField(max_length=300)
    required = serializers.BooleanField(default=False)
    options = OptionSerializer(many=True, required=False)
    validation = serializers.DictField(required=False)

    def validate(self, attrs):
        q_type = attrs["type"]
        options = attrs.get("options", [])
        validation = attrs.get("validation", {})

        if q_type in ("single_choice", "multi_choice"):
            if len(options) < 2:
                raise serializers.ValidationError({"options": "选择题至少需要2个选项"})
            option_keys = [item["key"] for item in options]
            if len(option_keys) != len(set(option_keys)):
                raise serializers.ValidationError({"options": "选项 key 不可重复"})

        if q_type == "single_choice" and validation:
            raise serializers.ValidationError({"validation": "单选题不支持额外 validation 字段"})

        if q_type == "multi_choice":
            min_select = validation.get("min_select")
            max_select = validation.get("max_select")
            if min_select is not None and min_select < 0:
                raise serializers.ValidationError({"validation": "min_select 不能小于 0"})
            if max_select is not None and max_select < 1:
                raise serializers.ValidationError({"validation": "max_select 必须大于等于 1"})
            if min_select is not None and max_select is not None and min_select > max_select:
                raise serializers.ValidationError({"validation": "min_select 不能大于 max_select"})

        if q_type == "fill_blank":
            value_type = validation.get("value_type")
            if value_type not in FILL_VALUE_TYPES:
                raise serializers.ValidationError({"validation": "填空题必须设置 value_type=text/number"})

            if value_type == "text":
                min_length = validation.get("min_length")
                max_length = validation.get("max_length")
                if min_length is not None and min_length < 0:
                    raise serializers.ValidationError({"validation": "min_length 不能小于 0"})
                if max_length is not None and max_length < 1:
                    raise serializers.ValidationError({"validation": "max_length 必须大于等于 1"})
                if min_length is not None and max_length is not None and min_length > max_length:
                    raise serializers.ValidationError({"validation": "min_length 不能大于 max_length"})

            if value_type == "number":
                min_value = validation.get("min_value")
                max_value = validation.get("max_value")
                if min_value is not None and max_value is not None and min_value > max_value:
                    raise serializers.ValidationError({"validation": "min_value 不能大于 max_value"})
                if "is_integer" in validation and not isinstance(validation["is_integer"], bool):
                    raise serializers.ValidationError({"validation": "is_integer 必须是布尔值"})

        return attrs


class QuestionUpdateSerializer(QuestionCreateSerializer):
    order = serializers.IntegerField(min_value=1, required=False)
    type = serializers.ChoiceField(choices=QUESTION_TYPES, required=False)
    title = serializers.CharField(max_length=300, required=False)
    required = serializers.BooleanField(required=False)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("至少提供一个更新字段")
        if "type" not in attrs:
            attrs["type"] = self.context.get("current_type")
        if "options" not in attrs:
            attrs["options"] = self.context.get("current_options", [])
        if "validation" not in attrs:
            attrs["validation"] = self.context.get("current_validation", {})
        return super().validate(attrs)


class JumpRuleCreateSerializer(serializers.Serializer):
    question_id = serializers.CharField()
    rule_type = serializers.ChoiceField(choices=("single_choice", "multi_choice", "number"))
    operator = serializers.ChoiceField(choices=RULE_OPERATORS)
    value = serializers.JSONField()
    target_question_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    target_order = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    priority = serializers.IntegerField(required=False, min_value=1, default=100)

    def validate(self, attrs):
        if not attrs.get("target_question_id") and not attrs.get("target_order"):
            raise serializers.ValidationError("target_question_id 和 target_order 至少提供一个")

        rule_type = attrs["rule_type"]
        operator = attrs["operator"]

        if rule_type == "single_choice" and operator not in ("eq", "in"):
            raise serializers.ValidationError("单选跳转仅支持 eq/in")

        if rule_type == "multi_choice" and operator not in ("contains_any", "contains_all", "in"):
            raise serializers.ValidationError("多选跳转仅支持 contains_any/contains_all/in")

        if rule_type == "number" and operator not in ("eq", "gt", "gte", "lt", "lte", "range"):
            raise serializers.ValidationError("数字跳转仅支持 eq/gt/gte/lt/lte/range")

        return attrs


class AnswerItemSerializer(serializers.Serializer):
    question_id = serializers.CharField()
    answer = serializers.JSONField(required=False, allow_null=True)


class SubmitAnswerSerializer(serializers.Serializer):
    is_anonymous = serializers.BooleanField(default=False)
    answers = AnswerItemSerializer(many=True, min_length=1)
    client_fingerprint = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class NextQuestionSerializer(serializers.Serializer):
    current_question_id = serializers.CharField()
    answer = serializers.JSONField(required=False, allow_null=True)


class QuestionBankCreateSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=QUESTION_TYPES)
    title = serializers.CharField(max_length=300)
    options = OptionSerializer(many=True, required=False)
    validation = serializers.DictField(required=False)
    version_note = serializers.CharField(max_length=500, required=False, allow_blank=True)

    def validate(self, attrs):
        q_type = attrs["type"]
        options = attrs.get("options", [])
        validation = attrs.get("validation", {})

        if q_type in ("single_choice", "multi_choice"):
            if len(options) < 2:
                raise serializers.ValidationError({"options": "选择题至少需要2个选项"})
            option_keys = [item["key"] for item in options]
            if len(option_keys) != len(set(option_keys)):
                raise serializers.ValidationError({"options": "选项 key 不可重复"})

        if q_type == "fill_blank":
            value_type = validation.get("value_type")
            if value_type not in FILL_VALUE_TYPES:
                raise serializers.ValidationError({"validation": "填空题必须设置 value_type=text/number"})

        return attrs


class QuestionBankImportSerializer(serializers.Serializer):
    item_id = serializers.CharField()
    order = serializers.IntegerField(min_value=1)
    required = serializers.BooleanField(required=False, default=False)


class QuestionBankNewVersionSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=300, required=False)
    type = serializers.ChoiceField(choices=QUESTION_TYPES, required=False)
    options = OptionSerializer(many=True, required=False)
    validation = serializers.DictField(required=False)
    version_note = serializers.CharField(max_length=500, required=False, allow_blank=True)


class QuestionBankShareSerializer(serializers.Serializer):
    usernames = serializers.ListField(child=serializers.CharField(max_length=50), min_length=1)


class QuestionBankRestoreSerializer(serializers.Serializer):
    version_item_id = serializers.CharField()



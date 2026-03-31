from django.urls import path

from .views import (
    JumpRuleDetailView,
    JumpRuleListCreateView,
    LoginView,
    NextQuestionView,
    PublicSurveyView,
    QuestionDetailView,
    QuestionListCreateView,
    QuestionStatsView,
    RegisterView,
    SubmitSurveyView,
    SurveyCloseView,
    SurveyDetailView,
    SurveyDraftView,
    SurveyListCreateView,
    SurveyPublishView,
    SurveyStatsView,
)

urlpatterns = [
    path("auth/register", RegisterView.as_view()),
    path("auth/login", LoginView.as_view()),
    path("surveys", SurveyListCreateView.as_view()),
    path("surveys/<str:survey_id>", SurveyDetailView.as_view()),
    path("surveys/<str:survey_id>/publish", SurveyPublishView.as_view()),
    path("surveys/<str:survey_id>/close", SurveyCloseView.as_view()),
    path("surveys/<str:survey_id>/draft", SurveyDraftView.as_view()),
    path("surveys/<str:survey_id>/questions", QuestionListCreateView.as_view()),
    path("questions/<str:question_id>", QuestionDetailView.as_view()),
    path("surveys/<str:survey_id>/jump-rules", JumpRuleListCreateView.as_view()),
    path("jump-rules/<str:rule_id>", JumpRuleDetailView.as_view()),
    path("public/surveys/<str:slug>", PublicSurveyView.as_view()),
    path("public/surveys/<str:slug>/next-question", NextQuestionView.as_view()),
    path("public/surveys/<str:slug>/submit", SubmitSurveyView.as_view()),
    path("surveys/<str:survey_id>/stats", SurveyStatsView.as_view()),
    path("questions/<str:question_id>/stats", QuestionStatsView.as_view()),
]

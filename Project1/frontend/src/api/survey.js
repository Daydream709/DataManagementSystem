import http from "./http";

export const listSurveysApi = () => http.get("/surveys");
export const createSurveyApi = (payload) => http.post("/surveys", payload);
export const getSurveyApi = (id) => http.get(`/surveys/${id}`);
export const updateSurveyApi = (id, payload) => http.put(`/surveys/${id}`, payload);
export const deleteSurveyApi = (id) => http.delete(`/surveys/${id}`);

export const publishSurveyApi = (id) => http.post(`/surveys/${id}/publish`);
export const closeSurveyApi = (id) => http.post(`/surveys/${id}/close`);
export const draftSurveyApi = (id) => http.post(`/surveys/${id}/draft`);

export const listQuestionsApi = (surveyId) => http.get(`/surveys/${surveyId}/questions`);
export const createQuestionApi = (surveyId, payload) => http.post(`/surveys/${surveyId}/questions`, payload);
export const updateQuestionApi = (questionId, payload) => http.put(`/questions/${questionId}`, payload);
export const deleteQuestionApi = (questionId) => http.delete(`/questions/${questionId}`);

export const listJumpRulesApi = (surveyId) => http.get(`/surveys/${surveyId}/jump-rules`);
export const createJumpRuleApi = (surveyId, payload) => http.post(`/surveys/${surveyId}/jump-rules`, payload);
export const deleteJumpRuleApi = (ruleId) => http.delete(`/jump-rules/${ruleId}`);

export const getPublicSurveyApi = (slug) => http.get(`/public/surveys/${slug}`);
export const nextQuestionApi = (slug, payload) => http.post(`/public/surveys/${slug}/next-question`, payload);
export const submitSurveyApi = (slug, payload) => http.post(`/public/surveys/${slug}/submit`, payload);

export const getSurveyStatsApi = (surveyId) => http.get(`/surveys/${surveyId}/stats`);
export const getQuestionStatsApi = (questionId) => http.get(`/questions/${questionId}/stats`);

// Question Bank - Basic
export const listQuestionBankApi = () => http.get("/question-bank");
export const createQuestionBankApi = (payload) => http.post("/question-bank", payload);
export const deleteQuestionBankApi = (itemId, chain = false) =>
  http.delete(`/question-bank/${itemId}${chain ? "?chain=true" : ""}`);

// Question Bank - Versions
export const listBankVersionsApi = (itemId) => http.get(`/question-bank/${itemId}/versions`);
export const createNewBankVersionApi = (itemId, payload) =>
  http.post(`/question-bank/${itemId}/new-version`, payload);
export const restoreBankVersionApi = (itemId, versionItemId) =>
  http.post(`/question-bank/${itemId}/restore`, { version_item_id: versionItemId });

// Question Bank - Sharing
export const listSharedBankApi = () => http.get("/question-bank/shared");
export const shareBankItemApi = (itemId, usernames) =>
  http.post(`/question-bank/${itemId}/share`, { usernames });

// Question Bank - Usage & Stats
export const getBankUsageApi = (itemId) => http.get(`/question-bank/${itemId}/usage`);
export const getBankCrossStatsApi = (itemId, version) =>
  http.get(`/question-bank/${itemId}/cross-stats${version != null ? `?version=${version}` : ''}`);

// Import
export const importQuestionFromBankApi = (surveyId, payload) =>
  http.post(`/surveys/${surveyId}/questions/import`, payload);

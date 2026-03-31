import axios from "axios";

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api",
  timeout: 15000,
});

http.interceptors.request.use((config) => {
  const token = localStorage.getItem("survey_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

http.interceptors.response.use(
  (response) => {
    if (response.data?.code !== 0) {
      return Promise.reject(new Error(response.data?.message || "请求失败"));
    }
    return response.data.data;
  },
  (error) => {
    const message = error?.response?.data?.message || error?.message || "网络错误";
    return Promise.reject(new Error(message));
  },
);

export default http;

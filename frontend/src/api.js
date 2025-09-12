import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || "/", // with proxy, this is "/"
  timeout: 15000,
});

api.interceptors.request.use((config) => {
  config.headers = config.headers || {};

  const t = sessionStorage.getItem("token");

  // Normalize to pathname so regex works for both relative/absolute URLs
  let path = "";
  try {
    path = new URL(config.url, config.baseURL || window.location.origin).pathname;
  } catch {
    path = config.url || "";
  }

  // Don't send Authorization for login/register
  const isAuthEndpoint = /^\/api\/auth\/(login|register)\b/.test(path);

  if (t && !isAuthEndpoint) {
    config.headers.Authorization = `Bearer ${t}`;
  } else if ("Authorization" in config.headers) {
    delete config.headers.Authorization;
  }

  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const friendly = err?.response?.data?.message || err.message || "Request failed";
    return Promise.reject({ ...err, friendly, status: err?.response?.status });
  }
);

export default api;

import { createContext, useContext, useEffect, useState } from "react";
import api from "./api";

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Rehydrate on refresh
  useEffect(() => {
    const t = sessionStorage.getItem("token");
    const u = sessionStorage.getItem("user");
    if (t) setToken(t);
    if (u) setUser(JSON.parse(u));
    setLoading(false);
  }, []);

  const login = async (username, password) => {
    // Trim whitespace to avoid trailing/leading space bugs
    const body = {
      username: String(username || "").trim(),
      password: String(password || ""),
    };

    const { data } = await api.post("/api/auth/login", body);

    // Accept common token key names; your backend returns access_token
    const t = data?.access_token || data?.token || data?.data?.access_token;
    if (!t) throw new Error("No token returned");

    sessionStorage.setItem("token", t);
    setToken(t);

    // (Optional) fetch user id; axios interceptor will also attach token,
    // but we pass header explicitly to be safe.
    try {
      const me = await api.get("/api/auth/me", {
        headers: { Authorization: `Bearer ${t}` },
      });
      const u = { id: me.data?.user_id, username: body.username };
      setUser(u);
      sessionStorage.setItem("user", JSON.stringify(u));
    } catch {
      const u = { username: body.username };
      setUser(u);
      sessionStorage.setItem("user", JSON.stringify(u));
    }
  };

  const logout = () => {
    sessionStorage.clear();
    setToken(null);
    setUser(null);
  };

  return (
    <AuthCtx.Provider
      value={{ token, user, loading, login, logout, isAuthed: !!token }}
    >
      {children}
    </AuthCtx.Provider>
  );
}

export const useAuth = () => useContext(AuthCtx);

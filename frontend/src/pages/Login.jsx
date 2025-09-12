import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../auth";

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [username, setU] = useState("");
  const [password, setP] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    setErr(""); setBusy(true);
    
    try {
      await login(username, password);
      nav("/scan", { replace: true });
    } catch (e) {
      // Show precise server message to avoid guessing
      console.log("LOGIN ERROR:", e.status, e.response?.data || e);
      setErr(
        (e.response &&
          (e.response.data?.message ||
            e.response.data?.error ||
            JSON.stringify(e.response.data))) ||
          e.friendly ||
          e.message ||
          "Login failed"
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container">
      <div className="card" style={{ maxWidth: 420 }}>
        <h2 style={{ marginTop: 0 }}>Login</h2>
        {err && <p className="error">{err}</p>}
        <form onSubmit={onSubmit}>
          <input placeholder="username" value={username} onChange={(e)=>setU(e.target.value)} />
          <div style={{ height: 8 }} />
          <input type="password" placeholder="password" value={password} onChange={(e)=>setP(e.target.value)} />
          <div style={{ height: 12 }} />
          <button disabled={busy}>{busy ? "..." : "Login"}</button>
        </form>
        <p className="muted" style={{ marginTop: 8 }}>
          New? <Link to="/register">Create account</Link>
        </p>
      </div>
    </div>
  );
}

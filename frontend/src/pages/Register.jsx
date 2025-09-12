import { useState } from "react";
import api from "../api";
import { Link, useNavigate } from "react-router-dom";

export default function Register() {
  const [username, setU] = useState("");
  const [password, setP] = useState("");
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);
  const nav = useNavigate();

  const submit = async (e) => {
    e.preventDefault();
    setMsg(""); setBusy(true);
    if (!username.trim()) { setMsg("username is required"); setBusy(false); return; }
    if (password.trim().length < 8) { setMsg("password must be at least 8 characters"); setBusy(false); return; }
    try {
      const res = await api.post("/api/auth/register", { username, password });
      setMsg(res.data?.message || "registered");
      setTimeout(()=> nav("/login"), 600);
    } catch (err) {
      setMsg(err?.response?.data?.message || err?.friendly || "register failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container">
      <div className="card" style={{ maxWidth: 420 }}>
        <h2 style={{ marginTop: 0 }}>Create account</h2>
        {msg && <p className={/failed|required|exists|least/i.test(msg) ? "error" : "success"}>{msg}</p>}
        <form onSubmit={submit}>
          <input placeholder="username" value={username} onChange={(e)=>setU(e.target.value)} />
          <div style={{ height: 8 }} />
          <input type="password" placeholder="password (min 8 chars)" value={password} onChange={(e)=>setP(e.target.value)} />
          <div style={{ height: 12 }} />
          <button disabled={busy}>{busy ? "..." : "Register"}</button>
        </form>
        <p className="muted" style={{ marginTop: 8 }}>
          Already have an account? <Link to="/login">Login</Link>
        </p>
      </div>
    </div>
  );
}

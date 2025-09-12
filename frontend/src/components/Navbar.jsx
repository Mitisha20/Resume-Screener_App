import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";

export default function Navbar() {
  const { token, user, logout } = useAuth();
  const nav = useNavigate();

  const onLogout = () => {
    logout();
    nav("/login");
  };

  return (
    <nav className="nav">
      <div className="container" style={{ display: "flex", gap: 12, alignItems: "center" }}>
        <Link to="/">Home</Link>
        <Link to="/scan">Scan</Link>
        <Link to="/history">History</Link>

        <div style={{ marginLeft: "auto" }}>
          {token ? (
            <>
              <span className="muted" style={{ marginRight: 12 }}>
                Hi, {user?.username || "user"}
              </span>
              <button onClick={onLogout}>Logout</button>
            </>
          ) : (
            <>
              <Link to="/login" style={{ marginRight: 12 }}>
                Login
              </Link>
              <Link to="/register">Register</Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}

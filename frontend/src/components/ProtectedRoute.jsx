import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth";

export default function ProtectedRoute({ children }) {
  const { isAuthed, loading } = useAuth();
  const location = useLocation();

  // avoid flicker while we rehydrate token/user
  if (loading) {
    return (
      <div className="container">
        <div className="card">Loading…</div>
      </div>
    );
  }

  if (!isAuthed) {
    // send them to login and remember where they were going
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return children;
}

import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Scan from "./pages/Scan";   // <- our scanner page
import History from "./pages/History";
import ProtectedRoute from "./components/ProtectedRoute";
// placeholder list (can be empty)

// Minimal, safe Home & 404 so routing never explodes
function Home() {
  return (
    <div className="container">
      <div className="card">
        <h2 style={{ marginTop: 0 }}>Home</h2>
        <p>Welcome!</p>
      </div>
    </div>
  );
}

function NotFound() {
  return (
    <div className="container">
      <div className="card">
        <h3>Page not found</h3>
      </div>
    </div>
  );
}

export default function App() {
 return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        {/* Protected pages */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Home />
            </ProtectedRoute>
          }
        />
        <Route
          path="/scan"
          element={
            <ProtectedRoute>
              <Scan />
            </ProtectedRoute>
          }
        />
        <Route
          path="/history"
          element={
            <ProtectedRoute>
              <History />
            </ProtectedRoute>
          }
        />

        {/* Public auth pages */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* 404 */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}

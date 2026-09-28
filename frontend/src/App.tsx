import type { ReactNode } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { isLoggedIn } from "./api";
import Login from "./pages/Login";
import Lures from "./pages/Lures";
import Catches from "./pages/Catches";

function RequireAuth({ children }: { children: ReactNode }) {
  if (!isLoggedIn()) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/lures"
          element={
            <RequireAuth>
              <Lures />
            </RequireAuth>
          }
        />
        <Route
          path="/catches"
          element={
            <RequireAuth>
              <Catches />
            </RequireAuth>
          }
        />
        <Route
          path="*"
          element={<Navigate to={isLoggedIn() ? "/lures" : "/login"} replace />}
        />
      </Routes>
    </BrowserRouter>
  );
}

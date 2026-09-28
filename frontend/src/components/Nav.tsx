import { Link, useNavigate } from "react-router-dom";
import { clearToken } from "../api";

export default function Nav() {
  const navigate = useNavigate();

  function handleLogout() {
    clearToken();
    navigate("/login");
  }

  return (
    <nav className="nav">
      <Link to="/lures">Lures</Link>
      <Link to="/catches">Catches</Link>
      <button type="button" onClick={handleLogout}>
        Log out
      </button>
    </nav>
  );
}

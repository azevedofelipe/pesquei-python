import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError, login, register } from "../api";

type Tab = "login" | "register";

export default function Login() {
  const navigate = useNavigate();
  const [tab, setTab] = useState<Tab>("login");

  const [loginUsername, setLoginUsername] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loginLoading, setLoginLoading] = useState(false);

  const [registerUsername, setRegisterUsername] = useState("");
  const [registerEmail, setRegisterEmail] = useState("");
  const [registerPassword, setRegisterPassword] = useState("");
  const [registerError, setRegisterError] = useState<string | null>(null);
  const [registerSuccess, setRegisterSuccess] = useState<string | null>(null);
  const [registerLoading, setRegisterLoading] = useState(false);

  function selectTab(next: Tab) {
    setTab(next);
    setLoginError(null);
    setRegisterError(null);
    setRegisterSuccess(null);
  }

  async function handleLogin(e: FormEvent) {
    e.preventDefault();
    setLoginError(null);
    setLoginLoading(true);
    try {
      await login(loginUsername, loginPassword);
      navigate("/lures");
    } catch (err) {
      setLoginError(err instanceof ApiError ? err.message : "Failed to log in.");
    } finally {
      setLoginLoading(false);
    }
  }

  async function handleRegister(e: FormEvent) {
    e.preventDefault();
    setRegisterError(null);
    setRegisterSuccess(null);
    setRegisterLoading(true);
    try {
      await register(registerUsername, registerEmail, registerPassword);
      setRegisterSuccess("Account created. You can log in now.");
      setLoginUsername(registerUsername);
      setRegisterPassword("");
      setTab("login");
    } catch (err) {
      setRegisterError(err instanceof ApiError ? err.message : "Failed to register.");
    } finally {
      setRegisterLoading(false);
    }
  }

  return (
    <div>
      <h1>Pesquei</h1>
      <div className="nav">
        <a href="#login" onClick={(e) => { e.preventDefault(); selectTab("login"); }}>
          Log in
        </a>
        <a href="#register" onClick={(e) => { e.preventDefault(); selectTab("register"); }}>
          Register
        </a>
      </div>

      {tab === "login" ? (
        <form onSubmit={handleLogin}>
          <div>
            <label htmlFor="login-username">Username</label>
            <input
              id="login-username"
              type="text"
              required
              value={loginUsername}
              onChange={(e) => setLoginUsername(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="login-password">Password</label>
            <input
              id="login-password"
              type="password"
              required
              value={loginPassword}
              onChange={(e) => setLoginPassword(e.target.value)}
            />
          </div>
          {registerSuccess && <div className="success">{registerSuccess}</div>}
          {loginError && <div className="error">{loginError}</div>}
          <button type="submit" disabled={loginLoading}>
            {loginLoading ? "Logging in..." : "Log in"}
          </button>
        </form>
      ) : (
        <form onSubmit={handleRegister}>
          <div>
            <label htmlFor="register-username">Username</label>
            <input
              id="register-username"
              type="text"
              required
              value={registerUsername}
              onChange={(e) => setRegisterUsername(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="register-email">Email</label>
            <input
              id="register-email"
              type="email"
              required
              value={registerEmail}
              onChange={(e) => setRegisterEmail(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="register-password">Password</label>
            <input
              id="register-password"
              type="password"
              required
              value={registerPassword}
              onChange={(e) => setRegisterPassword(e.target.value)}
            />
          </div>
          {registerError && <div className="error">{registerError}</div>}
          <button type="submit" disabled={registerLoading}>
            {registerLoading ? "Registering..." : "Register"}
          </button>
        </form>
      )}
    </div>
  );
}

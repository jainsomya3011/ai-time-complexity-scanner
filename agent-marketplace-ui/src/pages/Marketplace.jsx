import { useCallback, useEffect, useState } from "react";
import AgentCard from "../components/AgentCard";
import { MARKETPLACE_API } from "../apiBase";

function Marketplace() {
  const [urlAgentId, setUrlAgentId] = useState(() => {
    if (typeof window === "undefined") return "";
    return new URLSearchParams(window.location.search).get("agent") || "";
  });
  const [agents, setAgents] = useState([]);
  const [token, setToken] = useState(() => localStorage.getItem("token") || null);
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem("token");
    return stored ? stored.split(":")[0] : null;
  });
  const [authMode, setAuthMode] = useState("login");
  const [authData, setAuthData] = useState({ email: "", password: "" });
  const [ownedAgents, setOwnedAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [agentCode, setAgentCode] = useState("");
  const [agentEndpoint, setAgentEndpoint] = useState("");
  const [agentResult, setAgentResult] = useState(null);
  const [agentError, setAgentError] = useState(null);
  const [agentBusy, setAgentBusy] = useState(false);
  const [loading, setLoading] = useState(false);
  const [authNotice, setAuthNotice] = useState(null);

  const fetchUserAgents = useCallback(async (activeToken) => {
    const t = activeToken ?? token;
    if (!t) return;
    const res = await fetch(`${MARKETPLACE_API}/user/agents`, {
      headers: { Authorization: `Bearer ${t}` },
    });
    if (res.ok) {
      const data = await res.json();
      setOwnedAgents(data.owned_agents || []);
    }
  }, [token]);

  useEffect(() => {
    const syncAgentFromUrl = () => {
      const next = new URLSearchParams(window.location.search).get("agent") || "";
      setUrlAgentId(next);
    };
    window.addEventListener("popstate", syncAgentFromUrl);
    return () => window.removeEventListener("popstate", syncAgentFromUrl);
  }, []);

  useEffect(() => {
    fetch(`${MARKETPLACE_API}/agents`)
      .then((res) => res.json())
      .then((data) => setAgents(Array.isArray(data) ? data : []))
      .catch((err) => console.error(err));
  }, []);

  useEffect(() => {
    const storedToken = localStorage.getItem("token");
    if (!storedToken) return;
    fetch(`${MARKETPLACE_API}/user/agents`, {
      headers: { Authorization: `Bearer ${storedToken}` },
    })
      .then((res) => (res.ok ? res.json() : Promise.reject()))
      .then((data) => setOwnedAgents(data.owned_agents || []))
      .catch(() => setOwnedAgents([]));
  }, []);

  const handleAuth = async (e) => {
    e.preventDefault();
    setLoading(true);
    setAuthNotice(null);
    try {
      const endpoint = authMode === "login" ? "login" : "signup";
      const res = await fetch(`${MARKETPLACE_API}/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(authData),
      });

      const raw = await res.text();
      let data = {};
      try {
        data = raw ? JSON.parse(raw) : {};
      } catch {
        data = { error: raw || "Unexpected response" };
      }

      if (!res.ok) {
        setAuthNotice({ type: "error", text: data.error || `Request failed (${res.status})` });
        setLoading(false);
        return;
      }

      if (authMode === "signup") {
        setAuthNotice({
          type: "success",
          text: data.message || "Account created. Log in with the same email and password to continue.",
        });
        setAuthMode("login");
        setAuthData((prev) => ({ ...prev, password: "" }));
        setLoading(false);
        return;
      }

      if (!data.token) {
        setAuthNotice({ type: "error", text: "Login succeeded but no token was returned." });
        setLoading(false);
        return;
      }

      setToken(data.token);
      localStorage.setItem("token", data.token);
      setUser(authData.email);
      setAuthData({ email: "", password: "" });
      await fetchUserAgents(data.token);
    } catch (error) {
      setAuthNotice({ type: "error", text: `Network error: ${error.message}` });
    }
    setLoading(false);
  };

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    setOwnedAgents([]);
    setSelectedAgent(null);
    setAgentCode("");
    setAgentEndpoint("");
    setAgentResult(null);
    setAgentError(null);
    localStorage.removeItem("token");
    setAuthNotice(null);
  };

  const openAgentPage = async (agent) => {
    const nextUrl = `${window.location.origin}${window.location.pathname}?agent=${encodeURIComponent(
      agent.skills[0].id
    )}`;
    window.open(nextUrl, "_blank", "noopener,noreferrer");
  };

  const loadAgentFromUrl = useCallback(async () => {
    if (!urlAgentId || !token || agents.length === 0) return;
    const agent = agents.find((item) => item.skills?.[0]?.id === urlAgentId);
    if (!agent) return;
    setSelectedAgent(agent);
    setAgentResult(null);
    setAgentError(null);
    setAgentEndpoint(agent.executionEndpoint || "");
    setAgentCode("");
    try {
      const res = await fetch(`${MARKETPLACE_API}/use`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ agent_id: agent.skills[0].id }),
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok && data.endpoint) {
        setAgentEndpoint(data.endpoint);
      }
    } catch {
      // Keep fallback endpoint from card data.
    }
  }, [agents, token, urlAgentId]);

  useEffect(() => {
    loadAgentFromUrl();
  }, [loadAgentFromUrl]);

  const buySelectedAgent = async () => {
    if (!selectedAgent) return;
    setAgentError(null);
    setAgentBusy(true);
    try {
      const res = await fetch(`${MARKETPLACE_API}/buy`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ agent_id: selectedAgent.skills[0].id }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setAgentError(data.error || "Purchase failed");
        return;
      }
      await fetchUserAgents();
    } finally {
      setAgentBusy(false);
    }
  };

  const runSelectedAgent = async () => {
    if (!selectedAgent) return;
    if (!agentCode.trim()) {
      setAgentError("Paste code before using this endpoint.");
      return;
    }
    setAgentError(null);
    setAgentResult(null);
    setAgentBusy(true);
    try {
      const useRes = await fetch(`${MARKETPLACE_API}/use`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ agent_id: selectedAgent.skills[0].id }),
      });
      const useData = await useRes.json().catch(() => ({}));
      if (!useRes.ok) {
        setAgentError(useData.error || "Please buy this agent first.");
        return;
      }

      const endpoint = useData.endpoint || agentEndpoint;
      if (!endpoint) {
        setAgentError("Endpoint is not available.");
        return;
      }
      setAgentEndpoint(endpoint);

      const execRes = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          skill: selectedAgent.skills[0].id,
          input: agentCode,
        }),
      });
      const execData = await execRes.json().catch(() => ({}));
      if (!execRes.ok) {
        setAgentError(execData.error || "Execution failed");
        return;
      }
      setAgentResult(execData);
    } finally {
      setAgentBusy(false);
    }
  };

  if (!token) {
    return (
      <div className="auth-shell">
        <div className="auth-panel">
          <h1 className="auth-title">AI Agent Marketplace</h1>
          <p className="auth-subtitle">
            Create an account, sign in, purchase the agents you need, then run them on your code. Execution stays on the
            existing backend — this UI only guides the journey.
          </p>

          <ol className="auth-steps">
            <li>Sign up</li>
            <li>Log in</li>
            <li>Buy an agent</li>
            <li>Run the agent</li>
          </ol>

          {authNotice ? (
            <div className={`auth-banner auth-banner--${authNotice.type}`} role="status">
              {authNotice.text}
            </div>
          ) : null}

          <div className="auth-card">
            <h2 className="auth-card-title">{authMode === "login" ? "Welcome back" : "Create your account"}</h2>
            <form onSubmit={handleAuth} className="auth-form">
              <label className="auth-label">
                Email
                <input
                  type="email"
                  autoComplete="email"
                  value={authData.email}
                  onChange={(e) => setAuthData({ ...authData, email: e.target.value })}
                  className="auth-input"
                  required
                />
              </label>
              <label className="auth-label">
                Password
                <input
                  type="password"
                  autoComplete={authMode === "login" ? "current-password" : "new-password"}
                  value={authData.password}
                  onChange={(e) => setAuthData({ ...authData, password: e.target.value })}
                  className="auth-input"
                  required
                />
              </label>
              <button type="submit" className="auth-submit" disabled={loading}>
                {loading ? "Please wait…" : authMode === "login" ? "Log in" : "Sign up"}
              </button>
            </form>
            <p className="auth-switch">
              {authMode === "login" ? "New here?" : "Already registered?"}{" "}
              <button
                type="button"
                className="auth-link"
                onClick={() => {
                  setAuthMode(authMode === "login" ? "signup" : "login");
                  setAuthNotice(null);
                }}
              >
                {authMode === "login" ? "Create an account" : "Log in instead"}
              </button>
            </p>
          </div>
        </div>
        <style>{`
          .auth-shell {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem 1.25rem;
            background: radial-gradient(circle at 20% 20%, #c7d2fe 0, transparent 35%),
              radial-gradient(circle at 80% 0%, #bae6fd 0, transparent 32%),
              linear-gradient(145deg, #0f172a, #1e293b 55%, #312e81);
          }
          .auth-panel {
            width: min(480px, 100%);
            color: #e2e8f0;
          }
          .auth-title {
            margin: 0 0 0.5rem;
            font-size: clamp(1.75rem, 4vw, 2.25rem);
            font-weight: 700;
            letter-spacing: -0.02em;
          }
          .auth-subtitle {
            margin: 0 0 1.25rem;
            color: #cbd5f5;
            font-size: 0.95rem;
          }
          .auth-steps {
            margin: 0 0 1.25rem;
            padding-left: 1.2rem;
            color: #cbd5e1;
            font-size: 0.88rem;
            line-height: 1.6;
          }
          .auth-banner {
            margin-bottom: 1rem;
            padding: 0.75rem 1rem;
            border-radius: 12px;
            font-size: 0.9rem;
          }
          .auth-banner--success {
            background: rgba(16, 185, 129, 0.15);
            border: 1px solid rgba(16, 185, 129, 0.45);
            color: #bbf7d0;
          }
          .auth-banner--error {
            background: rgba(248, 113, 113, 0.12);
            border: 1px solid rgba(248, 113, 113, 0.45);
            color: #fecaca;
          }
          .auth-card {
            background: #fff;
            color: var(--text);
            border-radius: 18px;
            padding: 1.5rem 1.35rem 1.25rem;
            box-shadow: 0 25px 60px rgba(0, 0, 0, 0.35);
          }
          .auth-card-title {
            margin: 0 0 1rem;
            font-size: 1.2rem;
          }
          .auth-form {
            display: flex;
            flex-direction: column;
            gap: 0.85rem;
          }
          .auth-label {
            display: flex;
            flex-direction: column;
            gap: 0.35rem;
            font-size: 0.85rem;
            font-weight: 600;
            color: #334155;
          }
          .auth-input {
            padding: 0.7rem 0.85rem;
            border-radius: 10px;
            border: 1px solid var(--border);
            font-size: 1rem;
          }
          .auth-input:focus {
            outline: 2px solid #6366f1;
            outline-offset: 1px;
            border-color: #6366f1;
          }
          .auth-submit {
            margin-top: 0.25rem;
            padding: 0.85rem 1rem;
            border: none;
            border-radius: 11px;
            font-weight: 700;
            color: #fff;
            cursor: pointer;
            background: linear-gradient(135deg, #4f46e5, #7c3aed);
          }
          .auth-submit:disabled {
            opacity: 0.65;
            cursor: not-allowed;
          }
          .auth-switch {
            margin: 1rem 0 0;
            text-align: center;
            font-size: 0.9rem;
            color: #64748b;
          }
          .auth-link {
            border: none;
            background: none;
            padding: 0;
            color: #4f46e5;
            font-weight: 700;
            cursor: pointer;
            text-decoration: underline;
          }
        `}</style>
      </div>
    );
  }

  const selectedOwned = selectedAgent ? ownedAgents.includes(selectedAgent.skills[0].id) : false;
  const isAgentPage = Boolean(urlAgentId);

  return (
    <div className="market-layout">
      <header className="market-header">
        <div>
          <p className="market-eyebrow">Signed in</p>
          <h1 className="market-title">Agent workspace</h1>
          <p className="market-lede">
            Click Use endpoint on an agent to open its page, then buy it and run it after pasting your code.
          </p>
        </div>
        <div className="market-user">
          <span className="market-owned-count">Owned agents: {ownedAgents.length}</span>
          <span className="market-email">{user}</span>
          <button type="button" className="market-logout" onClick={handleLogout}>
            Log out
          </button>
        </div>
      </header>

      {selectedAgent ? (
        <section className="agent-page">
          <div className="agent-page-head">
            <h2>{selectedAgent.name} page</h2>
            <span className={`agent-status ${selectedOwned ? "owned" : "not-owned"}`}>
              {selectedOwned ? "Purchased" : "Not purchased"}
            </span>
          </div>
          {isAgentPage ? (
            <button
              type="button"
              className="back-btn"
              onClick={() => {
                const baseUrl = `${window.location.origin}${window.location.pathname}`;
                window.location.href = baseUrl;
              }}
            >
              Back to catalog
            </button>
          ) : null}
          <p className="agent-page-endpoint">
            Endpoint: <code>{agentEndpoint || selectedAgent.executionEndpoint}</code>
          </p>
          {!selectedOwned ? (
            <button type="button" className="buy-btn" onClick={buySelectedAgent} disabled={agentBusy}>
              {agentBusy ? "Buying..." : `Buy this agent · $${selectedAgent.price}`}
            </button>
          ) : null}
          <label className="code-label">
            Paste code for this agent
            <textarea
              className="code-textarea"
              value={agentCode}
              onChange={(e) => setAgentCode(e.target.value)}
              placeholder="// Paste code here"
              spellCheck={false}
            />
          </label>
          <div className="agent-actions">
            <button
              type="button"
              className="run-btn"
              onClick={runSelectedAgent}
              disabled={agentBusy || !selectedOwned}
              title={!selectedOwned ? "Buy this agent first" : "Run selected endpoint"}
            >
              {agentBusy ? "Running..." : "Use endpoint"}
            </button>
            {!isAgentPage ? (
              <button type="button" className="close-btn" onClick={() => setSelectedAgent(null)} disabled={agentBusy}>
                Close
              </button>
            ) : null}
          </div>
          {!selectedOwned ? (
            <p className="agent-help">Buy this agent first. After purchase, the Use endpoint button will be enabled.</p>
          ) : null}
          {agentError ? <p className="agent-error">{agentError}</p> : null}
          {agentResult ? <pre className="agent-result">{JSON.stringify(agentResult, null, 2)}</pre> : null}
        </section>
      ) : null}

      {!isAgentPage ? (
        <section>
        <div className="section-head">
          <h2>Catalog</h2>
          <p className="section-copy">Each card has its endpoint. Copy it, paste in browser, buy that agent, then use it.</p>
        </div>
        {agents.length === 0 ? (
          <p className="muted">Loading agents from the marketplace API…</p>
        ) : (
          <div className="agent-grid">
            {agents.map((agent) => (
              <AgentCard
                key={agent.skills[0].id}
                agent={agent}
                owned={ownedAgents.includes(agent.skills[0].id)}
                onUseEndpoint={openAgentPage}
              />
            ))}
          </div>
        )}
        </section>
      ) : null}

      <style>{`
        .market-layout {
          max-width: 1120px;
          margin: 0 auto;
          padding: 2rem 1.25rem 3rem;
        }
        .market-header {
          display: flex;
          flex-wrap: wrap;
          gap: 1rem;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 1.75rem;
        }
        .market-eyebrow {
          margin: 0;
          font-size: 0.78rem;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          color: var(--text-muted);
          font-weight: 700;
        }
        .market-title {
          margin: 0.15rem 0 0.35rem;
          font-size: clamp(1.6rem, 3vw, 2rem);
        }
        .market-lede {
          margin: 0;
          max-width: 640px;
          color: #475569;
        }
        .market-user {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
          align-items: flex-end;
        }
        .market-email {
          font-weight: 600;
          color: #0f172a;
          word-break: break-all;
          text-align: right;
        }
        .market-owned-count {
          font-size: 0.78rem;
          letter-spacing: 0.02em;
          text-transform: uppercase;
          color: #475569;
          font-weight: 700;
        }
        .market-logout {
          border: 1px solid #e2e8f0;
          background: #fff;
          padding: 0.45rem 0.9rem;
          border-radius: 999px;
          cursor: pointer;
          font-weight: 600;
          color: #b91c1c;
        }
        .section-head h2 {
          margin: 0 0 0.25rem;
          font-size: 1.2rem;
        }
        .section-copy {
          margin: 0 0 1rem;
          color: var(--text-muted);
          font-size: 0.92rem;
        }
        .agent-grid {
          display: grid;
          gap: 1.25rem;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        }
        .muted {
          color: var(--text-muted);
        }
        .agent-page {
          margin-top: 2rem;
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: var(--radius-lg);
          padding: 1rem 1.1rem 1.2rem;
          box-shadow: var(--shadow);
        }
        .agent-page-head {
          display: flex;
          justify-content: space-between;
          gap: 1rem;
          align-items: center;
          margin-bottom: 0.65rem;
        }
        .agent-page-head h2 {
          margin: 0;
          font-size: 1.1rem;
        }
        .agent-status {
          font-size: 0.78rem;
          font-weight: 700;
          padding: 0.25rem 0.6rem;
          border-radius: 999px;
          border: 1px solid;
        }
        .agent-status.owned {
          color: #065f46;
          border-color: #6ee7b7;
          background: #ecfdf5;
        }
        .agent-status.not-owned {
          color: #92400e;
          border-color: #fcd34d;
          background: #fffbeb;
        }
        .agent-page-endpoint {
          margin: 0 0 0.75rem;
          color: #334155;
          font-size: 0.9rem;
        }
        .buy-btn,
        .run-btn {
          border: none;
          border-radius: 10px;
          padding: 0.7rem 1rem;
          font-weight: 700;
          cursor: pointer;
          color: #fff;
        }
        .back-btn {
          margin-bottom: 0.7rem;
          border: 1px solid #cbd5e1;
          border-radius: 10px;
          padding: 0.45rem 0.75rem;
          font-weight: 700;
          background: #fff;
          color: #1e293b;
          cursor: pointer;
        }
        .close-btn {
          border: 1px solid #cbd5e1;
          border-radius: 10px;
          padding: 0.7rem 1rem;
          font-weight: 700;
          cursor: pointer;
          background: #fff;
          color: #334155;
        }
        .buy-btn {
          margin-bottom: 0.85rem;
          background: linear-gradient(135deg, #16a34a, #15803d);
        }
        .run-btn {
          background: linear-gradient(135deg, #2563eb, #1d4ed8);
        }
        .buy-btn:disabled,
        .run-btn:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }
        .code-label {
          display: flex;
          flex-direction: column;
          gap: 0.45rem;
          color: #1e293b;
          font-weight: 600;
          font-size: 0.9rem;
          margin-bottom: 0.8rem;
        }
        .code-textarea {
          min-height: 160px;
          border: 1px solid var(--border);
          border-radius: 10px;
          padding: 0.75rem 0.85rem;
          resize: vertical;
          font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
          font-size: 0.88rem;
        }
        .agent-actions {
          display: flex;
          gap: 0.6rem;
          justify-content: flex-start;
          margin-bottom: 0.6rem;
        }
        .agent-help {
          margin: 0.2rem 0 0;
          color: #92400e;
          font-size: 0.85rem;
        }
        .agent-error {
          margin: 0.4rem 0 0;
          color: #b91c1c;
          font-size: 0.88rem;
        }
        .agent-result {
          margin: 0.8rem 0 0;
          background: #0f172a;
          color: #e2e8f0;
          border-radius: 10px;
          padding: 0.85rem;
          overflow: auto;
          font-size: 0.82rem;
        }
      `}</style>
    </div>
  );
}

export default Marketplace;

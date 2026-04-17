import { useMemo, useState } from "react";

const defaults = {
  icon: "🤖",
  accentColor: "#0ea5e9",
  tagline: "",
  highlights: [],
};

function AgentCard({ agent, owned, onUseEndpoint }) {
  const accent = agent.accentColor || defaults.accentColor;
  const icon = agent.icon || defaults.icon;
  const tagline = agent.tagline || defaults.tagline;
  const highlights = agent.highlights?.length ? agent.highlights : defaults.highlights;
  const skillId = agent.skills[0].id;
  const [cardOpen, setCardOpen] = useState(true);

  const cardJson = useMemo(() => JSON.stringify(agent, null, 2), [agent]);

  return (
    <article
      className="agent-card"
      style={{
        borderRadius: "var(--radius-lg)",
        border: `1px solid ${accent}33`,
        background: "var(--surface)",
        boxShadow: "var(--shadow)",
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <header
        style={{
          padding: "1.25rem 1.25rem 1rem",
          background: `linear-gradient(135deg, ${accent}14, transparent)`,
          borderBottom: "1px solid var(--border)",
        }}
      >
        <div style={{ display: "flex", gap: "0.85rem", alignItems: "flex-start" }}>
          <div
            aria-hidden
            style={{
              width: "3rem",
              height: "3rem",
              borderRadius: "12px",
              background: `${accent}22`,
              display: "grid",
              placeItems: "center",
              fontSize: "1.5rem",
              flexShrink: 0,
            }}
          >
            {icon}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem 0.6rem", alignItems: "center" }}>
              <h2 style={{ margin: 0, fontSize: "1.2rem", fontWeight: 700, color: "var(--text)" }}>
                {agent.name}
              </h2>
              <span
                style={{
                  fontSize: "0.72rem",
                  fontWeight: 600,
                  letterSpacing: "0.04em",
                  textTransform: "uppercase",
                  color: accent,
                  border: `1px solid ${accent}55`,
                  padding: "0.15rem 0.45rem",
                  borderRadius: "999px",
                  background: "#fff",
                }}
              >
                {agent.category}
              </span>
            </div>
            {tagline ? (
              <p style={{ margin: "0.35rem 0 0", color: "var(--text-muted)", fontSize: "0.95rem" }}>{tagline}</p>
            ) : null}
            <p style={{ margin: "0.5rem 0 0", color: "#475569", fontSize: "0.9rem" }}>{agent.description}</p>
          </div>
        </div>

        {highlights.length > 0 ? (
          <ul
            style={{
              margin: "1rem 0 0",
              paddingLeft: "1.15rem",
              color: "#334155",
              fontSize: "0.88rem",
            }}
          >
            {highlights.map((h) => (
              <li key={h} style={{ marginBottom: "0.25rem" }}>
                {h}
              </li>
            ))}
          </ul>
        ) : null}

        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "0.75rem",
            marginTop: "1rem",
            fontSize: "0.85rem",
            color: "var(--text-muted)",
          }}
        >
          <span>
            <strong style={{ color: "var(--text)" }}>Price</strong> · ${agent.price}
          </span>
          <span>
            <strong style={{ color: "var(--text)" }}>Version</strong> · {agent.version}
          </span>
          <span>
            <strong style={{ color: "var(--text)" }}>Endpoint</strong> ·{" "}
            <code style={{ fontSize: "0.8rem", background: "var(--surface-muted)", padding: "0.1rem 0.35rem", borderRadius: 6 }}>
              {agent.executionEndpoint || "Resolved at runtime"}
            </code>
          </span>
        </div>
      </header>

      <div style={{ padding: "1rem 1.25rem", display: "flex", flexDirection: "column", gap: "0.75rem" }}>
        <button
          type="button"
          onClick={() => onUseEndpoint(agent)}
          style={{
            width: "100%",
            padding: "0.75rem 1rem",
            borderRadius: 10,
            border: `1px solid ${accent}`,
            cursor: "pointer",
            fontWeight: 700,
            color: "#fff",
            background: `linear-gradient(135deg, ${accent}, ${accent}cc)`,
          }}
        >
          Use endpoint
        </button>
        <p style={{ margin: 0, fontSize: "0.82rem", color: "var(--text-muted)" }}>
          {owned ? "Purchased." : "Not purchased yet."} Click to open this agent page.
        </p>
      </div>

      <section
        style={{
          borderTop: "1px solid var(--border)",
          background: "var(--surface-muted)",
        }}
      >
        <button
          type="button"
          onClick={() => setCardOpen((o) => !o)}
          style={{
            width: "100%",
            padding: "0.85rem 1.25rem",
            border: "none",
            background: "transparent",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            cursor: "pointer",
            fontWeight: 600,
            color: "#334155",
          }}
        >
          <span>Agent card (machine-readable)</span>
          <span aria-hidden style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
            {cardOpen ? "Hide" : "Show"}
          </span>
        </button>
        {cardOpen ? (
          <div style={{ padding: "0 1.25rem 1.25rem" }}>
            <p style={{ margin: "0 0 0.65rem", fontSize: "0.82rem", color: "var(--text-muted)" }}>
              Full A2A-style descriptor served from the backend. Skill id <code>{skillId}</code> is used for purchase, and
              execution is routed to that skill's dedicated endpoint by the marketplace.
            </p>
            <pre
              style={{
                margin: 0,
                maxHeight: "320px",
                overflow: "auto",
                padding: "1rem",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--border)",
                background: "#fff",
                fontSize: "0.78rem",
                lineHeight: 1.45,
              }}
            >
              {cardJson}
            </pre>
          </div>
        ) : null}
      </section>
    </article>
  );
}

export default AgentCard;

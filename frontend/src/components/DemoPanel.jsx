import { SCENARIOS } from "../data";

export function DemoPanel({ selected, disabled, onSelect }) {
  return (
    <aside className="demo-panel" aria-labelledby="demo-title">
      <div className="demo-panel__heading">
        <span className="demo-pill">Demo mode</span>
        <span className="demo-panel__pulse" aria-hidden="true" />
      </div>
      <h2 id="demo-title">Simulated deterministic scenario</h2>
      <p>Every value below comes from the FastAPI fixture API. No live call or model inference is running.</p>
      <div className="scenario-list" role="radiogroup" aria-label="Demo scenario">
        {SCENARIOS.map((scenario, index) => (
          <button
            key={scenario.id}
            className={`scenario ${selected === scenario.id ? "scenario--selected" : ""}`}
            role="radio"
            aria-checked={selected === scenario.id}
            disabled={disabled}
            onClick={() => onSelect(scenario.id)}
          >
            <span className="scenario__index">0{index + 1}</span>
            <span className="scenario__copy"><strong>{scenario.label}</strong><small>{scenario.detail}</small></span>
            <span className={`scenario__risk risk-dot--${scenario.expected.toLowerCase()}`}>{scenario.expected}</span>
          </button>
        ))}
      </div>
      <p className="demo-panel__footnote">Switching scenarios creates a new ephemeral demo session.</p>
    </aside>
  );
}

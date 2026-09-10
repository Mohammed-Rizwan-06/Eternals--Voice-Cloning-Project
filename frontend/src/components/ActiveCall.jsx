import { useEffect, useState } from "react";
import { RISK_COPY, SIGNAL_LABELS } from "../data";
import { ProbabilityMeter } from "./ProbabilityMeter";
import { Waveform } from "./Waveform";

function formatDuration(seconds) {
  return `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
}

export function ActiveCall({ session, eventState, busyAction, onCommand }) {
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    const timer = window.setInterval(() => setSeconds((value) => value + 1), 1000);
    return () => window.clearInterval(timer);
  }, []);

  const { authenticity, conversation, risk, caller } = session;
  const riskCopy = RISK_COPY[risk.level] || RISK_COPY.unavailable;
  return (
    <section className={`active-call risk-theme--${risk.level}`} aria-labelledby="active-title">
      <div className="call-header">
        <div><p className="eyebrow"><span className="live-dot" /> Protected demo call</p><h1 id="active-title">{caller.display_name}</h1><p>{caller.masked_phone_number} · {caller.reputation} caller</p></div>
        <div className="timer" aria-label={`Call duration ${formatDuration(seconds)}`}><span>{formatDuration(seconds)}</span><small>elapsed</small></div>
      </div>

      <Waveform />

      <div className="monitor-strip">
        <span className="monitor-icon" aria-hidden="true">V</span>
        <div><strong>VoxShield monitoring enabled</strong><small>Deterministic fixture analysis · SSE {eventState}</small></div>
        <span className="demo-pill">Simulated</span>
      </div>

      <div className="analysis-grid">
        <article className="panel voice-panel">
          <div className="panel__heading"><div><p className="eyebrow">Independent signal 01</p><h2>Voice authenticity</h2></div><span className={`status-tag status-tag--${authenticity.status}`}>{authenticity.status.replaceAll("_", " ")}</span></div>
          <ProbabilityMeter label="Likely human" value={authenticity.human_probability} tone="human" />
          <ProbabilityMeter label="AI / cloned voice" value={authenticity.ai_probability} tone="ai" />
          <div className="metric-row"><span>Rolling AI evidence</span><strong>{authenticity.rolling_ai_probability == null ? "Unavailable" : `${Math.round(authenticity.rolling_ai_probability * 100)}%`}</strong></div>
          <div className="metric-row"><span>Usable speech</span><strong>{authenticity.usable_speech_seconds}s · {authenticity.valid_windows} windows</strong></div>
          <p className="disclaimer">Authenticity evidence does not determine whether a caller is financially safe.</p>
        </article>

        <article className="panel conversation-panel">
          <div className="panel__heading"><div><p className="eyebrow">Independent signal 02</p><h2>Conversation intelligence</h2></div><span className={`status-tag status-tag--${conversation.status}`}>{conversation.status.replaceAll("_", " ")}</span></div>
          <div className="transcript" aria-live="polite">
            <span>Rolling transcript · demo fixture</span>
            <p>{conversation.transcript || "No transcript supplied by this deterministic scenario."}</p>
          </div>
          <div className="signals">
            <h3>Detected indicators <span>{conversation.signals.length}</span></h3>
            {conversation.signals.length ? conversation.signals.map((signal) => (
              <div className={`signal signal--${signal.severity}`} key={`${signal.type}-${signal.timestamp}`}>
                <span aria-hidden="true">!</span><div><strong>{SIGNAL_LABELS[signal.type] || signal.type.replaceAll("_", " ")}</strong><small>{signal.evidence}</small></div><em>{signal.severity}</em>
              </div>
            )) : <p className="empty-state">No scam-language indicators supplied.</p>}
          </div>
        </article>
      </div>

      <article className={`risk-card risk-card--${risk.level}`} aria-live="polite">
        <div className="risk-card__level"><span>Overall fused assessment</span><strong>{riskCopy.label}</strong><small>{riskCopy.summary}</small></div>
        <div className="risk-components">
          <span>Caller <strong>{risk.caller_risk}</strong></span><span>Authenticity <strong>{risk.authenticity_risk}</strong></span><span>Conversation <strong>{risk.conversation_risk}</strong></span>
        </div>
        <div className="risk-card__reason"><strong>Why this assessment</strong>{risk.reasons.map((reason) => <p key={reason}>{reason}</p>)}</div>
        <div className="recommended"><span aria-hidden="true">→</span><p><strong>Recommended action</strong>{risk.recommended_action}</p></div>
      </article>

      <div className="action-bar" aria-label="Call actions">
        <button className="button button--secondary" onClick={() => onCommand("verify")} disabled={busyAction}>Verify caller</button>
        <button className="button button--danger" onClick={() => onCommand("end")} disabled={busyAction}>End call</button>
        <button className="button button--ghost" onClick={() => onCommand("report")} disabled={busyAction}>Report</button>
      </div>
    </section>
  );
}

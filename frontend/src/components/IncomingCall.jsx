import { ShieldMark } from "./Brand";

export function IncomingCall({ session, busy, onAnswer, onDecline }) {
  const caller = session.caller;
  const initials = caller.display_name.split(" ").filter(Boolean).slice(0, 2).map((word) => word[0]).join("");
  return (
    <section className="phone-stage incoming" aria-labelledby="incoming-title">
      <div className="protection-badge"><ShieldMark /> Protection available</div>
      <p className="eyebrow">Simulated incoming call</p>
      <div className="avatar" aria-hidden="true">{initials}</div>
      <h1 id="incoming-title">{caller.display_name}</h1>
      <p className="phone-number">{caller.masked_phone_number}</p>
      <div className={`reputation reputation--${caller.reputation}`}>
        <span aria-hidden="true">●</span> {caller.reputation} caller · {caller.data_source.replaceAll("_", " ")}
      </div>
      <div className="incoming__note">
        <ShieldMark />
        <p><strong>Answer with VoxShield</strong><span>Enable simulated monitoring and risk guidance for this demo session.</span></p>
      </div>
      <div className="call-actions">
        <button className="round-action round-action--decline" onClick={onDecline} disabled={busy} aria-label="Decline simulated call"><span aria-hidden="true">×</span><small>Decline</small></button>
        <button className="round-action round-action--answer" onClick={onAnswer} disabled={busy} aria-label="Answer with VoxShield"><span aria-hidden="true">✓</span><small>{busy ? "Connecting" : "Answer"}</small></button>
      </div>
    </section>
  );
}

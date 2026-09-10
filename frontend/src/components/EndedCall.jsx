export function EndedCall({ session, reported, onRestart }) {
  return (
    <section className="phone-stage ended" aria-labelledby="ended-title">
      <div className="ended__icon" aria-hidden="true">✓</div>
      <p className="eyebrow">Simulated session complete</p>
      <h1 id="ended-title">Call ended</h1>
      <p>{session.caller.display_name} · final assessment <strong className={`text--${session.risk.level}`}>{session.risk.level}</strong></p>
      {reported && <div className="local-report"><strong>Prototype report recorded</strong><span>This is a local demo action. No external authority was contacted.</span></div>}
      <button className="button button--primary" onClick={onRestart}>Return to incoming call</button>
    </section>
  );
}

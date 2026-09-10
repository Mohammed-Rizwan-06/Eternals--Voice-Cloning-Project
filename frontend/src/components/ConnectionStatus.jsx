export function ConnectionStatus({ status, health, onRetry }) {
  const labels = { checking: "Checking backend", online: "Backend connected", offline: "Backend unavailable" };
  return (
    <div className={`connection connection--${status}`} role="status" aria-live="polite">
      <span className="connection__dot" aria-hidden="true" />
      <span>{labels[status]}</span>
      {status === "online" && health?.demo_mode && <span className="connection__mode">Demo API</span>}
      {status === "offline" && <button className="text-button" onClick={onRetry}>Retry</button>}
    </div>
  );
}

export function ProbabilityMeter({ label, value, tone }) {
  const available = typeof value === "number";
  const percentage = available ? Math.round(value * 100) : null;
  return (
    <div className="probability">
      <div className="probability__label"><span>{label}</span><strong>{available ? `${percentage}%` : "Unavailable"}</strong></div>
      <div className="meter" role="meter" aria-label={label} aria-valuemin="0" aria-valuemax="100" aria-valuenow={percentage ?? undefined}>
        <span className={`meter__fill meter__fill--${tone}`} style={{ "--meter-value": `${percentage ?? 0}%` }} />
      </div>
    </div>
  );
}

export function ShieldMark() {
  return <span className="shield-mark" aria-hidden="true">V</span>;
}

export function Brand() {
  return (
    <a className="brand" href="#top" aria-label="VoxShield home">
      <ShieldMark />
      <span><strong>VoxShield</strong><small>Trust the voice. Verify the call.</small></span>
    </a>
  );
}

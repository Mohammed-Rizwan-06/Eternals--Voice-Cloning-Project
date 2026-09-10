const BARS = [34, 56, 72, 48, 82, 61, 39, 74, 92, 58, 45, 78, 64, 38, 70, 88, 52, 66, 42, 76, 57, 84, 49, 68];

export function Waveform() {
  return (
    <div className="waveform-wrap">
      <div className="waveform" aria-hidden="true">
        {BARS.map((height, index) => <span key={index} style={{ "--bar-height": `${height}%`, "--bar-delay": `${index * -45}ms` }} />)}
      </div>
      <span>Simulated voice activity</span>
    </div>
  );
}

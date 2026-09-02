import type { ModelRow } from '../lib/demoData';

export function ModelBars({ rows }: { rows: ModelRow[] }) {
  const max = Math.max(...rows.map((row) => row.mae));
  return (
    <div className="model-bars">
      {rows.map((row) => (
        <div className="model-bar-row" key={row.name}>
          <div className="model-bar-label"><strong>{row.name}</strong><span>MAE {row.mae.toFixed(2)}</span></div>
          <div className="model-bar-track"><span style={{ width: `${(row.mae / max) * 100}%` }} /></div>
        </div>
      ))}
      <p className="tiny-note">Niższa wartość MAE oznacza lepszy wynik. Dane na ekranie są demonstracyjne.</p>
    </div>
  );
}

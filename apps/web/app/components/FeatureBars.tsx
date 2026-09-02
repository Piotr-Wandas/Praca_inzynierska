export function FeatureBars({ data }: { data: { label: string; value: number }[] }) {
  return (
    <div className="feature-bars">
      {data.map((item) => (
        <div className="feature-row" key={item.label}>
          <div className="feature-meta"><span>{item.label}</span><strong>{item.value}</strong></div>
          <div className="feature-track"><span style={{ width: `${item.value}%` }} /></div>
        </div>
      ))}
      <p className="tiny-note">Wartości demonstracyjne: względna ważność cech, nie wynik finalnego eksperymentu SHAP.</p>
    </div>
  );
}

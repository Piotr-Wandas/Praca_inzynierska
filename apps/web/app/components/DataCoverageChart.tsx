type Point = { label: string; companies: number; target: number; revenue?: number };

export default function DataCoverageChart({ data }: { data: Point[] }) {
  if (!data.length) return <div className="empty-chart">Brak danych do wykresu.</div>;
  const width = 920, height = 300, left = 46, right = 18, top = 24, bottom = 48;
  const maxY = Math.max(1, ...data.flatMap(d => [d.companies || 0, d.target || 0, d.revenue || 0]));
  const x = (i:number) => left + (i * (width-left-right)) / Math.max(1, data.length-1);
  const y = (v:number) => top + (height-top-bottom) * (1 - v/maxY);
  const pts = (key:'companies'|'target'|'revenue') => data.map((d,i)=>`${x(i)},${y(Number(d[key]||0))}`).join(' ');
  const tickEvery = Math.max(1, Math.ceil(data.length/8));
  return <div className="chart-wrap data-chart">
    <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Pokrycie danych kwartalnych">
      {[0,.25,.5,.75,1].map((t,i)=><g key={i}><line className="chart-grid" x1={left} y1={y(maxY*t)} x2={width-right} y2={y(maxY*t)}/><text className="chart-label" x={8} y={y(maxY*t)+4}>{Math.round(maxY*t)}</text></g>)}
      <polyline className="data-series all" points={pts('companies')}/>
      <polyline className="data-series target" points={pts('target')}/>
      <polyline className="data-series revenue" points={pts('revenue')}/>
      {data.map((d,i)=> i%tickEvery===0 || i===data.length-1 ? <text key={i} className="chart-label" x={x(i)} y={height-15} textAnchor="middle">{d.label}</text> : null)}
    </svg>
    <div className="chart-legend"><span><i className="legend-dot all"/>Spółki z fundamentami</span><span><i className="legend-dot target"/>Zysk netto</span><span><i className="legend-dot revenue"/>Przychody</span></div>
  </div>;
}

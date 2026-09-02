import type { QuarterPoint } from '../lib/demoData';

export function LineChart({ data }: { data: QuarterPoint[] }) {
  const width = 760;
  const height = 300;
  const padX = 48;
  const padY = 32;
  const values = data.flatMap((point) => [point.actual, point.predicted]);
  const min = Math.min(...values) * 0.9;
  const max = Math.max(...values) * 1.08;
  const usableW = width - padX * 2;
  const usableH = height - padY * 2;
  const x = (index: number) => padX + (index * usableW) / Math.max(data.length - 1, 1);
  const y = (value: number) => padY + ((max - value) * usableH) / Math.max(max - min, 0.001);
  const actual = data.map((point, index) => `${x(index)},${y(point.actual)}`).join(' ');
  const predicted = data.map((point, index) => `${x(index)},${y(point.predicted)}`).join(' ');

  return (
    <div className="chart-wrap">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Wykres wartości rzeczywistych i prognozowanych">
        {[0, 1, 2, 3, 4].map((tick) => {
          const gy = padY + (usableH * tick) / 4;
          return <line key={tick} x1={padX} x2={width - padX} y1={gy} y2={gy} className="chart-grid" />;
        })}
        <polyline points={actual} className="chart-line chart-line-actual" />
        <polyline points={predicted} className="chart-line chart-line-predicted" />
        {data.map((point, index) => (
          <g key={point.quarter}>
            <circle cx={x(index)} cy={y(point.actual)} r="4.5" className="chart-dot chart-dot-actual" />
            <circle cx={x(index)} cy={y(point.predicted)} r="4.5" className="chart-dot chart-dot-predicted" />
            <text x={x(index)} y={height - 9} textAnchor="middle" className="chart-label">
              {point.quarter.replace('20', '')}
            </text>
          </g>
        ))}
      </svg>
      <div className="chart-legend">
        <span><i className="legend-line actual" />Wartość rzeczywista</span>
        <span><i className="legend-line predicted" />Prognoza</span>
      </div>
    </div>
  );
}

'use client';

import { useEffect, useMemo, useState } from 'react';

type Company = { ticker: string; name: string; sector: string };
type Catalog = {
  targets: string[];
  models: { target_code: string; model_name: string }[];
  companies: Company[];
  sectors: string[];
  range: { date_from?: string | null; date_to?: string | null };
};
type MetricSummary = {
  observations: number;
  companies?: number;
  periods?: number;
  mae: number | null;
  rmse: number | null;
  smape: number | null;
  wape: number | null;
  r2: number | null;
};
type Overview = {
  dataset_version: string | null;
  target_code?: string;
  selected_model: { id: number; model_name: string; metrics?: Record<string, number | null>; created_at?: string } | null;
  summary: MetricSummary;
  series: { period: string; actual: number; predicted: number; observations: number }[];
  by_company: ({ ticker: string } & MetricSummary)[];
  by_period: ({ period: string } & MetricSummary)[];
  model_comparison: { model_name: string; metrics: Record<string, number | null> | null }[];
  feature_importance: { feature_name: string; importance_type: string; importance_value: number }[];
  observations: { id: number; ticker: string; company_name: string; sector: string; target_period_end: string; cutoff_at: string; predicted_value: number; actual_value: number; absolute_error: number }[];
};

type Filters = { target: string; model: string; ticker: string; sector: string; dateFrom: string; dateTo: string };

const EMPTY_FILTERS: Filters = { target: 'NET_INCOME_CANONICAL', model: '', ticker: '', sector: '', dateFrom: '', dateTo: '' };

function fmtMoney(value: number | null | undefined) {
  if (value == null || !Number.isFinite(value)) return '—';
  const abs = Math.abs(value);
  if (abs >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(2)} mld`;
  if (abs >= 1_000_000) return `${(value / 1_000_000).toFixed(1)} mln`;
  if (abs >= 1_000) return `${(value / 1_000).toFixed(1)} tys.`;
  return value.toFixed(2);
}
function fmtPct(value: number | null | undefined) { return value == null || !Number.isFinite(value) ? '—' : `${value.toFixed(2)}%`; }
function fmtR2(value: number | null | undefined) { return value == null || !Number.isFinite(value) ? '—' : value.toFixed(3); }
function targetLabel(code: string) {
  const labels: Record<string, string> = { NET_INCOME_CANONICAL: 'Zysk netto t+1', REVENUE: 'Przychody t+1', NET_INTEREST_INCOME: 'Wynik odsetkowy t+1' };
  return labels[code] || code;
}

function TrendChart({ rows }: { rows: Overview['series'] }) {
  if (!rows.length) return <div className="analytics-empty">Brak obserwacji dla wybranych filtrów.</div>;
  const width = 900, height = 310, px = 58, py = 34;
  const vals = rows.flatMap(r => [r.actual, r.predicted]).filter(Number.isFinite);
  const min = Math.min(...vals), max = Math.max(...vals);
  const span = Math.max(max - min, Math.abs(max) * .08, 1);
  const lo = min - span * .08, hi = max + span * .08;
  const x = (i: number) => px + i * (width - px * 2) / Math.max(rows.length - 1, 1);
  const y = (v: number) => py + (hi - v) * (height - py * 2) / (hi - lo);
  const actual = rows.map((r,i)=>`${x(i)},${y(r.actual)}`).join(' ');
  const predicted = rows.map((r,i)=>`${x(i)},${y(r.predicted)}`).join(' ');
  const step = Math.max(1, Math.ceil(rows.length / 8));
  return <div className="analytics-chart-wrap">
    <svg viewBox={`0 0 ${width} ${height}`} className="analytics-svg" role="img" aria-label="Wartość rzeczywista i przewidywana w czasie">
      {[0,1,2,3,4].map(i=>{ const gy=py+i*(height-py*2)/4; return <line key={i} x1={px} x2={width-px} y1={gy} y2={gy} className="analytics-grid"/>; })}
      <polyline points={actual} className="analytics-line actual" />
      <polyline points={predicted} className="analytics-line predicted" />
      {rows.map((r,i)=><g key={r.period}>{i%step===0 || i===rows.length-1 ? <text x={x(i)} y={height-8} textAnchor="middle" className="analytics-axis-label">{r.period.slice(0,7)}</text> : null}</g>)}
    </svg>
    <div className="analytics-legend"><span><i className="legend-swatch actual"/>Rzeczywiste</span><span><i className="legend-swatch predicted"/>Prognoza</span></div>
  </div>;
}

function ErrorBars({ rows }: { rows: Overview['by_company'] }) {
  const data = rows.filter(r=>r.mae != null).slice().sort((a,b)=>(b.mae||0)-(a.mae||0)).slice(0,12);
  if (!data.length) return <div className="analytics-empty">Brak danych do rankingu.</div>;
  const max = Math.max(...data.map(r=>r.mae || 0), 1);
  return <div className="analytics-bars">{data.map(r=><div className="analytics-bar-row" key={r.ticker}>
    <div className="analytics-bar-label"><strong>{r.ticker}</strong><span>{fmtMoney(r.mae)} · n={r.observations}</span></div>
    <div className="analytics-bar-track"><i style={{width:`${Math.max(2,(r.mae||0)/max*100)}%`}}/></div>
  </div>)}</div>;
}

function ModelComparison({ rows, selected }: { rows: Overview['model_comparison']; selected?: string }) {
  const data = rows.map(r=>({name:r.model_name, mae:Number(r.metrics?.mae ?? NaN), smape:Number(r.metrics?.smape ?? NaN)})).filter(r=>Number.isFinite(r.mae)).sort((a,b)=>a.mae-b.mae);
  if (!data.length) return <div className="analytics-empty">Brak zapisanych metryk modeli.</div>;
  const max = Math.max(...data.map(r=>r.mae),1);
  return <div className="analytics-bars">{data.map(r=><div className={`analytics-bar-row ${r.name===selected?'selected':''}`} key={r.name}>
    <div className="analytics-bar-label"><strong>{r.name}</strong><span>MAE {fmtMoney(r.mae)} · sMAPE {fmtPct(r.smape)}</span></div>
    <div className="analytics-bar-track model"><i style={{width:`${Math.max(2,r.mae/max*100)}%`}}/></div>
  </div>)}</div>;
}

function ScatterChart({ rows }: { rows: Overview['observations'] }) {
  const data = rows.filter(r=>Number.isFinite(r.actual_value)&&Number.isFinite(r.predicted_value));
  if (!data.length) return <div className="analytics-empty">Brak punktów actual/predicted.</div>;
  const width=560,height=310,p=42;
  const vals=data.flatMap(r=>[r.actual_value,r.predicted_value]); const min=Math.min(...vals), max=Math.max(...vals); const span=Math.max(max-min,1); const lo=min-span*.05, hi=max+span*.05;
  const pos=(v:number)=>p+(v-lo)*(width-p*2)/(hi-lo); const posY=(v:number)=>height-p-(v-lo)*(height-p*2)/(hi-lo);
  return <div className="analytics-chart-wrap"><svg viewBox={`0 0 ${width} ${height}`} className="analytics-svg" role="img" aria-label="Wykres rozrzutu wartości rzeczywistych i prognozowanych">
    <line x1={pos(lo)} y1={posY(lo)} x2={pos(hi)} y2={posY(hi)} className="analytics-diagonal"/>
    {data.slice(-180).map(r=><circle key={r.id} cx={pos(r.actual_value)} cy={posY(r.predicted_value)} r="3.5" className="analytics-dot"><title>{r.ticker} {r.target_period_end}: actual {fmtMoney(r.actual_value)}, predicted {fmtMoney(r.predicted_value)}</title></circle>)}
    <text x={width/2} y={height-5} textAnchor="middle" className="analytics-axis-label">Wartość rzeczywista</text>
    <text x={14} y={height/2} textAnchor="middle" transform={`rotate(-90 14 ${height/2})`} className="analytics-axis-label">Prognoza</text>
  </svg></div>;
}

function FeatureImportance({ rows }: { rows: Overview['feature_importance'] }) {
  const data=rows.slice(0,12); if(!data.length) return <div className="analytics-empty">Dla wybranego treningu nie zapisano jeszcze feature importance.</div>;
  const max=Math.max(...data.map(r=>Math.abs(r.importance_value)),1);
  return <div className="analytics-bars">{data.map(r=><div className="analytics-bar-row" key={`${r.feature_name}-${r.importance_type}`}><div className="analytics-bar-label"><code>{r.feature_name}</code><span>{r.importance_value.toFixed(4)}</span></div><div className="analytics-bar-track feature"><i style={{width:`${Math.max(2,Math.abs(r.importance_value)/max*100)}%`}}/></div></div>)}</div>;
}

export function AnalyticsClient() {
  const [catalog,setCatalog]=useState<Catalog|null>(null);
  const [filters,setFilters]=useState<Filters>(EMPTY_FILTERS);
  const [applied,setApplied]=useState<Filters>(EMPTY_FILTERS);
  const [data,setData]=useState<Overview|null>(null);
  const [loading,setLoading]=useState(true);
  const [error,setError]=useState('');

  useEffect(()=>{ fetch('/api/analytics?mode=catalog',{cache:'no-store'}).then(r=>r.ok?r.json():Promise.reject(new Error(`HTTP ${r.status}`))).then((c:Catalog)=>{setCatalog(c); const target=c.targets.includes('NET_INCOME_CANONICAL')?'NET_INCOME_CANONICAL':(c.targets[0]||'NET_INCOME_CANONICAL'); const f={...EMPTY_FILTERS,target,dateFrom:c.range.date_from||'',dateTo:c.range.date_to||''}; setFilters(f); setApplied(f);}).catch(e=>setError(String(e))); },[]);
  useEffect(()=>{ if(!catalog) return; setLoading(true); setError(''); const q=new URLSearchParams({mode:'overview',target_code:applied.target}); if(applied.model)q.set('model_name',applied.model); if(applied.ticker)q.set('ticker',applied.ticker); if(applied.sector)q.set('sector',applied.sector); if(applied.dateFrom)q.set('date_from',applied.dateFrom); if(applied.dateTo)q.set('date_to',applied.dateTo); fetch(`/api/analytics?${q.toString()}`,{cache:'no-store'}).then(r=>r.ok?r.json():r.json().then(j=>Promise.reject(new Error(j.detail||`HTTP ${r.status}`)))).then((d:Overview)=>setData(d)).catch(e=>setError(String(e))).finally(()=>setLoading(false)); },[catalog,applied]);

  const modelOptions=useMemo(()=>catalog?.models.filter(m=>m.target_code===filters.target).map(m=>m.model_name) || [],[catalog,filters.target]);
  const companyOptions=useMemo(()=>catalog?.companies.filter(c=>!filters.sector||c.sector===filters.sector) || [],[catalog,filters.sector]);
  const update=(key:keyof Filters,value:string)=>setFilters(prev=>({...prev,[key]:value,...(key==='target'?{model:''}:{})}));
  const reset=()=>{ if(!catalog)return; const target=catalog.targets.includes('NET_INCOME_CANONICAL')?'NET_INCOME_CANONICAL':(catalog.targets[0]||'NET_INCOME_CANONICAL'); const f={...EMPTY_FILTERS,target,dateFrom:catalog.range.date_from||'',dateTo:catalog.range.date_to||''}; setFilters(f); setApplied(f); };

  return <>
    <section className="panel analytics-filter-panel">
      <div className="panel-head"><div><p className="eyebrow">Filtry analizy</p><h2>Zdefiniuj zakres badania</h2></div><div className="analytics-mode"><span className="status-dot ok"/>Dane z PostgreSQL</div></div>
      <div className="analytics-filters">
        <label><span>Target</span><select value={filters.target} onChange={e=>update('target',e.target.value)}>{(catalog?.targets||[]).map(t=><option value={t} key={t}>{targetLabel(t)}</option>)}</select></label>
        <label><span>Model</span><select value={filters.model} onChange={e=>update('model',e.target.value)}><option value="">Champion automatycznie</option>{modelOptions.map(m=><option value={m} key={m}>{m}</option>)}</select></label>
        <label><span>Sektor</span><select value={filters.sector} onChange={e=>update('sector',e.target.value)}><option value="">Wszystkie sektory</option>{(catalog?.sectors||[]).map(s=><option value={s} key={s}>{s}</option>)}</select></label>
        <label><span>Spółka</span><select value={filters.ticker} onChange={e=>update('ticker',e.target.value)}><option value="">Wszystkie spółki</option>{companyOptions.map(c=><option value={c.ticker} key={c.ticker}>{c.ticker} — {c.name}</option>)}</select></label>
        <label><span>Data od</span><input type="date" value={filters.dateFrom} onChange={e=>update('dateFrom',e.target.value)}/></label>
        <label><span>Data do</span><input type="date" value={filters.dateTo} onChange={e=>update('dateTo',e.target.value)}/></label>
      </div>
      <div className="analytics-filter-actions"><button className="primary-btn" onClick={()=>setApplied(filters)}>Zastosuj filtry</button><button className="ghost-btn" onClick={reset}>Wyczyść</button><span>Dataset: <strong>{data?.dataset_version || '—'}</strong></span></div>
    </section>

    {error && <div className="browser-error">{error}</div>}
    {loading ? <div className="panel browser-loading">Przeliczanie dashboardu…</div> : data ? <>
      <section className="stats-row analytics-kpis">
        <div className="mini-stat"><span>Model</span><strong className="analytics-model-name">{data.selected_model?.model_name || '—'}</strong><small>{targetLabel(applied.target)}</small></div>
        <div className="mini-stat"><span>Obserwacje OOF</span><strong>{data.summary.observations}</strong><small>{data.summary.companies||0} spółek · {data.summary.periods||0} okresów</small></div>
        <div className="mini-stat"><span>MAE</span><strong>{fmtMoney(data.summary.mae)}</strong><small>średni błąd bezwzględny</small></div>
        <div className="mini-stat"><span>RMSE</span><strong>{fmtMoney(data.summary.rmse)}</strong><small>kara większe błędy</small></div>
        <div className="mini-stat"><span>sMAPE</span><strong>{fmtPct(data.summary.smape)}</strong><small>procentowy błąd symetryczny</small></div>
        <div className="mini-stat"><span>R²</span><strong>{fmtR2(data.summary.r2)}</strong><small>dopasowanie do zmienności targetu</small></div>
      </section>

      <section className="panel">
        <div className="panel-head"><div><p className="eyebrow">Actual vs predicted</p><h2>Rzeczywiste wyniki i prognoza w czasie</h2></div><span className="analytics-caption">Dla wielu spółek wartości są sumowane w kwartale; wybór jednej spółki pokazuje jej serię indywidualną.</span></div>
        <TrendChart rows={data.series}/>
      </section>

      <section className="analytics-two-col">
        <div className="panel"><div className="panel-head"><div><p className="eyebrow">Diagnostyka spółek</p><h2>Największy MAE</h2></div></div><ErrorBars rows={data.by_company}/></div>
        <div className="panel"><div className="panel-head"><div><p className="eyebrow">Porównanie modeli</p><h2>MAE na wspólnej próbce</h2></div></div><ModelComparison rows={data.model_comparison} selected={data.selected_model?.model_name}/></div>
      </section>

      <section className="analytics-two-col">
        <div className="panel"><div className="panel-head"><div><p className="eyebrow">Kalibracja wizualna</p><h2>Actual vs predicted — scatter</h2></div></div><ScatterChart rows={data.observations}/></div>
        <div className="panel"><div className="panel-head"><div><p className="eyebrow">Interpretowalność</p><h2>Feature importance</h2></div></div><FeatureImportance rows={data.feature_importance}/></div>
      </section>

      <section className="panel">
        <div className="panel-head"><div><p className="eyebrow">Błąd w czasie</p><h2>Metryki per okres ewaluacyjny</h2></div><span className="analytics-caption">Pokazuje stabilność modelu między kolejnymi foldami walk-forward.</span></div>
        <div className="table-scroll"><table className="model-table"><thead><tr><th>Okres</th><th>n</th><th>MAE</th><th>RMSE</th><th>sMAPE</th><th>R²</th></tr></thead><tbody>{data.by_period.map(r=><tr key={r.period}><td>{r.period}</td><td>{r.observations}</td><td>{fmtMoney(r.mae)}</td><td>{fmtMoney(r.rmse)}</td><td>{fmtPct(r.smape)}</td><td>{fmtR2(r.r2)}</td></tr>)}</tbody></table></div>
      </section>

      <section className="panel">
        <div className="panel-head"><div><p className="eyebrow">Rekordy ewaluacyjne</p><h2>Predykcje użyte w analizie</h2></div><a className="button secondary" href="/data-browser">Otwórz pełny podgląd danych</a></div>
        <div className="table-scroll"><table className="model-table"><thead><tr><th>Okres</th><th>Ticker</th><th>Sektor</th><th>Rzeczywiste</th><th>Prognoza</th><th>Błąd abs.</th><th>Cutoff</th></tr></thead><tbody>{data.observations.slice().reverse().slice(0,80).map(r=><tr key={r.id}><td>{r.target_period_end}</td><td>{r.ticker}</td><td>{r.sector}</td><td>{fmtMoney(r.actual_value)}</td><td>{fmtMoney(r.predicted_value)}</td><td>{fmtMoney(r.absolute_error)}</td><td>{String(r.cutoff_at).slice(0,10)}</td></tr>)}</tbody></table></div>
      </section>
    </> : null}
  </>;
}

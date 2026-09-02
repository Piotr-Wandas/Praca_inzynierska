import DataCoverageChart from '../components/DataCoverageChart';
import CompanyDataBars from '../components/CompanyDataBars';
import Link from 'next/link';

const API = process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
async function getJson(path:string){ try{ const r=await fetch(`${API}${path}`,{cache:'no-store'}); return r.ok?r.json():null; }catch{return null;} }
function n(v:any){return new Intl.NumberFormat('pl-PL').format(Number(v||0));}
function pct(v:any){return `${(Number(v||0)*100).toLocaleString('pl-PL',{maximumFractionDigits:1})}%`;}
function date(v:any){ return v ? String(v).slice(0,10) : '—'; }
function statusLabel(s:string){return s==='good'?'dobre':s==='warning'?'średnie':'niskie';}
function scopeLabel(s:string){return s==='financial'?'banki':s==='non_financial'?'spółki niefinansowe':'cały panel';}

export default async function DataPage(){
  const data=await getJson('/api/v1/data-preparation');
  const q=data?.quality?.dataset||{};
  const features=data?.quality?.features||[];
  const featureScopes=data?.quality?.feature_scope_summary||[];
  const companies=data?.companies||[];
  const quarters=(data?.quarters||[]).map((r:any)=>({label:`${r.year} Q${r.quarter}`,companies:Number(r.companies||0),target:Number(r.net_income_companies||0),revenue:Number(r.revenue_companies||0)}));
  const checks=data?.checks||{};
  return <main className="shell page-stack">
    <section className="page-header data-hero">
      <p className="eyebrow">Przygotowanie danych · v5.6</p><h1>Dane wejściowe i jakość datasetu</h1>
      <p className="lead compact">Profesjonalny podgląd całego procesu przed modelowaniem: źródła, zakres czasu, pokrycie spółek i kwartałów, mapowanie danych finansowych, braki, feature engineering oraz kontrole jakości.</p><div className="hero-actions"><Link className="primary-btn" href="/data-browser">Przeglądaj rekordy →</Link></div>
    </section>

    <section className="stats-row four">
      <div className="mini-stat"><span>Wiersze panelu</span><strong>{n(q.rows)}</strong><small>{n(q.companies)} spółek · {n(q.periods)} okresów</small></div>
      <div className="mini-stat"><span>Pokrycie targetu</span><strong>{pct(q.target_coverage)}</strong><small>zysk netto t+1</small></div>
      <div className="mini-stat"><span>Zakres fundamentów</span><strong className="date-stat">{date(data?.ranges?.fundamentals_from)}</strong><small>do {date(data?.ranges?.fundamentals_to)}</small></div>
      <div className="mini-stat"><span>Zakres notowań</span><strong className="date-stat">{date(data?.ranges?.market_from)}</strong><small>do {date(data?.ranges?.market_to)}</small></div>
    </section>

    <section className="panel">
      <div className="panel-head"><div><p className="eyebrow">ETL / preprocessing</p><h2>Jak dane są przygotowywane do modelowania?</h2></div></div>
      <div className="prep-pipeline">{(data?.pipeline||[]).map((p:any,i:number)=><div className="prep-step" key={p.step}><div className="prep-number">{p.step}</div><div><strong>{p.name}</strong><p>{p.detail}</p></div>{i<(data?.pipeline||[]).length-1&&<span className="prep-arrow">→</span>}</div>)}</div>
      <div className="notice">Kluczowa zasada: cecha może trafić do obserwacji tylko wtedy, gdy była dostępna w chwili <code>cutoff_at</code>. To ogranicza look-ahead bias.</div>
    </section>

    <section className="panel">
      <div className="panel-head"><div><p className="eyebrow">Pokrycie w czasie</p><h2>Ile spółek ma dane w poszczególnych kwartałach?</h2></div><span className={`quality-pill ${q.training_ready?'good':'poor'}`}>{q.training_ready?'gotowe':'wymaga danych'}</span></div>
      <DataCoverageChart data={quarters}/>
      <p className="tiny-note">Wykres pokazuje faktycznie zapisane dane w PostgreSQL. Linia zysku netto ujawnia okresy, które mogą wejść do targetu modelu.</p>
    </section>

    <section className="two-col data-two-col">
      <div className="panel">
        <div className="panel-head"><div><p className="eyebrow">Pokrycie per spółka</p><h2>Rynek vs historia fundamentalna</h2></div></div>
        <CompanyDataBars rows={companies}/>
      </div>
      <div className="panel">
        <div className="panel-head"><div><p className="eyebrow">Kontrole jakości</p><h2>Stan danych przed feature engineering</h2></div></div>
        <div className="quality-check-list">
          <div><span>Brakujący wolumen</span><strong>{n(checks.market_missing_volume)}</strong></div>
          <div><span>Daty proxy +120 dni</span><strong>{n(checks.proxy_120d_rows)}</strong></div>
          <div><span>Nierozpoznane etykiety z wartościami</span><strong>{n(checks.unmatched_mapping_labels)}</strong></div>
          <div><span>Bieżące fakty finansowe</span><strong>{n(checks.current_facts)}</strong></div>
          <div><span>Historyczne wersje faktów</span><strong>{n(checks.historical_fact_versions)}</strong></div>
        </div>
        <div className="notice warning-notice">Daty proxy pozostają elementem prototypowym. Finalna ewaluacja powinna korzystać z dokładnych dat raportów emitenta/ESPI/ESEF.</div>
      </div>
    </section>

    <section className="panel">
      <div className="panel-head"><div><p className="eyebrow">Feature engineering · v5.5</p><h2>Kompletność cech względem właściwej populacji</h2></div></div>
      <p className="lead compact feature-scope-explainer">Brak cechy sektorowej poza jej zakresem nie jest traktowany jako brak jakości. Wynik odsetkowy jest oceniany tylko dla banków, a przychody operacyjne dla spółek niefinansowych. Dzięki temu wskaźnik pokrycia nie jest sztucznie zaniżany.</p>
      <div className="feature-scope-cards">{featureScopes.map((g:any)=><div className="feature-scope-card" key={g.scope}><span>{scopeLabel(g.scope)}</span><strong>{pct(g.avg_coverage)}</strong><small>{n(g.eligible_rows)} obserwacji · {n(g.eligible_companies)} spółek</small><div className="scope-status-row"><b>{g.good_features||0} dobre</b><b>{g.warning_features||0} średnie</b><b>{g.poor_features||0} niskie</b></div></div>)}</div>
      <div className="feature-quality-grid sector-aware">{features.map((f:any)=><div className="feature-quality-row" key={f.feature}>
        <div className="feature-quality-title"><div><code>{f.feature}</code><span className={`scope-badge ${f.scope}`}>{scopeLabel(f.scope)}</span></div><span>{pct(f.coverage)}</span></div>
        <div className="quality-track"><div className={`quality-fill ${f.status}`} style={{width:`${Math.max(0,Math.min(100,Number(f.coverage||0)*100))}%`}}/></div>
        <div className="feature-quality-meta"><span>{n(f.observed)} / {n(f.eligible_rows)} właściwych obserwacji</span><span className={`quality-text ${f.status}`}>{statusLabel(f.status)}</span></div>
        {f.scope!=='all'&&<div className="feature-global-note">Dla porównania: {pct(f.global_coverage)} względem całego panelu.</div>}
      </div>)}</div>
      <div className="notice">v5.5 rozróżnia <strong>brak strukturalny</strong> od rzeczywistego braku danych. Cechy sektorowe nie są już medianowo imputowane spółkom, dla których nie mają znaczenia.</div>
    </section>

    <section className="panel">
      <div className="panel-head"><div><p className="eyebrow">Dane fundamentalne</p><h2>Pokrycie konceptów finansowych</h2></div></div>
      <div className="table-scroll"><table className="model-table"><thead><tr><th>Koncept</th><th>Nazwa</th><th>Zakres</th><th>Wiersze</th><th>Spółki</th><th>Okresy</th><th>Pierwszy</th><th>Ostatni</th></tr></thead><tbody>{(data?.concepts||[]).map((r:any)=><tr key={r.code}><td><code>{r.code}</code></td><td>{r.name_pl}</td><td>{r.applicable_to}</td><td>{n(r.rows)}</td><td>{n(r.companies)}</td><td>{n(r.periods)}</td><td>{date(r.first_period)}</td><td>{date(r.last_period)}</td></tr>)}</tbody></table></div>
    </section>

    <section className="two-col data-two-col">
      <div className="panel"><div className="panel-head"><div><p className="eyebrow">Makroekonomia</p><h2>Serie dostępne w bazie</h2></div></div><div className="table-scroll"><table className="model-table"><thead><tr><th>Seria</th><th>Częstotliwość</th><th>Wiersze</th><th>Zakres</th></tr></thead><tbody>{(data?.macro_series||[]).map((r:any)=><tr key={r.code}><td><strong>{r.code}</strong><div className="tiny-note">{r.name}</div></td><td>{r.frequency}</td><td>{n(r.rows)}</td><td>{date(r.first_date)} → {date(r.last_date)}</td></tr>)}</tbody></table></div></div>
      <div className="panel"><div className="panel-head"><div><p className="eyebrow">Rekomendacje</p><h2>Co poprawić przed interpretacją modelu?</h2></div></div><div className="recommendation-list">{(data?.quality?.recommendations||[]).map((r:string,i:number)=><div className="recommendation-item" key={i}>{r}</div>)}</div></div>
    </section>
  </main>;
}

'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';

type DatasetMeta = { code:string; label:string; description:string; date_field:string; default_sort:string; columns:string[] };
type Catalog = {
  datasets: DatasetMeta[];
  tickers: {ticker:string;name:string;sector:string}[];
  concepts: {code:string;name:string;applicable_to:string}[];
  macro_series: {code:string;name:string;frequency:string;source_code:string}[];
  limits?: {max_page_size:number;max_export_rows:number};
};
type Result = {dataset:string;label:string;description:string;columns:string[];rows:Record<string,any>[];total:number;page:number;page_size:number;pages:number;sort:string;order:string};

const numberFormatter = new Intl.NumberFormat('pl-PL', { maximumFractionDigits: 4 });
const compactFormatter = new Intl.NumberFormat('pl-PL', { notation:'compact', maximumFractionDigits:2 });

function displayName(key:string){
  const names:Record<string,string>={
    ticker:'Ticker', company:'Spółka', sector:'Sektor', trade_date:'Data sesji', open:'Otwarcie', high:'Max', low:'Min', close:'Zamknięcie', adjusted_close:'Skorygowane', volume:'Wolumen', available_at:'Dostępne od',
    concept_code:'Koncept', concept_name:'Nazwa konceptu', value:'Wartość', unit:'Jednostka', period_start:'Początek okresu', period_end:'Koniec okresu', period_type:'Typ okresu', publication_date:'Publikacja', source_label:'Etykieta źródłowa', source_concept:'Koncept źródłowy', revision_no:'Rewizja', is_current:'Bieżąca',
    series_code:'Seria', series_name:'Nazwa serii', observation_date:'Data obserwacji', frequency:'Częstotliwość', source_code:'Źródło', cutoff_at:'Cutoff', NET_INCOME_CANONICAL:'Zysk netto', REVENUE:'Przychody', target_net_income:'Target zysk t+1', target_revenue:'Target przychody t+1', net_income_lag1:'Zysk lag1', net_income_lag4:'Zysk lag4', net_income_yoy:'Zysk YoY', revenue_lag1:'Przychody lag1', revenue_lag4:'Przychody lag4', revenue_yoy:'Przychody YoY', return_20d:'Zwrot 20d', return_60d:'Zwrot 60d', volatility_20d:'Zmienność 20d', volume_ratio_20d:'Rel. wolumen', fx_eurpln:'EUR/PLN', fx_usdpln:'USD/PLN', fx_chfpln:'CHF/PLN', net_income_source:'Źródło zysku', target_source_concept:'Źródło targetu'
  };
  return names[key] || key.replaceAll('_',' ');
}
function formatCell(key:string,value:any){
  if(value===null||value===undefined||value==='') return <span className="null-value">NULL</span>;
  if(typeof value==='boolean') return value?'tak':'nie';
  if(typeof value==='number'){
    if(['value','volume','NET_INCOME_CANONICAL','REVENUE','target_net_income','target_revenue','net_income_lag1','net_income_lag4','revenue_lag1','revenue_lag4'].includes(key)) return Math.abs(value)>=100000 ? compactFormatter.format(value) : numberFormatter.format(value);
    if(['return_20d','return_60d','volatility_20d','volume_ratio_20d','net_income_yoy','revenue_yoy'].includes(key)) return numberFormatter.format(value);
    return numberFormatter.format(value);
  }
  const text=String(value);
  if(/date|_at|period/.test(key) && /^\d{4}-\d{2}-\d{2}/.test(text)) return text.slice(0,10)+(text.includes('T')?` ${text.slice(11,16)}`:'');
  return text;
}
function csvEscape(value:any){ const s=value==null?'':String(value); return `"${s.replaceAll('"','""')}"`; }

export default function DataBrowserClient(){
  const [catalog,setCatalog]=useState<Catalog|null>(null);
  const [result,setResult]=useState<Result|null>(null);
  const [loading,setLoading]=useState(true);
  const [error,setError]=useState('');
  const [dataset,setDataset]=useState('fundamentals');
  const [ticker,setTicker]=useState('');
  const [concept,setConcept]=useState('');
  const [series,setSeries]=useState('');
  const [dateFrom,setDateFrom]=useState('');
  const [dateTo,setDateTo]=useState('');
  const [search,setSearch]=useState('');
  const [includeHistory,setIncludeHistory]=useState(false);
  const [hasTarget,setHasTarget]=useState(false);
  const [pageSize,setPageSize]=useState(50);
  const [sort,setSort]=useState('');
  const [order,setOrder]=useState<'asc'|'desc'>('desc');
  const [page,setPage]=useState(1);

  const meta=useMemo(()=>catalog?.datasets.find(d=>d.code===dataset),[catalog,dataset]);

  const buildParams=useCallback((pageOverride?:number,sortOverride?:string,orderOverride?:'asc'|'desc')=>{
    const p=new URLSearchParams({dataset,page:String(pageOverride||page),page_size:String(pageSize),order:orderOverride||order});
    const s=sortOverride ?? sort;
    if(s)p.set('sort',s); if(ticker)p.set('ticker',ticker); if(concept&&dataset==='fundamentals')p.set('concept',concept); if(series&&dataset==='macro')p.set('series',series);
    if(dateFrom)p.set('date_from',dateFrom); if(dateTo)p.set('date_to',dateTo); if(search)p.set('search',search);
    if(includeHistory&&dataset==='fundamentals')p.set('include_history','true'); if(hasTarget&&dataset==='panel')p.set('has_target','true');
    return p;
  },[dataset,page,pageSize,order,sort,ticker,concept,series,dateFrom,dateTo,search,includeHistory,hasTarget]);

  const load=useCallback(async(pageOverride?:number,sortOverride?:string,orderOverride?:'asc'|'desc')=>{
    setLoading(true);setError('');
    try{
      const r=await fetch(`/api/data-browser?${buildParams(pageOverride,sortOverride,orderOverride).toString()}`,{cache:'no-store'});
      const json=await r.json(); if(!r.ok)throw new Error(json.detail||'Nie udało się pobrać danych');
      setResult(json); setPage(json.page); setSort(json.sort); setOrder(json.order);
    }catch(e:any){setError(e?.message||String(e));}finally{setLoading(false);}
  },[buildParams]);

  useEffect(()=>{(async()=>{try{const r=await fetch('/api/data-browser?mode=catalog',{cache:'no-store'});const j=await r.json();setCatalog(j);}catch(e:any){setError(String(e));}})();},[]);
  useEffect(()=>{ if(catalog) load(1); },[catalog,dataset]); // intentionally reload on dataset only

  async function resetFilters(){
    setTicker('');setConcept('');setSeries('');setDateFrom('');setDateTo('');setSearch('');setIncludeHistory(false);setHasTarget(false);setSort(meta?.default_sort||'');setOrder('desc');setPage(1);
    setLoading(true);setError('');
    try{
      const p=new URLSearchParams({dataset,page:'1',page_size:String(pageSize),order:'desc'});
      if(meta?.default_sort)p.set('sort',meta.default_sort);
      const r=await fetch(`/api/data-browser?${p.toString()}`,{cache:'no-store'});
      const json=await r.json(); if(!r.ok)throw new Error(json.detail||'Nie udało się pobrać danych');
      setResult(json);setPage(json.page);setSort(json.sort);setOrder(json.order);
    }catch(e:any){setError(e?.message||String(e));}finally{setLoading(false);}
  }
  function changeDataset(code:string){setDataset(code);setTicker('');setConcept('');setSeries('');setDateFrom('');setDateTo('');setSearch('');setIncludeHistory(false);setHasTarget(false);setSort(catalog?.datasets.find(d=>d.code===code)?.default_sort||'');setOrder('desc');setPage(1);}
  function headerSort(col:string){const nextOrder=sort===col&&order==='desc'?'asc':'desc';setSort(col);setOrder(nextOrder);load(1,col,nextOrder);}
  function exportPage(){if(!result?.rows.length)return;const cols=result.columns;const csv=[cols.map(csvEscape).join(';'),...result.rows.map(r=>cols.map(c=>csvEscape(r[c])).join(';'))].join('\n');const blob=new Blob(['\uFEFF'+csv],{type:'text/csv;charset=utf-8'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=`${dataset}_page_${result.page}.csv`;a.click();URL.revokeObjectURL(url);}

  return <>
    <section className="panel browser-toolbar-panel">
      <div className="panel-head browser-head"><div><p className="eyebrow">Źródło danych</p><h2>{meta?.label||'Wybierz zbiór'}</h2><p className="tiny-note browser-description">{meta?.description}</p></div><div className="browser-actions"><button className="secondary-btn" onClick={exportPage} disabled={!result?.rows?.length}>Eksport strony CSV</button></div></div>
      <div className="dataset-tabs">{catalog?.datasets.map(d=><button key={d.code} className={dataset===d.code?'active':''} onClick={()=>changeDataset(d.code)}>{d.label}</button>)}</div>
      <div className="browser-filters">
        <label><span>Szukaj</span><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="ticker, spółka, etykieta…" /></label>
        {dataset!=='macro'&&<label><span>Spółka</span><select value={ticker} onChange={e=>setTicker(e.target.value)}><option value="">Wszystkie</option>{catalog?.tickers.map(t=><option key={t.ticker} value={t.ticker}>{t.ticker} — {t.name}</option>)}</select></label>}
        {dataset==='fundamentals'&&<label><span>Koncept</span><select value={concept} onChange={e=>setConcept(e.target.value)}><option value="">Wszystkie</option>{catalog?.concepts.map(c=><option key={c.code} value={c.code}>{c.code} — {c.name}</option>)}</select></label>}
        {dataset==='macro'&&<label><span>Seria</span><select value={series} onChange={e=>setSeries(e.target.value)}><option value="">Wszystkie</option>{catalog?.macro_series.map(s=><option key={s.code} value={s.code}>{s.code} — {s.name}</option>)}</select></label>}
        <label><span>Data od</span><input type="date" value={dateFrom} onChange={e=>setDateFrom(e.target.value)} /></label>
        <label><span>Data do</span><input type="date" value={dateTo} onChange={e=>setDateTo(e.target.value)} /></label>
        <label><span>Wierszy na stronę</span><select value={pageSize} onChange={e=>setPageSize(Number(e.target.value))}><option>25</option><option>50</option><option>100</option><option>200</option></select></label>
      </div>
      <div className="browser-filter-footer">
        <div className="browser-checks">
          {dataset==='fundamentals'&&<label className="check-label"><input type="checkbox" checked={includeHistory} onChange={e=>setIncludeHistory(e.target.checked)}/> Pokaż historyczne wersje faktów</label>}
          {dataset==='panel'&&<label className="check-label"><input type="checkbox" checked={hasTarget} onChange={e=>setHasTarget(e.target.checked)}/> Tylko rekordy ze znanym targetem zysku t+1</label>}
        </div>
        <div className="browser-buttons"><button className="ghost-btn" onClick={resetFilters}>Wyczyść</button><button className="primary-btn" onClick={()=>load(1)}>Zastosuj filtry</button></div>
      </div>
    </section>

    <section className="panel data-grid-panel">
      <div className="panel-head browser-result-head"><div><p className="eyebrow">Rekordy</p><h2>{result?`${result.total.toLocaleString('pl-PL')} rekordów`:'Ładowanie danych'}</h2></div>{result&&<div className="browser-result-meta"><span>Strona <strong>{result.page}</strong> / {result.pages}</span><span>Sortowanie: <strong>{displayName(result.sort)}</strong> {result.order==='asc'?'↑':'↓'}</span></div>}</div>
      {error&&<div className="browser-error">{error}</div>}
      {loading?<div className="browser-loading">Pobieranie rekordów z PostgreSQL…</div>:result?.rows?.length?<div className="data-table-wrap"><table className="data-browser-table"><thead><tr>{result.columns.map(c=><th key={c}><button onClick={()=>headerSort(c)} title={`Sortuj po: ${displayName(c)}`}>{displayName(c)} {result.sort===c?<b>{result.order==='asc'?'↑':'↓'}</b>:<i>↕</i>}</button></th>)}</tr></thead><tbody>{result.rows.map((row,i)=><tr key={i}>{result.columns.map(c=><td key={c} title={row[c]==null?'NULL':String(row[c])}>{formatCell(c,row[c])}</td>)}</tr>)}</tbody></table></div>:!error&&<div className="empty-chart">Brak rekordów spełniających wybrane filtry.</div>}
      {result&&<div className="pagination"><button disabled={result.page<=1||loading} onClick={()=>load(result.page-1)}>← Poprzednia</button><div><strong>{result.page}</strong><span>z {result.pages}</span></div><button disabled={result.page>=result.pages||loading} onClick={()=>load(result.page+1)}>Następna →</button></div>}
    </section>

    <section className="two-col browser-help-grid">
      <div className="panel"><p className="eyebrow">Jak czytać dane?</p><h2>Od rekordu źródłowego do modelu</h2><p className="lead compact">Zakładki <strong>Notowania</strong>, <strong>Fundamenty</strong> i <strong>Makro</strong> pokazują dane zapisane w warstwie <code>core</code>. <strong>Dataset modelowy</strong> pokazuje już wynik point-in-time join oraz feature engineering.</p><div className="notice">Kliknięcie nagłówka kolumny zmienia sortowanie. Filtry są wykonywane po stronie API i PostgreSQL; interfejs nie pobiera całej tabeli do przeglądarki.</div></div>
      <div className="panel"><p className="eyebrow">Interpretacja braków</p><h2><span className="null-value">NULL</span> nie zawsze oznacza błąd</h2><p className="lead compact">Brak może wynikać z braku publikacji, niewystarczającej historii dla <code>lag4</code>, strukturalnej nieadekwatności cechy sektorowej albo z faktu, że target t+1 nie jest jeszcze znany.</p><p className="tiny-note">Do oceny jakości korzystaj równolegle z zakładki „Dane”, która liczy kompletność względem właściwej populacji.</p></div>
    </section>
  </>;
}

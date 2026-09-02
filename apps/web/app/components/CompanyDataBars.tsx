type Row = { ticker:string; market_rows:number; fundamental_periods:number; net_income_rows:number };
export default function CompanyDataBars({ rows }:{rows:Row[]}){
  const maxMarket=Math.max(1,...rows.map(r=>Number(r.market_rows||0)));
  const maxPeriods=Math.max(1,...rows.map(r=>Number(r.fundamental_periods||0)));
  return <div className="company-data-bars">{rows.map(r=><div className="company-data-row" key={r.ticker}>
    <strong>{r.ticker}</strong>
    <div className="company-data-metric"><span>Rynek <b>{Number(r.market_rows||0).toLocaleString('pl-PL')}</b></span><div className="data-track"><i style={{width:`${Number(r.market_rows||0)/maxMarket*100}%`}}/></div></div>
    <div className="company-data-metric"><span>Kwartały <b>{r.fundamental_periods||0}</b></span><div className="data-track alt"><i style={{width:`${Number(r.fundamental_periods||0)/maxPeriods*100}%`}}/></div></div>
    <div className="company-data-metric compact"><span>Zysk netto <b>{r.net_income_rows||0}</b></span></div>
  </div>)}</div>
}

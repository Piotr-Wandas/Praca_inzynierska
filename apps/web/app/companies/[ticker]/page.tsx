import Link from "next/link";
import { notFound } from "next/navigation";
import { LineChart } from "../../components/LineChart";

const API = process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function getCompany(ticker:string) {
  try {
    const res = await fetch(`${API}/api/v1/dashboard/company/${ticker}`, { cache: "no-store" });
    if (res.status === 404) return null;
    if (!res.ok) return null;
    return await res.json();
  } catch { return null; }
}

function mln(value:any) {
  if (value === null || value === undefined) return "—";
  return `${(Number(value) / 1_000_000).toLocaleString("pl-PL", { maximumFractionDigits: 1 })} mln PLN`;
}

export default async function CompanyDetailsPage({ params }: { params: Promise<{ ticker: string }> }) {
  const { ticker } = await params;
  const data = await getCompany(ticker.toUpperCase());
  if (!data) notFound();
  const preds = data.predictions || [];
  const preferred = preds.filter((x:any) => x.model_name === "hist_gradient_boosting");
  const chosen = preferred.length ? preferred : preds;
  const series = chosen.slice(-12).map((x:any) => ({
    quarter: String(x.target_period_end).slice(0, 10),
    actual: Number(x.actual_value || 0) / 1_000_000,
    predicted: Number(x.predicted_value || 0) / 1_000_000,
  }));
  const latest = chosen.length ? chosen[chosen.length - 1] : null;
  const recentFinancials = (data.financials || []).slice(-12).reverse();

  return (
    <main className="shell page-stack">
      <div className="breadcrumb"><Link href="/companies">Spółki</Link><span>›</span><span>{data.company.name}</span></div>
      <section className="company-hero">
        <div className="company-avatar large">{data.company.ticker}</div>
        <div><p className="eyebrow">{data.company.sector || "GPW"}</p><h1>{data.company.name}</h1><p className="lead compact">Dane finansowe, notowania oraz wyniki predykcji są pobierane z PostgreSQL.</p></div>
      </section>
      <section className="stats-row four">
        <div className="mini-stat"><span>Target</span><strong>Zysk netto t+1</strong></div>
        <div className="mini-stat"><span>Notowania</span><strong>{data.prices?.length || 0}</strong></div>
        <div className="mini-stat"><span>Ostatnia prognoza</span><strong>{mln(latest?.predicted_value)}</strong></div>
        <div className="mini-stat"><span>Błąd abs.</span><strong>{mln(latest?.absolute_error)}</strong></div>
      </section>
      <section className="two-col">
        <article className="panel wide-panel">
          <div className="panel-head"><div><p className="eyebrow">Walidacja walk-forward</p><h2>Rzeczywiste vs prognozowane</h2></div><span className="tag">PostgreSQL</span></div>
          {series.length >= 2 ? <LineChart data={series} /> : <p className="tiny-note">Brak zapisanych predykcji. Uruchom trening modeli po pobraniu danych.</p>}
        </article>
        <article className="panel">
          <div className="panel-head"><div><p className="eyebrow">Dane wejściowe</p><h2>Ostatnie fakty finansowe</h2></div></div>
          <div className="table-scroll"><table className="model-table"><thead><tr><th>Okres</th><th>Pozycja</th><th>Wartość</th></tr></thead><tbody>
            {recentFinancials.map((x:any, i:number) => <tr key={`${x.period_end}-${x.concept}-${i}`}><td>{String(x.period_end)}</td><td>{x.concept}</td><td>{mln(x.value)}</td></tr>)}
          </tbody></table></div>
        </article>
      </section>
      <div className="notice">Źródło fundamentalne Yahoo Finance jest używane jako warstwa prototypowa. Rekordy z zastępczą datą dostępności są oznaczone w <code>source_label</code>; przed finalnym eksperymentem należy je zweryfikować raportami emitenta/ESPI/ESEF.</div>
    </main>
  );
}

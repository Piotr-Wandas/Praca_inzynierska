import Link from "next/link";

const API = process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function getCompanies() {
  try {
    const res = await fetch(`${API}/api/v1/dashboard/companies`, { cache: "no-store" });
    if (!res.ok) return [];
    return await res.json();
  } catch { return []; }
}

export default async function CompaniesPage() {
  const companies = await getCompanies();
  return (
    <main className="shell page-stack">
      <section className="page-header">
        <p className="eyebrow">Uniwersum badawcze</p>
        <h1>Spółki zapisane w PostgreSQL</h1>
        <p className="lead compact">Lista jest odczytywana z bazy przez FastAPI. Wersja pilotażowa służy uruchomieniu pełnego pipeline&apos;u; historyczny skład WIG20 powinien być później uzupełniony w <code>core.index_membership</code>.</p>
      </section>
      <section className="stats-row">
        <div className="mini-stat"><span>Spółki</span><strong>{companies.length}</strong></div>
        <div className="mini-stat"><span>Z danymi rynkowymi</span><strong>{companies.filter((x:any) => Number(x.price_rows) > 0).length}</strong></div>
        <div className="mini-stat"><span>Z danymi finansowymi</span><strong>{companies.filter((x:any) => Number(x.fundamental_rows) > 0).length}</strong></div>
      </section>
      <section className="company-grid">
        {companies.map((company:any) => (
          <Link className="company-card" href={`/companies/${company.ticker}`} key={company.ticker}>
            <div className="company-avatar">{company.ticker}</div>
            <div className="company-copy">
              <div className="company-topline"><h2>{company.name}</h2><span className="tag">{company.sector || "—"}</span></div>
              <p>Notowania: {company.price_rows || 0} · fakty finansowe: {company.fundamental_rows || 0} · ostatni raport: {company.last_report_period || "—"}</p>
              <span className="card-link">Otwórz analizę <b>→</b></span>
            </div>
          </Link>
        ))}
      </section>
      {!companies.length && <div className="notice">Brak spółek w bazie. Uruchom <code>python scripts/ingest_internet_data.py --start-year 2018</code>.</div>}
    </main>
  );
}

import DataBrowserClient from '../components/DataBrowserClient';

export default function DataBrowserPage() {
  return <main className="shell page-stack">
    <section className="page-header data-browser-hero">
      <p className="eyebrow">Eksplorator danych · v5.6</p>
      <h1>Podgląd danych źródłowych i modelowych</h1>
      <p className="lead compact">Przeglądaj rekordy zapisane w PostgreSQL, filtruj je po spółce, koncepcie i zakresie dat, sortuj po dowolnej dostępnej kolumnie oraz sprawdzaj dokładnie, na jakich danych wykonywane jest modelowanie.</p>
    </section>
    <DataBrowserClient />
  </main>;
}

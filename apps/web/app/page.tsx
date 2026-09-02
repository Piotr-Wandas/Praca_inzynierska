import Link from 'next/link';

export default async function Home() {
  const api = process.env.INTERNAL_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
  let health: { status?: string; stage?: string } = { status: 'offline' };
  try {
    health = await fetch(`${api}/api/v1/system/health`, { cache: 'no-store' }).then((response) => response.json());
  } catch {
    health = { status: 'offline' };
  }
  const online = health.status === 'ok';

  return (
    <main className="shell">
      <section className="hero hero-split">
        <div>
          <p className="eyebrow">Prototyp · II semestr</p>
          <h1>Predykcja wyników finansowych spółek WIG20</h1>
          <p className="lead">Platforma łączy dane fundamentalne, rynkowe i makroekonomiczne, tworząc poprawne czasowo zbiory cech do prognozy kolejnego kwartału.</p>
          <div className="hero-actions">
            <Link className="button primary" href="/companies">Przeglądaj spółki</Link>
            <Link className="button secondary" href="/models">Porównaj modele</Link>
            <Link className="button secondary" href="/dashboard">Dashboard</Link>
          </div>
        </div>
        <aside className="hero-status-card">
          <span className={`status-dot ${online ? 'ok' : ''}`} />
          <strong>API {online ? 'online' : 'offline'}</strong>
          <p>FastAPI · PostgreSQL · Prefect · MLflow</p>
        </aside>
      </section>

      <section className="grid" aria-label="Najważniejsze parametry projektu">
        <article className="card"><p className="card-label">Rynek</p><p className="card-value">GPW / WIG20</p><p className="card-note">Historia członkostwa w indeksie będzie przechowywana w bazie.</p></article>
        <article className="card"><p className="card-label">Horyzont</p><p className="card-value">t + 1 kwartał</p><p className="card-note">Prognoza kolejnego raportowanego okresu.</p></article>
        <article className="card"><p className="card-label">Walidacja</p><p className="card-value">Walk-forward</p><p className="card-note">Chronologiczna ocena bez losowego mieszania danych.</p></article>
        <article className="card"><p className="card-label">Kontrola czasu</p><p className="card-value">Point-in-time</p><p className="card-note">Tylko informacje dostępne w chwili historycznej prognozy.</p></article>
      </section>

      <section className="section">
        <div className="section-heading"><div><p className="eyebrow">Architektura</p><h2>Przepływ danych</h2></div></div>
        <div className="pipeline">
          {['Źródła danych', 'RAW', 'Walidacja', 'PostgreSQL', 'Feature engineering', 'Model ML', 'Predykcja'].map((step, index, array) => (
            <span className="pipeline-pair" key={step}><span className="pipeline-step">{step}</span>{index < array.length - 1 && <span className="arrow">→</span>}</span>
          ))}
        </div>
      </section>

      <section className="section quick-links">
        <Link href="/companies" className="feature-link"><span className="icon-box">20</span><div><strong>Spółki WIG20</strong><p>Lista spółek i przejście do szczegółów, prognoz oraz wykresów.</p></div><span>→</span></Link>
        <Link href="/models" className="feature-link"><span className="icon-box">ML</span><div><strong>Porównanie modeli</strong><p>Baseline, regresja i boosting z metrykami zapisanymi w PostgreSQL.</p></div><span>→</span></Link>
        <Link href="/dashboard" className="feature-link"><span className="icon-box">DB</span><div><strong>Dashboard analityczny</strong><p>Pokrycie danych, historia ETL i wyniki modeli odczytywane z bazy.</p></div><span>→</span></Link>
      </section>

      <div className="notice"><strong>Informacja:</strong> dashboard może pracować na rzeczywistych danych pobranych do PostgreSQL. Dane fundamentalne Yahoo w tej wersji są źródłem prototypowym; finalne daty publikacji należy zweryfikować w raportach emitenta/ESPI/ESEF.</div>
    </main>
  );
}

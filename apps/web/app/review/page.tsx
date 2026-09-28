import Link from 'next/link';

async function readJson(path: string) {
  const api = process.env.INTERNAL_API_URL ?? 'http://api:8000';
  try {
    const response = await fetch(`${api}${path}`, { cache: 'no-store' });
    if (!response.ok) return null;
    return response.json();
  } catch { return null; }
}

export default async function ReviewPage() {
  const [review, summary, models] = await Promise.all([
    readJson('/api/v1/review/info'),
    readJson('/api/v1/dashboard/summary'),
    readJson('/api/v1/dashboard/models?latest=true&target_code=NET_INCOME_CANONICAL'),
  ]);
  const snap = review?.snapshot ?? {};
  const modelRows = Array.isArray(models) ? models : [];
  return (
    <main className="shell">
      <section className="hero">
        <p className="eyebrow">v6.1 · INTERACTIVE ANALYTICS REVIEW</p>
        <h1>Wersja przygotowana do oceny pracy</h1>
        <p className="lead">System działa na zamrożonym snapshotcie danych i zapisanych wynikach eksperymentów. Prowadzący może od razu przejść do jakości danych, konkretnych rekordów, interaktywnych analiz i ewaluacji modeli.</p>
      </section>

      <section className="grid">
        <article className="card"><p className="card-label">Snapshot</p><p className="card-value">{snap.prepared ? 'Gotowy' : 'Nieprzygotowany'}</p><p className="card-note">{snap.dataset_version ?? 'brak wersji datasetu'}</p></article>
        <article className="card"><p className="card-label">Spółki</p><p className="card-value">{summary?.companies ?? 0}</p><p className="card-note">rekordy podmiotów w PostgreSQL</p></article>
        <article className="card"><p className="card-label">Notowania</p><p className="card-value">{Number(summary?.market_rows ?? 0).toLocaleString('pl-PL')}</p><p className="card-note">dziennych obserwacji rynkowych</p></article>
        <article className="card"><p className="card-label">Treningi</p><p className="card-value">{modelRows.length}</p><p className="card-note">modeli w najnowszej wspólnej ewaluacji</p></article>
      </section>

      <section className="section">
        <div className="section-heading"><div><p className="eyebrow">Ścieżka prezentacji</p><h2>Co warto sprawdzić</h2></div></div>
        <div className="review-links">
          <Link className="feature-link" href="/data"><span className="icon-box">01</span><div><strong>Przygotowanie i jakość danych</strong><p>Źródła, zakresy, kompletność, point-in-time oraz feature engineering.</p></div><span>→</span></Link>
          <Link className="feature-link" href="/data-browser"><span className="icon-box">02</span><div><strong>Podgląd rzeczywistych rekordów</strong><p>Filtrowanie i sortowanie danych rynkowych, fundamentalnych, makro oraz panelu modelowego.</p></div><span>→</span></Link>
          <Link className="feature-link" href="/analytics"><span className="icon-box">03</span><div><strong>Interaktywne analizy</strong><p>Filtry target/model/spółka/sektor/okres, actual vs predicted, błędy i interpretowalność.</p></div><span>→</span></Link>
          <Link className="feature-link" href="/models"><span className="icon-box">04</span><div><strong>Formalne porównanie modeli</strong><p>Wspólna próbka OOF, walk-forward i pełne metryki modeli.</p></div><span>→</span></Link>
          <Link className="feature-link" href="/dashboard"><span className="icon-box">05</span><div><strong>Dashboard techniczny</strong><p>Stan pipeline'u, jakość datasetu, treningi i diagnostyka.</p></div><span>→</span></Link>
        </div>
      </section>

      <section className="section">
        <div className="section-heading"><div><p className="eyebrow">Reprodukowalność</p><h2>Metadane snapshotu</h2></div></div>
        <div className="code-panel">
          <p><strong>Release:</strong> {review?.release ?? 'v6.1 INTERACTIVE ANALYTICS REVIEW'}</p>
          <p><strong>Utworzono:</strong> {snap.created_at ?? '—'}</p>
          <p><strong>Dataset:</strong> {snap.dataset_version ?? '—'}</p>
          <p><strong>Fakty finansowe:</strong> {snap.fundamental_rows ?? summary?.fundamental_rows ?? 0}</p>
          <p><strong>Dane makro:</strong> {snap.macro_rows ?? summary?.macro_rows ?? 0}</p>
        </div>
      </section>
      <div className="notice"><strong>Tryb REVIEW:</strong> dane i wyniki są celowo zamrożone, aby ocena była reprodukowalna i niezależna od chwilowej dostępności serwisów zewnętrznych.</div>
    </main>
  );
}

import { AnalyticsClient } from '../components/AnalyticsClient';

export default function AnalyticsPage() {
  return (
    <main className="shell page-stack">
      <section className="page-header analytics-hero">
        <p className="eyebrow">Interaktywny dashboard analityczny · v6.1</p>
        <h1>Analiza wyników modeli</h1>
        <p className="lead compact">
          Filtruj target, model, spółkę, sektor i okres. Wykresy oraz metryki są przeliczane na podstawie
          predykcji zapisanych w PostgreSQL, bez ręcznie wpisanych danych demonstracyjnych.
        </p>
      </section>
      <AnalyticsClient />
    </main>
  );
}

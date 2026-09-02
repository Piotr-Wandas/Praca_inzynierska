const API = process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function getJson(path: string) {
  try {
    const res = await fetch(`${API}${path}`, { cache: "no-store" });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

function n(value: any) {
  return new Intl.NumberFormat("pl-PL").format(Number(value || 0));
}
function pct(value: any) {
  return `${(Number(value || 0) * 100).toLocaleString("pl-PL", { maximumFractionDigits: 1 })}%`;
}
function money(value: any) {
  const v = Number(value);
  if (!Number.isFinite(v)) return "—";
  return new Intl.NumberFormat("pl-PL", { notation: "compact", maximumFractionDigits: 2 }).format(v);
}
function statusLabel(status: string) {
  if (status === "good") return "dobre";
  if (status === "warning") return "średnie";
  if (status === "poor") return "niskie";
  return "brak";
}

export default async function DashboardPage() {
  const [summary, companies, models, runs, quality, diagnostics] = await Promise.all([
    getJson("/api/v1/dashboard/summary"),
    getJson("/api/v1/dashboard/companies"),
    getJson("/api/v1/dashboard/models"),
    getJson("/api/v1/dashboard/ingestion-runs?limit=8"),
    getJson("/api/v1/dashboard/data-quality"),
    getJson("/api/v1/dashboard/model-diagnostics"),
  ]);

  const q = quality?.dataset || {};
  const target = quality?.target_provenance || {};
  const champion = summary?.champion;
  const bestCompanyRows = (diagnostics?.by_company || []).filter((r: any) => r.model_name === champion?.model_name);

  return (
    <main className="site-shell shell page-stack">
      <section className="page-header">
        <p className="eyebrow">Dashboard analityczny · v5.3 DATA FIX</p>
        <h1>Dane, mapowanie, jakość i modele</h1>
        <p className="lead compact">
          v5.3 pokazuje nie tylko pokrycie danych, ale również audyt mapowania surowych nazw pozycji finansowych,
          gotowość trzech targetów oraz wspólną próbkę OOF używaną do uczciwego porównania modeli.
        </p>
      </section>

      <section className="stats-row four">
        <div className="mini-stat"><span>Spółki</span><strong>{n(summary?.companies)}</strong></div>
        <div className="mini-stat"><span>Notowania dzienne</span><strong>{n(summary?.market_rows)}</strong></div>
        <div className="mini-stat"><span>Fakty finansowe</span><strong>{n(summary?.fundamental_rows)}</strong></div>
        <div className="mini-stat"><span>Dane makro</span><strong>{n(summary?.macro_rows)}</strong></div>
      </section>

      <section className="panel">
        <div className="panel-head">
          <div><p className="eyebrow">Jakość datasetu</p><h2>Gotowość do modelowania</h2></div>
          <span className={`quality-pill ${q.training_ready ? "good" : "poor"}`}>
            {q.training_ready ? "gotowy do modelowania" : "niewystarczające dane do ewaluacji"}
          </span>
        </div>
        <div className="stats-row four quality-stats">
          <div className="mini-stat"><span>Wiersze panelu</span><strong>{n(q.rows)}</strong></div>
          <div className="mini-stat"><span>Pokrycie targetu</span><strong>{pct(q.target_coverage)}</strong></div>
          <div className="mini-stat"><span>Wspólna próbka OOF</span><strong>{n(q.common_eval_rows)}</strong></div>
          <div className="mini-stat"><span>Okresy wspólnej próby</span><strong>{n(q.common_eval_periods)}</strong></div>
        </div>
        <div className="recommendation-list">
          {(quality?.recommendations || []).map((r: string, i: number) => <div className="recommendation-item" key={i}>{r}</div>)}
        </div>
      </section>

      <section className="panel">
        <div className="panel-head"><div><p className="eyebrow">Targety v5.3</p><h2>Gotowość targetów do ewaluacji</h2></div></div>
        <div className="table-scroll"><table className="model-table">
          <thead><tr><th>Target</th><th>Zakres</th><th>Pokrycie</th><th>Wspólne OOF</th><th>Spółki OOF</th><th>Okresy OOF</th><th>Status</th></tr></thead>
          <tbody>{(quality?.targets || []).map((t:any) => <tr key={t.key}>
            <td><strong>{t.label}</strong><div className="tiny-note"><code>{t.target_code}</code></div></td>
            <td>{t.applicability === "financial" ? "finansowe" : t.applicability === "non_financial" ? "niefinansowe" : "wszystkie"}</td>
            <td>{pct(t.target_coverage)}</td><td>{n(t.common_eval_rows)}</td><td>{n(t.common_eval_companies)}</td><td>{n(t.common_eval_periods)}</td>
            <td><span className={`quality-pill ${t.status}`}>{statusLabel(t.status)}</span></td>
          </tr>)}</tbody>
        </table></div>
      </section>

      <section className="two-col">
        <div className="panel">
          <div className="panel-head"><div><p className="eyebrow">Kanoniczny target</p><h2>Skąd pochodzi zysk netto?</h2></div></div>
          <div className="stats-row four">
            <div className="mini-stat"><span>Znane targety</span><strong>{n(q.known_targets)}</strong></div>
            <div className="mini-stat"><span>NET_INCOME_PARENT</span><strong>{n(target.parent_targets)}</strong></div>
            <div className="mini-stat"><span>Fallback NET_INCOME</span><strong>{n(target.generic_fallback_targets)}</strong></div>
            <div className="mini-stat"><span>Udział parent</span><strong>{pct(target.parent_share)}</strong></div>
          </div>
          <div className="notice" style={{ marginTop: 16 }}>
            v5.3 preferuje <code>NET_INCOME_PARENT</code>. Gdy źródło nie rozróżnia wyniku jednostki dominującej,
            używany jest <code>NET_INCOME</code>, a pochodzenie targetu pozostaje zapisane w datasetcie.
          </div>
        </div>

        <div className="panel model-summary">
          <p className="eyebrow">Najnowszy wspólny eksperyment</p>
          {champion ? <>
            <div className="model-champion">{champion.model_name}</div>
            <p>Champion jest wybierany wyłącznie z najnowszej wersji datasetu i tej samej próbki OOF.</p>
            <div className="summary-metrics">
              <div><span>MAE</span><strong>{money(champion.metrics?.mae)}</strong></div>
              <div><span>sMAPE</span><strong>{champion.metrics?.smape?.toFixed?.(2) ?? "—"}%</strong></div>
              <div><span>Obserwacje</span><strong>{n(champion.metrics?.evaluation_observations)}</strong></div>
            </div>
            <p className="tiny-note">Dataset: {summary?.dataset_version?.version_code || diagnostics?.dataset_version || "—"}</p>
          </> : <><div className="model-champion">Brak treningu</div><p>Po pobraniu danych uruchom trening modeli.</p></>}
        </div>
      </section>

      <section className="panel">
        <div className="panel-head"><div><p className="eyebrow">DATA FIX · audyt mapowania</p><h2>Surowe etykiety Bankier/Notoria → koncepty kanoniczne</h2></div></div>
        <div className="stats-row four quality-stats">
          <div className="mini-stat"><span>Etykiety z ostatniego audytu</span><strong>{n(quality?.mapping_audit?.labels_total)}</strong></div>
          <div className="mini-stat"><span>Zmapowane z danymi</span><strong>{n(quality?.mapping_audit?.mapped_with_values)}</strong></div>
          <div className="mini-stat"><span>Nierozpoznane z danymi</span><strong>{n(quality?.mapping_audit?.unmatched_with_values)}</strong></div>
          <div className="mini-stat"><span>Skuteczność mapowania</span><strong>{pct(quality?.mapping_audit?.mapping_rate_with_values)}</strong></div>
        </div>
        {(quality?.mapping_audit?.top_unmatched || []).length > 0 ? <div className="table-scroll" style={{marginTop:16}}><table className="model-table">
          <thead><tr><th>Spółka</th><th>Sprawozdanie</th><th>Nierozpoznana etykieta</th><th>Obserwacje</th><th>Zakres</th></tr></thead>
          <tbody>{(quality?.mapping_audit?.top_unmatched || []).slice(0,15).map((r:any,i:number)=><tr key={`${r.ticker}-${i}`}>
            <td>{r.ticker}</td><td>{r.statement_name}</td><td>{r.source_label}</td><td>{n(r.values_observed)}</td><td>{String(r.first_period||"—")} → {String(r.last_period||"—")}</td>
          </tr>)}</tbody>
        </table></div> : <div className="notice" style={{marginTop:16}}>Brak nierozpoznanych etykiet z wartościami w ostatnim audycie albo audyt nie został jeszcze uruchomiony.</div>}
      </section>

      <section className="panel">
        <div className="panel-head"><div><p className="eyebrow">Kompletność cech</p><h2>Pokrycie feature engineering</h2></div></div>
        <div className="feature-quality-grid">
          {(quality?.features || []).map((f: any) => <div className="feature-quality-row" key={f.feature}>
            <div className="feature-quality-title"><code>{f.feature}</code><span>{pct(f.coverage)}</span></div>
            <div className="quality-track"><div className={`quality-fill ${f.status}`} style={{ width: `${Math.max(0, Math.min(100, Number(f.coverage || 0) * 100))}%` }} /></div>
            <div className="feature-quality-meta"><span>{n(f.observed)} obserwacji</span><span className={`quality-text ${f.status}`}>{statusLabel(f.status)}</span></div>
          </div>)}
        </div>
      </section>

      <section className="two-col">
        <div className="panel">
          <div className="panel-head"><div><p className="eyebrow">Historia kwartalna</p><h2>Gotowość spółek</h2></div></div>
          <div className="table-scroll"><table className="model-table">
            <thead><tr><th>Ticker</th><th>Kwartały</th><th>Targety</th><th>Wspólne OOF</th><th>lag4</th></tr></thead>
            <tbody>{(quality?.companies || []).map((c: any) => <tr key={c.ticker}>
              <td>{c.ticker}</td><td>{n(c.periods)}</td><td>{n(c.known_targets)}</td><td>{n(c.common_eval_rows)}</td>
              <td><span className={`quality-pill ${c.lag4_ready ? "good" : "warning"}`}>{c.lag4_ready ? "gotowy" : "za krótka historia"}</span></td>
            </tr>)}</tbody>
          </table></div>
        </div>
        <div className="panel">
          <div className="panel-head"><div><p className="eyebrow">Pochodzenie danych</p><h2>Źródła fundamentów</h2></div></div>
          <div className="table-scroll"><table className="model-table">
            <thead><tr><th>Źródło</th><th>Wiersze</th><th>Spółki</th><th>Daty raportów</th><th>Proxy +120d</th></tr></thead>
            <tbody>{(quality?.sources || []).map((s: any) => <tr key={s.source}>
              <td>{s.source}</td><td>{n(s.rows)}</td><td>{n(s.companies)}</td><td>{n(s.exact_date_rows)}</td><td>{n(s.proxy_date_rows)}</td>
            </tr>)}</tbody>
          </table></div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-head"><div><p className="eyebrow">Porównanie modeli</p><h2>Ta sama liczba obserwacji dla każdego modelu</h2></div><a href="/models" className="button secondary">Pełna diagnostyka</a></div>
        <div className="table-scroll"><table className="model-table">
          <thead><tr><th>Model</th><th>MAE</th><th>RMSE</th><th>sMAPE</th><th>R²</th><th>OOF</th><th>Foldy</th></tr></thead>
          <tbody>{(models || []).map((m: any) => <tr key={m.id}>
            <td>{m.model_name}</td><td>{money(m.metrics?.mae)}</td><td>{money(m.metrics?.rmse)}</td><td>{m.metrics?.smape?.toFixed?.(2) ?? "—"}%</td><td>{m.metrics?.r2?.toFixed?.(3) ?? "—"}</td><td>{n(m.metrics?.evaluation_observations)}</td><td>{n(m.metrics?.walk_forward_folds)}</td>
          </tr>)}</tbody>
        </table></div>
      </section>

      {bestCompanyRows.length > 0 && <section className="panel">
        <div className="panel-head"><div><p className="eyebrow">Diagnostyka championa</p><h2>Błąd MAE per spółka</h2></div></div>
        <div className="table-scroll"><table className="model-table">
          <thead><tr><th>Ticker</th><th>Obserwacje</th><th>MAE</th><th>RMSE</th></tr></thead>
          <tbody>{bestCompanyRows.map((r: any) => <tr key={r.ticker}><td>{r.ticker}</td><td>{n(r.observations)}</td><td>{money(r.mae)}</td><td>{money(r.rmse)}</td></tr>)}</tbody>
        </table></div>
      </section>}

      <section className="panel">
        <div className="panel-head"><div><p className="eyebrow">ETL</p><h2>Historia pobierania danych</h2></div></div>
        <div className="table-scroll"><table className="model-table">
          <thead><tr><th>Źródło</th><th>Status</th><th>Rekordy</th><th>Start</th><th>Koniec</th></tr></thead>
          <tbody>{(runs || []).map((r: any) => <tr key={r.id}><td>{r.source_name}</td><td>{r.status}</td><td>{n(r.records_received)}</td><td>{String(r.started_at || "").replace("T", " ").slice(0, 19)}</td><td>{String(r.finished_at || "").replace("T", " ").slice(0, 19)}</td></tr>)}</tbody>
        </table></div>
      </section>
    </main>
  );
}

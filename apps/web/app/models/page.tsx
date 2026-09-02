const API = process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
async function getJson(path: string) {
  try { const r = await fetch(`${API}${path}`, { cache: "no-store" }); return r.ok ? r.json() : null; }
  catch { return null; }
}
function n(v:any){ return new Intl.NumberFormat("pl-PL").format(Number(v||0)); }
function money(v:any){ const x=Number(v); return Number.isFinite(x) ? new Intl.NumberFormat("pl-PL",{notation:"compact",maximumFractionDigits:2}).format(x) : "—"; }

export default async function ModelsPage() {
  const [modelsRaw, diagnostics] = await Promise.all([
    getJson("/api/v1/dashboard/models"),
    getJson("/api/v1/dashboard/model-diagnostics"),
  ]);
  const models = modelsRaw || [];
  const sorted = [...models].sort((a:any,b:any) => Number(a.metrics?.mae ?? Infinity) - Number(b.metrics?.mae ?? Infinity));
  const champion = sorted[0];
  const companyRows = (diagnostics?.by_company || []).filter((r:any) => r.model_name === champion?.model_name);
  const periodRows = (diagnostics?.by_period || []).filter((r:any) => r.model_name === champion?.model_name);

  return <main className="shell page-stack">
    <section className="page-header">
      <p className="eyebrow">Walidacja modeli · v5.3</p>
      <h1>Porównanie na wspólnej próbce OOF</h1>
      <p className="lead compact">Baseline seasonal, last value, Ridge, Random Forest i HistGradientBoosting są oceniane na dokładnie tych samych obserwacjach walidacyjnych. Ranking nie miesza już modeli ocenianych na różnych próbkach.</p>
    </section>

    <section className="panel">
      <div className="panel-head"><div><p className="eyebrow">Ranking</p><h2>MAE / RMSE / sMAPE / WAPE / R²</h2></div>{champion && <span className="status-badge champion">Champion: {champion.model_name}</span>}</div>
      <div className="table-scroll"><table className="model-table"><thead><tr><th>Model</th><th>MAE</th><th>RMSE</th><th>MedAE</th><th>sMAPE</th><th>WAPE</th><th>R²</th><th>OOF</th><th>Foldy</th></tr></thead><tbody>
        {sorted.map((m:any) => <tr key={m.id}><td>{m.model_name}</td><td>{money(m.metrics?.mae)}</td><td>{money(m.metrics?.rmse)}</td><td>{money(m.metrics?.medae)}</td><td>{m.metrics?.smape?.toFixed?.(2) ?? "—"}%</td><td>{m.metrics?.wape?.toFixed?.(2) ?? "—"}%</td><td>{m.metrics?.r2?.toFixed?.(3) ?? "—"}</td><td>{n(m.metrics?.evaluation_observations)}</td><td>{n(m.metrics?.walk_forward_folds)}</td></tr>)}
      </tbody></table></div>
      {champion && <p className="tiny-note">Dataset: {champion.dataset_version} · zakres ewaluacji: {champion.metrics?.evaluation_from || "—"} → {champion.metrics?.evaluation_to || "—"} · spółki: {n(champion.metrics?.evaluation_companies)}</p>}
      {!models.length && <p className="tiny-note">Brak treningów w bazie. Uruchom <code>python scripts/train_from_database.py</code>.</p>}
    </section>

    <section className="two-col">
      <div className="panel"><div className="panel-head"><div><p className="eyebrow">Champion per spółka</p><h2>Gdzie model działa najlepiej i najgorzej?</h2></div></div>
        <div className="table-scroll"><table className="model-table"><thead><tr><th>Ticker</th><th>N</th><th>MAE</th><th>RMSE</th></tr></thead><tbody>
          {companyRows.map((r:any)=><tr key={r.ticker}><td>{r.ticker}</td><td>{n(r.observations)}</td><td>{money(r.mae)}</td><td>{money(r.rmse)}</td></tr>)}
        </tbody></table></div>
      </div>
      <div className="panel"><div className="panel-head"><div><p className="eyebrow">Champion w czasie</p><h2>Błąd per kwartał</h2></div></div>
        <div className="table-scroll"><table className="model-table"><thead><tr><th>Kwartał</th><th>N</th><th>MAE</th></tr></thead><tbody>
          {periodRows.slice(-16).map((r:any)=><tr key={String(r.target_period_end)}><td>{String(r.target_period_end)}</td><td>{n(r.observations)}</td><td>{money(r.mae)}</td></tr>)}
        </tbody></table></div>
      </div>
    </section>

    <div className="notice">Wyniki są techniczną ewaluacją prototypu. Przed raportowaniem wyników finalnych należy zweryfikować wartości fundamentalne i dokładne daty publikacji w raportach emitenta/ESPI/ESEF.</div>
  </main>
}

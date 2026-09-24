import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { api, type Case, type Report } from './api';
import { demoReports } from './demoReports';

const date = (value: string) => new Date(value).toLocaleString(undefined, {
  month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', timeZone: 'UTC',
}) + ' UTC';

function CoordinatePlot({ reports, selectedId, onSelect }: {
  reports: Report[]; selectedId: string | null; onSelect: (id: string) => void;
}) {
  const x = (longitude: number) => 32 + ((longitude + 180) / 360) * 736;
  const y = (latitude: number) => 22 + ((90 - latitude) / 180) * 336;
  return (
    <div className="plot" aria-label="Coordinate plot of filtered reports">
      <svg viewBox="0 0 800 380" role="img" aria-label="Report locations plotted by latitude and longitude">
        <defs>
          <pattern id="grid" width="92" height="84" patternUnits="userSpaceOnUse">
            <path d="M 92 0 L 0 0 0 84" fill="none" stroke="#29445d" strokeWidth="1" />
          </pattern>
          <radialGradient id="glow"><stop stopColor="#1b5c78" stopOpacity=".55" /><stop offset="1" stopColor="#1b5c78" stopOpacity="0" /></radialGradient>
        </defs>
        <rect width="800" height="380" rx="18" fill="#0b2033" />
        <rect x="32" y="22" width="736" height="336" fill="url(#grid)" />
        <ellipse cx="420" cy="185" rx="300" ry="140" fill="url(#glow)" />
        <path d="M32 190H768M400 22V358" stroke="#426079" strokeWidth="1" strokeDasharray="5 7" />
        <text x="42" y="46" className="map-label">90° N</text>
        <text x="42" y="184" className="map-label">0°</text>
        <text x="42" y="348" className="map-label">90° S</text>
        <text x="676" y="348" className="map-label">180° E</text>
        {reports.map((report) => (
          <g key={report.id} onClick={() => onSelect(report.id)} className="map-point" tabIndex={0}
            role="button" aria-label={`Select ${report.title}`} onKeyDown={(event) => {
              if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); onSelect(report.id); }
            }}>
            <title>{report.title} · {report.location.latitude.toFixed(2)}°, {report.location.longitude.toFixed(2)}°</title>
            <circle cx={x(report.location.longitude)} cy={y(report.location.latitude)} r={selectedId === report.id ? 17 : 12} fill="#ed9f63" opacity=".18" />
            <circle cx={x(report.location.longitude)} cy={y(report.location.latitude)} r={selectedId === report.id ? 7 : 5}
              fill={selectedId === report.id ? '#ffba7e' : '#71d2d0'} stroke="#e9ffff" strokeWidth="1.5" />
          </g>
        ))}
      </svg>
      <span className="plot-caption">Coordinate view · schematic grid, no basemap</span>
    </div>
  );
}

function App() {
  const [reports, setReports] = useState<Report[]>([]);
  const [cases, setCases] = useState<Case[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [evidence, setEvidence] = useState<string[]>([]);
  const [query, setQuery] = useState('');
  const [language, setLanguage] = useState('all');
  const [title, setTitle] = useState('');
  const [summary, setSummary] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [view, setView] = useState<'reports' | 'cases'>('reports');

  async function refresh() {
    try {
      const [nextReports, nextCases] = await Promise.all([api.reports(), api.cases()]);
      setReports(nextReports);
      setCases(nextCases);
      setSelectedId((id) => id && nextReports.some((r) => r.id === id) ? id : nextReports[0]?.id ?? null);
      setError('');
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Cannot reach the API. Is FastAPI running on port 8000?'); }
  }

  useEffect(() => { void refresh(); }, []);

  const filtered = useMemo(() => reports.filter((report) => {
    const text = `${report.title} ${report.content} ${report.source_name} ${report.external_id}`.toLocaleLowerCase();
    return (language === 'all' || report.language === language) && text.includes(query.toLocaleLowerCase());
  }), [reports, language, query]);
  const selected = reports.find((report) => report.id === selectedId);
  const languages = [...new Set(reports.map((report) => report.language))].sort();

  function toggleEvidence(id: string) {
    setEvidence((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);
  }

  async function seed() {
    setBusy(true); setError(''); setMessage('');
    try {
      const existing = new Set((await api.reports()).map((report) => report.external_id));
      for (const report of demoReports) {
        if (!existing.has(report.external_id)) await api.createReport(report);
      }
      await refresh();
      setMessage('Synthetic sample reports are ready.');
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Could not load demo reports.'); }
    finally { setBusy(false); }
  }

  async function createCase(event: FormEvent) {
    event.preventDefault();
    if (!evidence.length) { setError('Select at least one report as evidence.'); return; }
    setBusy(true); setError(''); setMessage('');
    try {
      const created = await api.createCase({ title, summary, report_ids: evidence });
      setTitle(''); setSummary(''); setEvidence([]);
      await refresh(); setView('cases');
      setMessage(`Case ${created.id.slice(0, 8)} created with ${created.report_ids.length} report${created.report_ids.length === 1 ? '' : 's'}.`);
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Could not create case.'); }
    finally { setBusy(false); }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><div className="brand-icon">M<span>✳</span></div><div><strong>MissionLens</strong><small>ANALYST WORKSPACE</small></div></div>
        <div className="nav-label">WORKSPACE</div>
        <nav aria-label="Main navigation">
          <button className={view === 'reports' ? 'nav-item active' : 'nav-item'} onClick={() => setView('reports')}><span>◈</span> Reports <b>{reports.length}</b></button>
          <button className={view === 'cases' ? 'nav-item active' : 'nav-item'} onClick={() => setView('cases')}><span>▣</span> Cases <b>{cases.length}</b></button>
        </nav>
        <div className="sidebar-bottom"><span className="live-dot" /> Local portfolio demo<br /><small>Synthetic data only · no authentication</small></div>
      </aside>

      <main className="main">
        <header className="topbar"><span>WORKSPACE / {view === 'reports' ? 'REPORT EXPLORER' : 'INVESTIGATION CASES'}</span><span className="environment">DEMO ENVIRONMENT</span></header>
        <section className="content">
          <div className="heading"><div><div className="eyebrow">MISSIONLENS / FIELD NOTES</div><h1>{view === 'reports' ? 'Report explorer' : 'Investigation cases'}</h1><p>{view === 'reports' ? 'Review source material, find patterns, and assemble evidence.' : 'Review cases created from selected source reports.'}</p></div><button className="ghost-button" onClick={() => void refresh()}>↻ Refresh</button></div>

          {error && <div className="alert error" role="alert">{error}</div>}
          {message && <div className="alert success" role="status">{message}</div>}

          {view === 'reports' ? <>
            <div className="metric-row"><div className="metric"><span>TOTAL REPORTS</span><strong>{reports.length.toString().padStart(2, '0')}</strong><small>Available for review</small></div><div className="metric"><span>LANGUAGES</span><strong>{languages.length.toString().padStart(2, '0')}</strong><small>Source language tags</small></div><div className="metric"><span>SELECTED EVIDENCE</span><strong>{evidence.length.toString().padStart(2, '0')}</strong><small>Ready for a case</small></div></div>
            <div className="workspace-grid">
              <div className="left-column">
                <section className="panel plot-panel"><div className="panel-title"><div><span className="eyebrow">GEOSPATIAL VIEW</span><h2>Report locations</h2></div><span className="pill">{filtered.length} visible</span></div><CoordinatePlot reports={filtered} selectedId={selectedId} onSelect={setSelectedId} /></section>
                <section className="panel reports-panel"><div className="panel-title"><div><span className="eyebrow">SOURCE MATERIAL</span><h2>Reports</h2></div><span className="count">{filtered.length} results</span></div>
                  <div className="filters"><input aria-label="Search reports" placeholder="Search title, content, or source…" value={query} onChange={(e) => setQuery(e.target.value)} /><select aria-label="Filter by language" value={language} onChange={(e) => setLanguage(e.target.value)}><option value="all">All languages</option>{languages.map((code) => <option key={code} value={code}>{code.toUpperCase()}</option>)}</select></div>
                  {filtered.length ? <div className="report-list">{filtered.map((report) => <div className={selectedId === report.id ? 'report-row selected' : 'report-row'} key={report.id}><button className="report-open" onClick={() => setSelectedId(report.id)}><span className="report-symbol">◈</span><span><strong>{report.title}</strong><small>{report.source_name} · {date(report.observed_at)}</small></span></button><span className="lang">{report.language.toUpperCase()}</span><label className="check"><input type="checkbox" checked={evidence.includes(report.id)} onChange={() => toggleEvidence(report.id)} aria-label={`Use ${report.title} as evidence`} /><span>Add</span></label></div>)}</div> : <div className="empty">No reports match. Clear the filters or load sample data.</div>}
                </section>
              </div>
              <div className="right-column">
                <section className="panel detail-panel"><span className="eyebrow">REPORT DETAIL</span>{selected ? <><h2>{selected.title}</h2><div className="detail-meta"><span>{selected.source_type.replaceAll('_', ' ')}</span><span>{selected.language.toUpperCase()}</span><span>{selected.status}</span></div><p className="report-content">{selected.content}</p><dl><div><dt>SOURCE</dt><dd>{selected.source_name}</dd></div><div><dt>OBSERVED</dt><dd>{date(selected.observed_at)}</dd></div><div><dt>COORDINATES</dt><dd>{selected.location.latitude.toFixed(4)}°, {selected.location.longitude.toFixed(4)}°</dd></div><div><dt>EXTERNAL ID</dt><dd>{selected.external_id}</dd></div></dl><button className="secondary-button full" onClick={() => toggleEvidence(selected.id)}>{evidence.includes(selected.id) ? '✓ Added to evidence' : '+ Add to case evidence'}</button></> : <div className="empty">Select a report to review its details.</div>}</section>
                <section className="panel action-panel"><span className="eyebrow">NEXT ACTION</span><h2>Create a case</h2><p>Group reports into one investigation. Approval and audit workflows are planned.</p><form onSubmit={(e) => void createCase(e)}><label>Case title<input value={title} minLength={3} maxLength={200} required onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Review port observations" /></label><label>Summary<textarea value={summary} minLength={10} maxLength={2000} required onChange={(e) => setSummary(e.target.value)} placeholder="What should the analyst review?" rows={3} /></label><div className="evidence-count">{evidence.length} report{evidence.length === 1 ? '' : 's'} selected</div><button className="primary-button full" disabled={busy || !evidence.length}>Create case →</button></form></section>
              </div>
            </div>
            <div className="demo-strip"><div><strong>Need sample reports?</strong><span>Load five fictional multilingual reports to explore the workflow.</span></div><button className="secondary-button" onClick={() => void seed()} disabled={busy}>Load synthetic demo data</button></div>
          </> : <section className="panel cases-panel"><div className="panel-title"><div><span className="eyebrow">INVESTIGATIONS</span><h2>Saved cases</h2></div><button className="secondary-button" onClick={() => setView('reports')}>+ New case</button></div>{cases.length ? <div className="case-list">{cases.map((item) => <article key={item.id} className="case-item"><span className="case-icon">▣</span><div><strong>{item.title}</strong><p>{item.summary}</p><small>{date(item.created_at)} · {item.report_ids.length} linked report{item.report_ids.length === 1 ? '' : 's'}</small><div className="case-evidence">{item.report_ids.map((id) => <span key={id}>{reports.find((report) => report.id === id)?.title ?? id.slice(0, 8)}</span>)}</div></div></article>)}</div> : <div className="empty">No cases yet. Select reports and create your first case.</div>}</section>}
          <footer>MissionLens is an independent portfolio demonstration using synthetic data. This interface does not implement user authentication or operational approvals.</footer>
        </section>
      </main>
    </div>
  );
}

export default App;

import { useEffect, useRef, useState, type FormEvent } from 'react';
import { api, ApiError, type Approval, type AuditEvent, type Case, type Report } from './api';
import { demoReports, scenarioCase, scenarioReportIds } from './demoReports';

const date = (value: string) => new Date(value).toLocaleString(undefined, {
  month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', timeZone: 'UTC',
}) + ' UTC';
const PAGE_SIZE = 10;

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
            <path d="M 92 0 L 0 0 0 84" fill="none" stroke="#243246" strokeWidth="1" />
          </pattern>
          <radialGradient id="glow"><stop stopColor="#3ecfc4" stopOpacity=".18" /><stop offset="1" stopColor="#3ecfc4" stopOpacity="0" /></radialGradient>
        </defs>
        <rect width="800" height="380" rx="18" fill="#0b1220" />
        <rect x="32" y="22" width="736" height="336" fill="url(#grid)" />
        <ellipse cx="420" cy="185" rx="300" ry="140" fill="url(#glow)" />
        <path d="M32 190H768M400 22V358" stroke="#2c3d52" strokeWidth="1" strokeDasharray="5 7" />
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
            <circle cx={x(report.location.longitude)} cy={y(report.location.latitude)} r={selectedId === report.id ? 17 : 12} fill={selectedId === report.id ? '#e08a4f' : '#3ecfc4'} opacity=".22" />
            <circle cx={x(report.location.longitude)} cy={y(report.location.latitude)} r={selectedId === report.id ? 7 : 5}
              fill={selectedId === report.id ? '#f3b07a' : '#3ecfc4'} stroke="#eef8ff" strokeWidth="1.5" />
          </g>
        ))}
      </svg>
      <span className="plot-caption">Coordinate view · schematic grid, no basemap</span>
    </div>
  );
}

function App() {
  const [reports, setReports] = useState<Report[]>([]);
  const [reportTotal, setReportTotal] = useState(0);
  const [languageOptions, setLanguageOptions] = useState<string[]>([]);
  const [cases, setCases] = useState<Case[]>([]);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [actor, setActor] = useState<'analyst-demo' | 'supervisor-demo'>('analyst-demo');
  const [actionCaseId, setActionCaseId] = useState('');
  const [actionDescription, setActionDescription] = useState('');
  const [decisionReason, setDecisionReason] = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [evidence, setEvidence] = useState<string[]>([]);
  const [evidenceTitles, setEvidenceTitles] = useState<Record<string, string>>({});
  const [query, setQuery] = useState('');
  const [language, setLanguage] = useState('all');
  const [page, setPage] = useState(0);
  const [title, setTitle] = useState('');
  const [summary, setSummary] = useState('');
  const [busy, setBusy] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [view, setView] = useState<'reports' | 'cases' | 'approvals' | 'audit'>('reports');
  const [connection, setConnection] = useState<'loading' | 'ready' | 'error'>('loading');
  const requestId = useRef(0);

  async function refresh(): Promise<boolean> {
    const id = ++requestId.current;
    try {
      const [result, nextCases, nextLanguages, nextApprovals, nextAudit] = await Promise.all([
        api.reports({ query: query.trim(), language, offset: page * PAGE_SIZE, limit: PAGE_SIZE }),
        api.cases(), api.languages(), api.approvals(actor),
        actor === 'supervisor-demo' ? api.auditEvents(actor) : Promise.resolve([]),
      ]);
      if (id !== requestId.current) return false;
      const nextReports = result.items;
      setReports(nextReports);
      setReportTotal(result.total);
      setLanguageOptions(nextLanguages);
      setCases(nextCases);
      setApprovals(nextApprovals);
      setAuditEvents(nextAudit);
      setActionCaseId((id) => id && nextCases.some((item) => item.id === id) ? id : nextCases[0]?.id ?? '');
      setSelectedId((id) => id && nextReports.some((r) => r.id === id) ? id : nextReports[0]?.id ?? null);
      setError('');
      setConnection('ready');
      return true;
    } catch (cause) {
      if (id !== requestId.current) return false;
      setError(cause instanceof Error ? cause.message : 'Cannot reach the API. Is FastAPI running on port 8000?');
      setConnection('error');
      return false;
    }
  }

  async function manualRefresh() {
    setRefreshing(true);
    setMessage('');
    try {
      if (await refresh()) setMessage('Reports, cases, and approvals are up to date.');
    } finally {
      setRefreshing(false);
    }
  }

  useEffect(() => {
    const timer = setTimeout(() => void refresh(), query ? 250 : 0);
    return () => clearTimeout(timer);
  }, [query, language, page, actor]);

  const filtered = reports;
  const selected = reports.find((report) => report.id === selectedId);
  const languages = languageOptions;

  function toggleEvidence(id: string) {
    const report = reports.find((item) => item.id === id);
    setEvidence((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);
    if (report) {
      setEvidenceTitles((current) => ({ ...current, [id]: report.title }));
    }
  }

  async function draftScenario() {
    setBusy(true);
    try {
      const result = await api.reports({ query: 'SCENARIO-IST', limit: 20 });
      const linked = scenarioReportIds.map((externalId) => result.items.find((report) => report.external_id === externalId)?.id);
      if (linked.some((id) => !id)) {
        setError('Load the synthetic investigation reports first.');
        return;
      }
      setEvidence(linked as string[]);
      setEvidenceTitles(Object.fromEntries(
        (linked as string[]).map((id) => [id, result.items.find((report) => report.id === id)?.title ?? id]),
      ));
      setTitle(scenarioCase.title);
      setSummary(scenarioCase.summary);
      setQuery('SCENARIO-IST');
      setLanguage('all');
      setPage(0);
      setSelectedId(linked[0] ?? null);
      setView('reports');
      setMessage('Example case drafted with three reports. Review the evidence before creating it.');
      setError('');
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Could not load the example reports.'); }
    finally { setBusy(false); }
  }

  async function seed() {
    setBusy(true); setError(''); setMessage('');
    try {
      for (const report of demoReports) {
        try { await api.createReport(report); }
        catch (cause) { if (!(cause instanceof ApiError) || cause.status !== 409) throw cause; }
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
      setTitle(''); setSummary(''); setEvidence([]); setEvidenceTitles({});
      await refresh(); setView('cases');
      setMessage(`Case ${created.id.slice(0, 8)} created with ${created.report_ids.length} report${created.report_ids.length === 1 ? '' : 's'}.`);
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Could not create case.'); }
    finally { setBusy(false); }
  }

  async function proposeAction(event: FormEvent) {
    event.preventDefault();
    if (actor !== 'analyst-demo' || !actionCaseId) return;
    setBusy(true); setError(''); setMessage('');
    try {
      await api.requestApproval(actionCaseId, actionDescription, actor);
      setActionDescription('');
      await refresh();
      setMessage('Proposed action submitted for supervisor review. No action was executed.');
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Could not request approval.'); }
    finally { setBusy(false); }
  }

  async function decide(id: string, decision: 'approved' | 'rejected') {
    if (actor !== 'supervisor-demo' || decisionReason.trim().length < 10) {
      setError('Enter a decision reason of at least 10 characters.');
      return;
    }
    setBusy(true); setError(''); setMessage('');
    try {
      await api.decideApproval(id, decision, decisionReason, actor);
      setDecisionReason('');
      await refresh();
      setMessage(`Decision recorded as ${decision}. No operational action was executed.`);
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Could not record the decision.'); }
    finally { setBusy(false); }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><div className="brand-icon">M<span>✳</span></div><div><strong>MissionLens</strong><small>ANALYST WORKSPACE</small></div></div>
        <div className="nav-label">WORKSPACE</div>
        <nav aria-label="Main navigation">
          <button className={view === 'reports' ? 'nav-item active' : 'nav-item'} onClick={() => setView('reports')}><span>◈</span> Reports <b>{connection === 'ready' ? reportTotal : '—'}</b></button>
          <button className={view === 'cases' ? 'nav-item active' : 'nav-item'} onClick={() => setView('cases')}><span>▣</span> Cases <b>{connection === 'ready' ? cases.length : '—'}</b></button>
          <button className={view === 'approvals' ? 'nav-item active' : 'nav-item'} onClick={() => setView('approvals')}><span>◇</span> Approvals <b>{connection === 'ready' ? approvals.filter((item) => item.status === 'pending').length : '—'}</b></button>
          {actor === 'supervisor-demo' && <button className={view === 'audit' ? 'nav-item active' : 'nav-item'} onClick={() => setView('audit')}><span>▤</span> Audit <b>{auditEvents.length}</b></button>}
        </nav>
        <div className="sidebar-bottom"><span className="live-dot" /> Local portfolio demo<br /><small>Synthetic data only · actor switch is not login</small></div>
      </aside>

      <main className="main">
        <header className="topbar"><span>WORKSPACE / {view.toUpperCase()}</span><div className="topbar-actions"><label htmlFor="demo-actor">Demo actor (not login)</label><select id="demo-actor" value={actor} onChange={(event) => { setActor(event.target.value as typeof actor); setView('approvals'); }}><option value="analyst-demo">Analyst</option><option value="supervisor-demo">Supervisor</option></select><span className="environment">DEMO ENVIRONMENT</span></div></header>
        <section className="content">
          <div className="heading"><div><div className="eyebrow">MISSIONLENS / FIELD NOTES</div><h1>{view === 'reports' ? 'Report explorer' : view === 'cases' ? 'Investigation cases' : view === 'approvals' ? 'Approval review' : 'Decision history'}</h1><p>{view === 'reports' ? 'Review source material, find patterns, and assemble evidence.' : view === 'cases' ? 'Review cases created from selected source reports.' : view === 'approvals' ? 'Propose or review an action before a decision is recorded.' : 'Review the local demo approval history.'}</p></div><button className="ghost-button" disabled={refreshing} onClick={() => void manualRefresh()}>{refreshing ? 'Refreshing…' : '↻ Refresh'}</button></div>

          {error && <div className="alert error" role="alert">{error}</div>}
          {message && <div className="alert success" role="status">{message}</div>}

          <section className="briefing" aria-label="Demo scope and analyst scenario">
            <div className="briefing-copy">
              <div><span className="eyebrow">Working now</span><p>Review reports, build a case, propose an action, and record a supervisor decision with audit history.</p></div>
              <div><span className="eyebrow">Analyst scenario</span><p>Three fictional reports describe a terminal delay. Compare them before deciding if they refer to the same event.</p></div>
              <div><span className="eyebrow">Planned next</span><p>Real identity integration, production authorization, deployment, and a geographic basemap.</p></div>
            </div>
            {view === 'reports' && connection === 'ready' && (
              <div className="demo-actions">
                <button className="secondary-button" onClick={() => void seed()} disabled={busy}>Load synthetic demo data</button>
                <button className="ghost-button" onClick={() => void draftScenario()} disabled={busy}>Draft example case</button>
              </div>
            )}
          </section>

          {connection !== 'ready' ? <section className="panel connection-panel" role="status">
            <h2>{connection === 'loading' ? 'Loading workspace…' : 'Workspace temporarily unavailable'}</h2>
            <p>{connection === 'loading' ? 'Fetching reports and cases.' : 'The API did not return the reports and cases. Make sure FastAPI is running on port 8000, then click Refresh. Your saved data has not been cleared.'}</p>
          </section> : view === 'reports' ? <>
            <div className="metric-row">
              <div className="metric"><span>Matching reports</span><strong>{reportTotal.toString().padStart(2, '0')}</strong><small>Across all result pages</small></div>
              <div className="metric"><span>Languages</span><strong>{languages.length.toString().padStart(2, '0')}</strong><small>Source language tags</small></div>
              <div className={evidence.length ? 'metric emphasis' : 'metric'}><span>Selected evidence</span><strong>{evidence.length.toString().padStart(2, '0')}</strong><small>Ready for a case</small></div>
            </div>
            <div className="workspace-grid">
              <div className="left-column">
                <section className="panel plot-panel"><div className="panel-title"><div><span className="eyebrow">GEOSPATIAL VIEW</span><h2>Report locations</h2></div><span className="pill">{filtered.length} on this page</span></div><CoordinatePlot reports={filtered} selectedId={selectedId} onSelect={setSelectedId} /></section>
                <section className="panel reports-panel"><div className="panel-title"><div><span className="eyebrow">SOURCE MATERIAL</span><h2>Reports</h2></div><span className="count">{reportTotal} results</span></div>
                  <div className="filters"><input aria-label="Search reports" placeholder="Search title, content, or source…" maxLength={200} value={query} onChange={(e) => { setQuery(e.target.value); setPage(0); }} /><select aria-label="Filter by language" value={language} onChange={(e) => { setLanguage(e.target.value); setPage(0); }}><option value="all">All languages</option>{languages.map((code) => <option key={code} value={code}>{code.toUpperCase()}</option>)}</select></div>
                  {filtered.length ? <div className="report-list">{filtered.map((report) => <div className={selectedId === report.id ? 'report-row selected' : 'report-row'} key={report.id}><button className="report-open" onClick={() => setSelectedId(report.id)}><span className="report-symbol">◈</span><span><strong>{report.title}</strong><small>{report.source_name} · {date(report.observed_at)}</small></span></button><span className="lang">{report.language.toUpperCase()}</span><label className="check"><input type="checkbox" checked={evidence.includes(report.id)} onChange={() => toggleEvidence(report.id)} aria-label={`Use ${report.title} as evidence`} /><span>Add</span></label></div>)}</div> : <div className="empty">No reports match. Clear the filters or load sample data.</div>}
                  {reportTotal > PAGE_SIZE && <div className="pagination"><button className="secondary-button" disabled={page === 0} onClick={() => setPage(page - 1)}>← Previous</button><span>Page {page + 1} of {Math.ceil(reportTotal / PAGE_SIZE)}</span><button className="secondary-button" disabled={(page + 1) * PAGE_SIZE >= reportTotal} onClick={() => setPage(page + 1)}>Next →</button></div>}
                </section>
              </div>
              <div className="right-column">
                <section className="panel detail-panel"><span className="eyebrow">Report detail</span>{selected ? <><h2>{selected.title}</h2><div className="detail-meta"><span>{selected.source_type.replaceAll('_', ' ')}</span><span>{selected.language.toUpperCase()}</span><span className={`status-chip ${selected.status}`}>{selected.status}</span></div><p className="report-content">{selected.content}</p><dl><div><dt>SOURCE</dt><dd>{selected.source_name}</dd></div><div><dt>OBSERVED</dt><dd>{date(selected.observed_at)}</dd></div><div><dt>COORDINATES</dt><dd>{selected.location.latitude.toFixed(4)}°, {selected.location.longitude.toFixed(4)}°</dd></div><div><dt>EXTERNAL ID</dt><dd>{selected.external_id}</dd></div></dl><button className="secondary-button full" onClick={() => toggleEvidence(selected.id)}>{evidence.includes(selected.id) ? '✓ Added to evidence' : '+ Add to case evidence'}</button></> : <div className="empty">Select a report to review its details.</div>}</section>
                <section className="panel action-panel"><span className="eyebrow">Next action</span><h2>Create a case</h2><p>Group reports into one investigation, then propose an action for demo supervisor review.</p><form onSubmit={(e) => void createCase(e)}><label>Case title<input value={title} minLength={3} maxLength={200} required onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Review port observations" /></label><label>Summary<textarea value={summary} minLength={10} maxLength={2000} required onChange={(e) => setSummary(e.target.value)} placeholder="What should the analyst review?" rows={3} /></label><div className="evidence-count">{evidence.length} report{evidence.length === 1 ? '' : 's'} selected</div>                  {evidence.length > 0 && (
                    <div className="evidence-chips">
                      {evidence.map((id) => {
                        const label = reports.find((item) => item.id === id)?.title ?? evidenceTitles[id] ?? id.slice(0, 8);
                        return (
                          <button type="button" key={id} onClick={() => toggleEvidence(id)} aria-label={`Remove ${label} from evidence`}>
                            {label} ×
                          </button>
                        );
                      })}
                    </div>
                  )}<button className="primary-button full" disabled={busy || !evidence.length}>Create case →</button></form></section>
              </div>
            </div>
          </> : view === 'cases' ? <section className="panel cases-panel">
            <div className="panel-title"><div><span className="eyebrow">INVESTIGATIONS</span><h2>Saved cases</h2></div><button className="secondary-button" onClick={() => setView('reports')}>+ New case</button></div>
            {cases.length ? <div className="case-list">{cases.map((item) => <article key={item.id} className="case-item"><span className="case-icon">▣</span><div><strong>{item.title}</strong><p>{item.summary}</p><small>{date(item.created_at)} · {item.report_ids.length} linked report{item.report_ids.length === 1 ? '' : 's'}</small><div className="case-evidence">{item.report_ids.map((id, index) => <span key={id}>{item.report_titles[index] ?? id.slice(0, 8)}</span>)}</div>{actor === 'analyst-demo' && <button className="secondary-button case-action" onClick={() => { setActionCaseId(item.id); setView('approvals'); }}>Propose action →</button>}</div></article>)}</div> : <div className="empty">No cases yet. Select reports and create your first case.</div>}
          </section> : view === 'approvals' ? <div className="approval-layout">
            {actor === 'analyst-demo' && <section className="panel approval-form"><span className="eyebrow">ANALYST</span><h2>Propose an action</h2><p>This records a request for review. It does not execute an action.</p><form onSubmit={(event) => void proposeAction(event)}><label>Investigation case<select value={actionCaseId} required onChange={(event) => setActionCaseId(event.target.value)}>{!cases.length && <option value="">Create a case first</option>}{cases.map((item) => <option value={item.id} key={item.id}>{item.title}</option>)}</select></label><label>Proposed action<textarea value={actionDescription} minLength={10} maxLength={1000} required rows={3} onChange={(event) => setActionDescription(event.target.value)} placeholder="What should the supervisor consider?" /></label><button className="primary-button" disabled={busy || !cases.length}>Request review →</button></form></section>}
            {actor === 'supervisor-demo' && <section className="panel approval-form"><span className="eyebrow">SUPERVISOR</span><h2>Decision reason</h2><p>Enter a reason, then approve or reject a pending request below. A decision is recorded; nothing is executed.</p><label>Explanation<textarea value={decisionReason} minLength={10} maxLength={1000} rows={3} onChange={(event) => setDecisionReason(event.target.value)} placeholder="What evidence supports this decision?" /></label></section>}
            <section className="panel cases-panel"><div className="panel-title"><div><span className="eyebrow">REVIEW QUEUE</span><h2>Proposed actions</h2></div><span className="count">{approvals.length} total</span></div>{approvals.length ? <div className="case-list">{approvals.map((item) => <article key={item.id} className="case-item"><span className="case-icon">◇</span><div><strong>{item.case_title}</strong><p>{item.action_description}</p><small><span className={`status-chip ${item.status}`}>{item.status}</span> · requested by {item.requested_by} · {date(item.created_at)}</small>{item.decision_reason && <p>Decision: {item.decision_reason}</p>}{actor === 'supervisor-demo' && item.status === 'pending' && <div className="approval-buttons"><button className="secondary-button" disabled={busy} onClick={() => void decide(item.id, 'rejected')}>Reject</button><button className="primary-button" disabled={busy} onClick={() => void decide(item.id, 'approved')}>Approve</button></div>}</div></article>)}</div> : <div className="empty">No approval requests yet. An analyst can propose an action from a saved case.</div>}</section>
          </div> : <section className="panel cases-panel"><div className="panel-title"><div><span className="eyebrow">SUPERVISOR / LAST 100 EVENTS</span><h2>Approval audit history</h2></div></div>{auditEvents.length ? <div className="case-list">{auditEvents.map((event) => <article key={event.id} className="case-item"><span className="case-icon">▤</span><div><strong>{event.event_type.replaceAll('_', ' ')}</strong><p>{event.details}</p><small>{event.actor_id} · {date(event.occurred_at)} · case {event.case_id.slice(0, 8)}</small></div></article>)}</div> : <div className="empty">No approval events recorded.</div>}</section>}
          <footer>Independent portfolio demonstration with synthetic data. The actor switch is spoofable and is not authentication. No operational actions are executed.</footer>
        </section>
      </main>
    </div>
  );
}

export default App;

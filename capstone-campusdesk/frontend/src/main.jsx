import React, { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { GraduationCap, Inbox, CircleCheck, Clock3, Plus, Search, RefreshCw, ArrowUpRight, X, Trash2, ChevronLeft, ChevronRight, AlertCircle, Wifi, Monitor, KeyRound, Boxes, LayoutGrid } from 'lucide-react';
import './styles.css';

const statuses = { open: 'Open', in_progress: 'In progress', resolved: 'Resolved' };
const categories = { network: 'Network', hardware: 'Hardware', software: 'Software', access: 'Account access', other: 'Other' };
const icons = { network: Wifi, hardware: Monitor, software: Boxes, access: KeyRound, other: LayoutGrid };
const empty = { title: '', description: '', requester: '', location: '', category: 'network', priority: 'medium', status: 'open', assignee: 'Unassigned' };
const date = value => new Date(value.endsWith('Z') || /[+-]\d\d:\d\d$/.test(value) ? value : `${value}Z`).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });

// FastAPI validation errors arrive as a list of { loc, msg }; show them as "field: message".
const describe = detail => typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map(item => `${item.loc?.slice(1).join('.') || 'request'}: ${item.msg}`).join('; ') : '';

async function api(path, options = {}) {
  const response = await fetch(path, { ...options, headers: { 'Content-Type': 'application/json' } });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(describe(error.detail) || `Request failed (${response.status}). Please check the ticket details.`);
  }
  return response.status === 204 ? null : response.json();
}

function TicketDialog({ ticket, onClose, onSaved }) {
  const [form, setForm] = useState(ticket ? Object.fromEntries(Object.keys(empty).map(key => [key, ticket[key]])) : empty);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [deleting, setDeleting] = useState(false);
  const dialog = useRef(null);
  useEffect(() => { dialog.current.showModal(); return () => dialog.current?.close(); }, []);
  const change = event => setForm({ ...form, [event.target.name]: event.target.value });
  async function submit(event) {
    event.preventDefault(); setBusy(true); setError('');
    try { await api(ticket ? `/api/tickets/${ticket.id}` : '/api/tickets', { method: ticket ? 'PUT' : 'POST', body: JSON.stringify(form) }); onSaved(ticket ? 'Ticket updated' : 'Ticket created'); }
    catch (e) { setError(e.message); } finally { setBusy(false); }
  }
  async function remove() {
    setBusy(true); setError('');
    try { await api(`/api/tickets/${ticket.id}`, { method: 'DELETE' }); onSaved('Ticket deleted'); }
    catch (e) { setError(e.message); } finally { setBusy(false); }
  }
  return <dialog ref={dialog} onCancel={event => { if (busy) event.preventDefault(); else onClose(); }} aria-labelledby="dialog-title">
    <header className="dialog-header"><div><p className="eyebrow">{ticket ? `CD-${String(ticket.id).padStart(4, '0')}` : 'CAMPUS SUPPORT'}</p><h2 id="dialog-title">{ticket ? 'Ticket details' : 'New support ticket'}</h2></div><button type="button" className="icon-button" aria-label="Close dialog" title="Close" onClick={onClose} disabled={busy}><X size={20}/></button></header>
    <form onSubmit={submit}>
      {error && <p className="error" role="alert">{error}</p>}
      <label>Subject<input name="title" autoFocus required minLength={3} maxLength={120} value={form.title} onChange={change} placeholder="What needs attention?"/></label>
      <label>Description<textarea name="description" maxLength={4000} rows={3} value={form.description} onChange={change} placeholder="Add the details your support team needs"/></label>
      <div className="form-grid"><label>Requester<input name="requester" required minLength={2} maxLength={80} value={form.requester} onChange={change}/></label><label>Location<input name="location" required minLength={2} maxLength={80} value={form.location} onChange={change} placeholder="Building / room"/></label>
      <label>Category<select name="category" value={form.category} onChange={change}>{Object.entries(categories).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      <label>Priority<select name="priority" value={form.priority} onChange={change}>{['low', 'medium', 'high', 'urgent'].map(value => <option key={value} value={value}>{value[0].toUpperCase() + value.slice(1)}</option>)}</select></label>
      <label>Status<select name="status" value={form.status} onChange={change}>{Object.entries(statuses).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      <label>Assigned to<input name="assignee" required minLength={2} maxLength={80} value={form.assignee} onChange={change}/></label></div>
      {deleting && <div className="delete-confirm"><p>Delete this ticket permanently?</p><button type="button" className="danger" disabled={busy} onClick={remove}>Delete ticket</button><button type="button" disabled={busy} onClick={() => setDeleting(false)}>Keep ticket</button></div>}
      <footer className="dialog-footer">{ticket && <button type="button" className="icon-button danger-text" aria-label="Delete ticket" title="Delete ticket" disabled={busy} onClick={() => setDeleting(true)}><Trash2 size={18}/></button>}<span className="spacer"/><button type="button" disabled={busy} onClick={onClose}>Cancel</button><button className="primary" disabled={busy}>{busy ? 'Saving...' : ticket ? 'Save changes' : 'Create ticket'}</button></footer>
    </form>
  </dialog>;
}

function App() {
  const [tickets, setTickets] = useState([]);
  const [hasNext, setHasNext] = useState(false);
  const [stats, setStats] = useState(null);
  const [status, setStatus] = useState('');
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [revision, setRevision] = useState(0);
  const [modal, setModal] = useState(undefined);
  const [notice, setNotice] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError('');
    const timer = setTimeout(async () => {
      try {
        const params = new URLSearchParams({ q: query, limit: '13', offset: String(page * 12) });
        if (status) params.set('status', status);
        const [rows, counts] = await Promise.all([api(`/api/tickets?${params}`, { signal: controller.signal }), api('/api/stats', { signal: controller.signal })]);
        if (!controller.signal.aborted) { setTickets(rows.slice(0, 12)); setHasNext(rows.length > 12); setStats(counts); }
      } catch (e) { if (e.name !== 'AbortError') setError(e.message); }
      finally { if (!controller.signal.aborted) setLoading(false); }
    }, query ? 220 : 0);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [status, query, page, revision]);
  useEffect(() => { if (notice) { const timer = setTimeout(() => setNotice(''), 4000); return () => clearTimeout(timer); } }, [notice]);
  function filter(value) { setStatus(value); setPage(0); }
  function saved(message) { setModal(undefined); setNotice(message); setPage(0); setRevision(value => value + 1); }
  return <div className="app-shell">
    <aside className="sidebar"><a className="brand" href="/" aria-label="CampusDesk home"><span className="brand-mark"><GraduationCap size={24}/></span><span>CampusDesk<span className="brand-caption">IT SERVICE DESK</span></span></a>
      <p className="nav-label">WORKSPACE</p><nav aria-label="Ticket navigation">{[['', Inbox, 'All tickets'], ['open', AlertCircle, 'Open'], ['in_progress', Clock3, 'In progress'], ['resolved', CircleCheck, 'Resolved']].map(([value, Icon, label]) => <button key={value} className={status === value ? 'nav-item active' : 'nav-item'} aria-label={label} title={label} aria-pressed={status === value} onClick={() => filter(value)}><Icon size={18}/><span>{label}</span><span className="nav-count">{stats ? stats[value || 'total'] : '-'}</span></button>)}</nav>
      <div className="sidebar-bottom"><span className="avatar">AK</span><div><strong>T. Abdul Kalam Azad</strong><small>24BCS10053</small></div></div>
    </aside>
    <main><header className="topbar"><span>Workspace <span className="crumb">/</span> Campus support</span><span className="workspace-dot">IT operations</span></header>
      <div className="page-content"><div className="page-title"><div><p className="eyebrow">CAMPUS OPERATIONS</p><h1>Service desk</h1><p className="muted">A better day on campus starts with support.</p></div><button className="primary" onClick={() => setModal(null)}><Plus size={18}/> New ticket</button></div>
      <section className="overview" aria-label="Ticket overview">{[['open', 'Open tickets', Inbox], ['in_progress', 'In progress', Clock3], ['resolved', 'Resolved', CircleCheck], ['urgent', 'Urgent attention', AlertCircle]].map(([key, label, Icon]) => <div className={`metric ${key}`} key={key}><span className="metric-label">{label}<Icon size={18}/></span><strong>{stats ? stats[key] : '-'}</strong><span className="metric-foot">{key === 'urgent' ? 'Unresolved urgent tickets' : key === 'resolved' ? 'Support delivered' : key === 'in_progress' ? 'Being worked on' : 'Awaiting a response'}</span></div>)}</section>
      <div className="workspace-grid"><section className="ticket-section" aria-label="Support tickets"><div className="section-heading"><h2>Support tickets</h2><button className="icon-button" aria-label="Refresh tickets" title="Refresh tickets" onClick={() => setRevision(value => value + 1)} disabled={loading}><RefreshCw size={17} className={loading ? 'spin' : ''}/></button></div>
        <div className="filters"><div className="tabs" aria-label="Ticket status">{[['', 'All tickets'], ...Object.entries(statuses)].map(([value, label]) => <button key={value} className={status === value ? 'selected' : ''} aria-pressed={status === value} onClick={() => filter(value)}>{label}</button>)}</div><label className="search"><Search size={17}/><input aria-label="Search tickets" placeholder="Search tickets..." maxLength={120} value={query} onChange={event => { setQuery(event.target.value); setPage(0); }}/></label></div>
        {error ? <div className="empty error" role="alert"><AlertCircle/><h3>Tickets could not be loaded</h3><p>{error}</p><button onClick={() => setRevision(value => value + 1)}>Try again</button></div> : loading ? <div className="empty" role="status"><RefreshCw className="spin"/><p>Loading tickets...</p></div> : tickets.length === 0 ? <div className="empty"><Inbox size={32}/><h3>{query || status ? 'No matching tickets' : 'Your desk is clear'}</h3><p>{query || status ? 'No tickets match the current selection.' : 'No support requests yet.'}</p>{!query && !status && <button onClick={() => setModal(null)}><Plus size={16}/> New ticket</button>}</div> : <div className="table-wrap"><table><thead><tr><th>Ticket / subject</th><th>Status</th><th>Priority</th><th>Assignee</th><th>Created</th><th><span className="sr-only">Open</span></th></tr></thead><tbody>{tickets.map(ticket => { const Icon = icons[ticket.category]; return <tr key={ticket.id}><td><div className="ticket-subject"><span className={`category-icon ${ticket.category}`}><Icon size={18}/></span><div><button className="ticket-link" onClick={() => setModal(ticket)}>{ticket.title}</button><small>CD-{String(ticket.id).padStart(4, '0')} <span className="dot-separator">/</span> {ticket.location}</small></div></div></td><td><span className={`status ${ticket.status}`}><span/>{statuses[ticket.status]}</span></td><td><span className={`priority ${ticket.priority}`}><i/>{ticket.priority}</span></td><td className="assignee">{ticket.assignee}</td><td className="date">{date(ticket.created_at)}</td><td><button className="icon-button" aria-label={`Open ticket ${ticket.id}`} title="Open ticket" onClick={() => setModal(ticket)}><ArrowUpRight size={17}/></button></td></tr>; })}</tbody></table></div>}
        <footer className="table-footer"><span>{error ? 'Unavailable' : loading ? 'Updating...' : `${tickets.length} tickets on this page`}</span><div><button className="icon-button" aria-label="Previous page" title="Previous page" disabled={page === 0 || loading || Boolean(error)} onClick={() => setPage(value => value - 1)}><ChevronLeft size={16}/></button><span>Page {page + 1}</span><button className="icon-button" aria-label="Next page" title="Next page" disabled={!hasNext || loading || Boolean(error)} onClick={() => setPage(value => value + 1)}><ChevronRight size={16}/></button></div></footer>
      </section><aside className="right-rail"><img className="campus-image" src="/campus.jpg" alt="Students working together on campus"/><div className="rail-section"><p className="eyebrow">CAMPUS CONNECTION</p><h2>Keep campus moving.</h2><p className="muted">Technology support for the places where we learn, work, and connect.</p></div><div className="rail-section"><h3>Ticket categories</h3>{Object.entries(categories).map(([key, label]) => { const Icon = icons[key]; return <div className="category-row" key={key}><Icon size={17}/><span>{label}</span></div>; })}</div><div className="ownership"><GraduationCap size={19}/><span>CampusDesk<br/><small>Student DevOps Capstone</small></span></div></aside></div>
      <footer className="page-footer"><span>CampusDesk / Campus IT Helpdesk</span><span>T. Abdul Kalam Azad · 24BCS10053</span></footer></div>
    </main>{modal !== undefined && <TicketDialog key={modal?.id || 'new'} ticket={modal} onClose={() => setModal(undefined)} onSaved={saved}/>}<div className="toast-region" role="status">{notice && <div className="toast"><CircleCheck size={18}/>{notice}</div>}</div>
  </div>;
}

createRoot(document.getElementById('root')).render(<App/>);

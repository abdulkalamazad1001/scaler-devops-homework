import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const API = '/api';
const NEXT_STATUS = { TODO: 'IN_PROGRESS', IN_PROGRESS: 'DONE', DONE: 'TODO' };

function App() {
  const [tasks, setTasks] = useState([]);
  const [stats, setStats] = useState({ total: 0, todo: 0, inProgress: 0, done: 0 });
  const [filter, setFilter] = useState('ALL');
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async () => {
    try {
      setError('');
      const [taskRes, statsRes] = await Promise.all([fetch(`${API}/tasks`), fetch(`${API}/tasks/stats`)]);
      if (!taskRes.ok || !statsRes.ok) throw new Error('Backend unavailable');
      setTasks(await taskRes.json());
      setStats(await statsRes.json());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const visible = filter === 'ALL' ? tasks : tasks.filter((t) => t.status === filter);

  const advance = async (task) => {
    await fetch(`${API}/tasks/${task.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: NEXT_STATUS[task.status] }),
    });
    load();
  };

  const create = async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await fetch(`${API}/tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: form.get('title'),
        description: form.get('description'),
        priority: form.get('priority'),
        assignee: form.get('assignee') || 'Unassigned',
        status: 'TODO',
      }),
    });
    event.currentTarget.reset();
    setShowForm(false);
    load();
  };

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">T</span>
          <div>
            <b>TaskBoard</b>
            <small>DevOps Final Project</small>
          </div>
        </div>
        <nav>
          <a className="active">▦ <span>Dashboard</span></a>
          <a>✓ <span>My Tasks</span></a>
          <a>◫ <span>Projects</span></a>
          <a>◌ <span>Activity</span></a>
        </nav>
        <div className="side-bottom">
          <div className="upgrade">
            <strong>Ship with confidence.</strong>
            <p>Build, scan, deploy and observe your application.</p>
          </div>
          <div className="profile">
            <div className="avatar">DU</div>
            <div>
              <b>Demo User</b>
              <small>Developer</small>
            </div>
          </div>
        </div>
      </aside>

      <main className="main">
        <header>
          <div>
            <p className="eyebrow">WORKSPACE / OVERVIEW</p>
            <h1>Team dashboard</h1>
            <p className="muted">What is happening with your team today.</p>
          </div>
          <button className="primary" onClick={() => setShowForm(true)}>＋ New task</button>
        </header>

        {error && <div className="alert">⚠ {error}. Check that the backend and PostgreSQL are running.</div>}

        <section className="stats">
          <Stat label="Total tasks" value={stats.total} icon="▦" />
          <Stat label="To do" value={stats.todo} icon="○" />
          <Stat label="In progress" value={stats.inProgress} icon="◔" />
          <Stat label="Completed" value={stats.done} icon="✓" />
        </section>

        <section className="content-grid">
          <div className="panel tasks-panel">
            <div className="panel-head">
              <div>
                <h2>Tasks</h2>
                <p className="muted">Track work across the product team.</p>
              </div>
              <div className="filters">
                {['ALL', 'TODO', 'IN_PROGRESS', 'DONE'].map((f) => (
                  <button className={filter === f ? 'selected' : ''} onClick={() => setFilter(f)} key={f}>
                    {f === 'ALL' ? 'All' : f.replace('_', ' ')}
                  </button>
                ))}
              </div>
            </div>
            {loading ? (
              <div className="empty">Loading tasks…</div>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr><th>Task</th><th>Assignee</th><th>Priority</th><th>Status</th><th></th></tr>
                  </thead>
                  <tbody>
                    {visible.map((t) => (
                      <tr key={t.id}>
                        <td>
                          <div className="task-title">
                            <span className={`dot ${t.status.toLowerCase()}`}></span>
                            <div><b>{t.title}</b><small>{t.description}</small></div>
                          </div>
                        </td>
                        <td>{t.assignee}</td>
                        <td><span className={`priority ${t.priority.toLowerCase()}`}>{t.priority}</span></td>
                        <td><span className={`status ${t.status.toLowerCase()}`}>{t.status.replace('_', ' ')}</span></td>
                        <td><button className="icon-btn" onClick={() => advance(t)} title="Advance status">↻</button></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {!visible.length && <div className="empty">No tasks in this filter.</div>}
              </div>
            )}
          </div>

          <aside className="panel activity">
            <div className="panel-head">
              <div>
                <h2>Delivery pipeline</h2>
                <p className="muted">How a commit reaches the cluster.</p>
              </div>
            </div>
            <Activity icon="✓" text="Tests and lint" time="pytest, ruff, vite build" />
            <Activity icon="⛨" text="Security gates" time="Semgrep, Bandit, pip-audit, Gitleaks, Trivy" />
            <Activity icon="▣" text="Images pushed" time="ghcr.io, tagged with the commit SHA" />
            <Activity icon="↗" text="Argo CD sync" time="Helm chart reconciled from Git" />
            <div className="pipeline">
              <span>CI</span><i></i><span>Scan</span><i></i><span>Build</span><i></i><span>Deploy</span>
            </div>
          </aside>
        </section>

        {showForm && (
          <div className="modal-backdrop">
            <form className="modal" onSubmit={create}>
              <div className="modal-head">
                <div>
                  <p className="eyebrow">CREATE TASK</p>
                  <h2>Add a new task</h2>
                </div>
                <button type="button" className="close" onClick={() => setShowForm(false)}>×</button>
              </div>
              <label>Task title<input name="title" required maxLength={200} placeholder="e.g. Configure production ingress" /></label>
              <label>Description<textarea name="description" placeholder="What needs to be done?" /></label>
              <div className="form-row">
                <label>Priority
                  <select name="priority" defaultValue="MEDIUM">
                    <option>LOW</option><option>MEDIUM</option><option>HIGH</option>
                  </select>
                </label>
                <label>Assignee<input name="assignee" placeholder="Unassigned" /></label>
              </div>
              <button className="primary full">Create task</button>
            </form>
          </div>
        )}
      </main>
    </div>
  );
}

function Stat({ label, value, icon }) {
  return (
    <div className="stat">
      <div className="stat-icon">{icon}</div>
      <div><small>{label}</small><strong>{value}</strong><span>Updated just now</span></div>
    </div>
  );
}

function Activity({ icon, text, time }) {
  return (
    <div className="activity-row">
      <span className="activity-icon">{icon}</span>
      <div><b>{text}</b><small>{time}</small></div>
    </div>
  );
}

createRoot(document.getElementById('root')).render(<App />);

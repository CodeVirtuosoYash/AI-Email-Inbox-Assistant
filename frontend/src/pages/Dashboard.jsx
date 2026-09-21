import { useState, useEffect } from 'react';
import { getDashboard } from '../api/client';
import SummarizeButton from '../components/SummarizeButton';
import TaskCard from '../components/TaskCard';
import ReplyEditor from '../components/ReplyEditor';
import LoadingState from '../components/LoadingState';

const CATEGORY_LABEL = {
  important_message: 'Important',
  task: 'Task',
  fyi: 'FYI',
};

const CATEGORY_CLASS = {
  important_message: 'high',
  task: 'medium',
  fyi: 'low',
};

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboard()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  function handleSummarized(result) {
    setData(result);
  }

  if (loading) return <LoadingState message="Loading dashboard…" />;

  const counts = data?.counts || { messages: 0, tasks: 0, fyi: 0 };
  const todayTasks = data?.todays_tasks || [];
  const tomorrowTasks = data?.tomorrows_tasks || [];
  const summaries = data?.all_analyses || [];
  const totalProcessed = data?.emails_processed || summaries.length;
  const hasSummaries = summaries.length > 0;

  return (
    <div className="page">
      {/* ── Hero: Summarize ────────────────────────────── */}
      <div className="hero-card">
        <div className="hero-content">
          <div className="hero-text">
            <h2>Inbox Copilot</h2>
            <p>
              {hasSummaries
                ? `${totalProcessed} emails analyzed · ${counts.messages} need replies · ${counts.tasks} tasks extracted`
                : 'Summarize your inbox to classify emails, extract tasks, and draft replies.'}
            </p>
            {data?.last_summarized_at && (
              <div className="watermark-line" style={{ marginTop: '8px', marginBottom: 0 }}>
                <span className="watermark-dot" />
                Last synced {formatTimestamp(data.last_summarized_at)}
              </div>
            )}
          </div>
          <SummarizeButton onComplete={handleSummarized} />
        </div>
      </div>

      {/* ── Stats ──────────────────────────────────────── */}
      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-icon messages">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
              <polyline points="22,6 12,13 2,6" />
            </svg>
          </div>
          <div className="stat-info">
            <h3>{counts.messages}</h3>
            <p>Need reply</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon tasks">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
          </div>
          <div className="stat-info">
            <h3>{counts.tasks}</h3>
            <p>Tasks found</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon fyi">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="16" x2="12" y2="12" />
              <line x1="12" y1="8" x2="12.01" y2="8" />
            </svg>
          </div>
          <div className="stat-info">
            <h3>{counts.fyi}</h3>
            <p>FYI only</p>
          </div>
        </div>
      </div>

      {/* ── Tasks Sections (Collapsible) ───────────────── */}
      <CollapsibleTaskGroup title="Due today" tasks={todayTasks} defaultExpanded={true} />
      <CollapsibleTaskGroup title="Due tomorrow" tasks={tomorrowTasks} defaultExpanded={true} />

      {/* ── Summary Feed (With Integrated Replies) ────── */}
      {hasSummaries && (
        <div style={{ marginBottom: 'var(--space-xl)' }}>
          <div className="section-header">
            <span className="section-title">Email Summaries</span>
            <span className="section-count">{summaries.length} emails</span>
          </div>
          <div className="summary-feed">
            {summaries.map((item, i) => (
              <SummaryRow key={item.id} item={item} index={i} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Collapsible Task Group Component ───────────────── */
function CollapsibleTaskGroup({ title, tasks, defaultExpanded = true }) {
  const [expanded, setExpanded] = useState(defaultExpanded);

  return (
    <div style={{ marginBottom: 'var(--space-xl)' }}>
      <div
        className="section-header collapsible"
        onClick={() => setExpanded(!expanded)}
        style={{ cursor: 'pointer', userSelect: 'none' }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            style={{
              width: 14,
              height: 14,
              transform: expanded ? 'rotate(90deg)' : 'rotate(0deg)',
              transition: 'transform 0.2s ease',
              color: 'var(--text-tertiary)',
            }}
          >
            <polyline points="9 18 15 12 9 6" />
          </svg>
          <span className="section-title">{title}</span>
        </div>
        <span className="section-count">{tasks.length}</span>
      </div>

      {expanded && (
        tasks.length > 0 ? (
          <div className="card-grid fade-in">
            {tasks.map((task, i) => (
              <TaskCard key={task.id} task={task} index={i} />
            ))}
          </div>
        ) : (
          <div className="card">
            <div className="empty-state" style={{ padding: '20px' }}>
              <p style={{ color: 'var(--text-tertiary)', fontSize: '13px' }}>Nothing in this group</p>
            </div>
          </div>
        )
      )}
    </div>
  );
}

/* ── Summary Row with Integrated Reply ───────── */
function SummaryRow({ item, index }) {
  const initials = item.email_sender
    ? item.email_sender.split('@')[0].slice(0, 2)
    : '??';

  const senderName = item.email_sender?.split('@')[0] || 'Unknown';
  const delayClass = index < 8 ? `fade-in-delay-${Math.min(index + 1, 5)}` : '';

  return (
    <div className={`summary-row fade-in ${delayClass}`}>
      <div className="summary-row-avatar">
        <div className={`avatar avatar-color-${(index % 5) + 1}`}>{initials}</div>
      </div>
      <div className="summary-row-body">
        <div className="summary-row-header">
          <span className="summary-row-sender">{senderName}</span>
          <span className="summary-row-subject">{item.email_subject}</span>
        </div>
        <p className="summary-row-text">{item.summary}</p>
        {item.priority_reason && (
          <p className="summary-row-reason">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="16" x2="12" y2="12" />
              <line x1="12" y1="8" x2="12.01" y2="8" />
            </svg>
            {item.priority_reason}
          </p>
        )}

        {/* Integrated Reply Section */}
        {item.suggested_reply && (
          <ReplyEditor
            defaultReply={item.suggested_reply}
            defaultTone={item.tone || 'friendly'}
            emailId={item.email_id || item.id}
          />
        )}
      </div>
      <div className="summary-row-meta">
        <span className={`category-badge ${CATEGORY_CLASS[item.category]}`}>
          {CATEGORY_LABEL[item.category]}
        </span>
        <span className={`priority-dot ${item.priority}`} title={item.priority} />
        {item.email_received_at && (
          <span className="summary-row-time">{formatTime(item.email_received_at)}</span>
        )}
      </div>
    </div>
  );
}

function formatTime(isoStr) {
  const d = new Date(isoStr);
  return d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
}

function formatTimestamp(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  const now = new Date();
  const diff = now - d;
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
}

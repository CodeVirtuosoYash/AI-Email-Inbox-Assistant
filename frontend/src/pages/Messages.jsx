import { useState, useEffect } from 'react';
import { getMessages } from '../api/client';
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

export default function Messages() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    getMessages()
      .then(setMessages)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingState message="Loading summaries…" />;

  const filtered = messages.filter((m) => {
    if (filter === 'all') return true;
    return m.category === filter;
  });

  // Sort by priority: high first
  const priorityOrder = { high: 0, medium: 1, low: 2 };
  const sorted = [...filtered].sort(
    (a, b) => (priorityOrder[a.priority] ?? 3) - (priorityOrder[b.priority] ?? 3)
  );

  const categoryCount = (cat) => messages.filter((m) => m.category === cat).length;

  return (
    <div className="page">
      <div className="page-header">
        <h2>All Summaries</h2>
        <p>Every email analyzed by the AI, with classification, reasoning, and draft replies</p>
      </div>

      {/* Filter tabs */}
      <div style={{ display: 'flex', gap: '6px', marginBottom: '20px' }}>
        {[
          { key: 'all', label: `All (${messages.length})` },
          { key: 'important_message', label: `Important (${categoryCount('important_message')})` },
          { key: 'task', label: `Tasks (${categoryCount('task')})` },
          { key: 'fyi', label: `FYI (${categoryCount('fyi')})` },
        ].map(({ key, label }) => (
          <button
            key={key}
            className={`tone-btn ${filter === key ? 'active' : ''}`}
            onClick={() => setFilter(key)}
          >
            {label}
          </button>
        ))}
      </div>

      {sorted.length > 0 ? (
        <div className="card-grid">
          {sorted.map((msg, i) => (
            <SummaryCard key={msg.id} item={msg} index={i} />
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <div className="empty-state-icon">📭</div>
          <h3>No summaries yet</h3>
          <p>Run Summarize from the Dashboard to analyze your inbox.</p>
        </div>
      )}
    </div>
  );
}

export function SummaryCard({ item, index, defaultOpenReply = false }) {
  const initials = item.email_sender
    ? item.email_sender.split('@')[0].slice(0, 2)
    : '??';

  const senderName = item.email_sender?.split('@')[0] || 'Unknown';
  const delayClass = index < 5 ? `fade-in-delay-${index + 1}` : '';

  return (
    <div className={`card summary-card-full fade-in ${delayClass}`}>
      <div className="summary-card-top">
        <div className="message-sender">
          <div className={`avatar avatar-color-${(index % 5) + 1}`}>{initials}</div>
          <div>
            <span className="message-sender-name">{senderName}</span>
            <p style={{ fontSize: '12px', color: 'var(--text-tertiary)', marginTop: '1px' }}>
              {item.email_sender}
            </p>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className={`category-badge ${CATEGORY_CLASS[item.category]}`}>
            {CATEGORY_LABEL[item.category]}
          </span>
          <span className={`priority-badge ${item.priority}`}>
            <span className={`priority-dot ${item.priority}`} />
            {item.priority}
          </span>
        </div>
      </div>

      <p className="message-subject">{item.email_subject}</p>

      <div className="summary-highlight">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ width: 14, height: 14, flexShrink: 0, marginTop: 2 }}>
          <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
        </svg>
        <p>{item.summary}</p>
      </div>

      {item.priority_reason && (
        <div className="message-reason">
          {item.priority_reason}
        </div>
      )}

      {/* Integrated Reply Editor directly inside SummaryCard */}
      {item.suggested_reply && (
        <ReplyEditor
          defaultReply={item.suggested_reply}
          defaultTone={item.tone || 'friendly'}
          emailId={item.email_id || item.id}
          initialOpen={defaultOpenReply}
        />
      )}

      {item.email_received_at && (
        <p style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginTop: '4px' }}>
          Received {formatTime(item.email_received_at)}
        </p>
      )}
    </div>
  );
}

function formatTime(isoStr) {
  const d = new Date(isoStr);
  return d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
}

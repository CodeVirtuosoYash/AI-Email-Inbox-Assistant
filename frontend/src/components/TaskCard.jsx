import { useState } from 'react';
import { patchTask } from '../api/client';

export default function TaskCard({ task, index = 0, onStatusChange }) {
  const [status, setStatus] = useState(task.status);
  const [expanded, setExpanded] = useState(false);
  const isDone = status === 'done';

  async function toggleDone() {
    const newStatus = isDone ? 'pending' : 'done';
    setStatus(newStatus);
    try {
      await patchTask(task.id, { status: newStatus });
      onStatusChange?.(task.id, newStatus);
    } catch {
      setStatus(isDone ? 'done' : 'pending'); // revert
    }
  }

  const delayClass = index < 5 ? `fade-in-delay-${index + 1}` : '';

  return (
    <div className={`card task-card fade-in ${delayClass}`}>
      <button
        className={`task-checkbox ${isDone ? 'checked' : ''}`}
        onClick={toggleDone}
        aria-label={isDone ? 'Mark as pending' : 'Mark as done'}
        id={`task-check-${task.id}`}
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="20 6 9 17 4 12" />
        </svg>
      </button>

      <div className="task-body">
        <p className={`task-text ${isDone ? 'done' : ''}`}>{task.text}</p>

        <div className="task-meta">
          {task.due_date && (
            <span className="task-meta-item">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                <line x1="16" y1="2" x2="16" y2="6" />
                <line x1="8" y1="2" x2="8" y2="6" />
                <line x1="3" y1="10" x2="21" y2="10" />
              </svg>
              {formatDate(task.due_date)}
            </span>
          )}
          {task.email_sender && (
            <span className="task-meta-item">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                <polyline points="22,6 12,13 2,6" />
              </svg>
              {task.email_sender.split('@')[0]}
            </span>
          )}
          {task.suggested_actions?.length > 0 && (
            <button
              className="task-actions-toggle"
              onClick={() => setExpanded(!expanded)}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ width: 12, height: 12, transform: expanded ? 'rotate(90deg)' : 'none', transition: 'transform 0.15s ease' }}>
                <polyline points="9 18 15 12 9 6" />
              </svg>
              {task.suggested_actions.length} suggested actions
            </button>
          )}
        </div>

        {expanded && task.suggested_actions?.length > 0 && (
          <ul className="task-actions-list fade-in">
            {task.suggested_actions.map((action, i) => (
              <li key={i}>{action}</li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function formatDate(dateStr) {
  const d = new Date(dateStr + 'T00:00:00');
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);

  if (d.getTime() === today.getTime()) return 'Today';
  if (d.getTime() === tomorrow.getTime()) return 'Tomorrow';

  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

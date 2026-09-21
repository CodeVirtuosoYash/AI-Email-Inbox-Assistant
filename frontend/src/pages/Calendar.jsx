import { useState, useEffect } from 'react';
import { getTasks, patchTask } from '../api/client';
import LoadingState from '../components/LoadingState';

const DAYS_OF_WEEK = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

export default function Calendar() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState('2026-08-12'); // Default today in demo context

  // Fixed demo month: August 2026
  const year = 2026;
  const month = 7; // 0-indexed: 7 is August

  useEffect(() => {
    getTasks()
      .then(setTasks)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  async function handleToggleStatus(taskId, currentStatus) {
    const newStatus = currentStatus === 'done' ? 'pending' : 'done';
    setTasks((prev) =>
      prev.map((t) => (t.id === taskId ? { ...t, status: newStatus } : t))
    );
    try {
      await patchTask(taskId, { status: newStatus });
    } catch {
      // revert if failed
      setTasks((prev) =>
        prev.map((t) => (t.id === taskId ? { ...t, status: currentStatus } : t))
      );
    }
  }

  if (loading) return <LoadingState message="Loading calendar deadlines…" />;

  // Generate days for August 2026
  const firstDayIndex = new Date(year, month, 1).getDay(); // 6 for Aug 1 2026 (Saturday)
  const totalDays = new Date(year, month + 1, 0).getDate(); // 31 days in August

  // Map tasks by date ISO string: "2026-08-XX"
  const tasksByDate = {};
  tasks.forEach((t) => {
    if (t.due_date) {
      if (!tasksByDate[t.due_date]) tasksByDate[t.due_date] = [];
      tasksByDate[t.due_date].push(t);
    }
  });

  const selectedDateTasks = selectedDate ? (tasksByDate[selectedDate] || []) : tasks;

  return (
    <div className="page">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2>Deadline Calendar</h2>
          <p>Track all extracted task deadlines and commitments for August 2026</p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            className={`tone-btn ${selectedDate === null ? 'active' : ''}`}
            onClick={() => setSelectedDate(null)}
          >
            Show All ({tasks.length})
          </button>
          <button
            className={`tone-btn ${selectedDate === '2026-08-12' ? 'active' : ''}`}
            onClick={() => setSelectedDate('2026-08-12')}
          >
            Today (Aug 12)
          </button>
        </div>
      </div>

      {/* ── Month Header ───────────────────────────────── */}
      <div className="calendar-header-card card" style={{ marginBottom: '16px', padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ fontSize: '16px', fontWeight: '700', letterSpacing: '-0.3px' }}>August 2026</h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '12px', color: 'var(--text-tertiary)' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--amber)' }} /> Pending task
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--green)' }} /> Completed
          </span>
        </div>
      </div>

      {/* ── Calendar Grid ──────────────────────────────── */}
      <div className="calendar-grid-container card" style={{ padding: '20px', marginBottom: 'var(--space-xl)' }}>
        {/* Days of week */}
        <div className="calendar-week-days">
          {DAYS_OF_WEEK.map((day) => (
            <div key={day} className="calendar-week-day">
              {day}
            </div>
          ))}
        </div>

        {/* Calendar Day Cells */}
        <div className="calendar-month-grid">
          {/* Empty padding cells before 1st of month */}
          {Array.from({ length: firstDayIndex }).map((_, i) => (
            <div key={`empty-${i}`} className="calendar-cell empty" />
          ))}

          {/* Actual day cells */}
          {Array.from({ length: totalDays }).map((_, i) => {
            const dayNum = i + 1;
            const dateStr = `2026-08-${dayNum.toString().padStart(2, '0')}`;
            const dayTasks = tasksByDate[dateStr] || [];
            const isToday = dateStr === '2026-08-12';
            const isSelected = dateStr === selectedDate;
            const hasPending = dayTasks.some((t) => t.status === 'pending');
            const hasDone = dayTasks.some((t) => t.status === 'done');

            return (
              <div
                key={dateStr}
                className={`calendar-cell ${isToday ? 'is-today' : ''} ${isSelected ? 'is-selected' : ''} ${dayTasks.length > 0 ? 'has-tasks' : ''}`}
                onClick={() => setSelectedDate(dateStr)}
              >
                <div className="calendar-day-number">{dayNum}</div>
                {dayTasks.length > 0 && (
                  <div className="calendar-day-indicators">
                    {dayTasks.map((t) => (
                      <span
                        key={t.id}
                        className={`calendar-task-dot ${t.status === 'done' ? 'done' : 'pending'}`}
                        title={`${t.text} (${t.status})`}
                      />
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Selected Date Agenda Details ───────────────── */}
      <div>
        <div className="section-header">
          <span className="section-title">
            {selectedDate ? `Deadlines for ${formatDateLabel(selectedDate)}` : 'All Extracted Deadlines'}
          </span>
          <span className="section-count">{selectedDateTasks.length} tasks</span>
        </div>

        {selectedDateTasks.length > 0 ? (
          <div className="card-grid">
            {selectedDateTasks.map((task) => (
              <div key={task.id} className="card task-card fade-in">
                <button
                  className={`task-checkbox ${task.status === 'done' ? 'checked' : ''}`}
                  onClick={() => handleToggleStatus(task.id, task.status)}
                  aria-label={task.status === 'done' ? 'Mark pending' : 'Mark done'}
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                </button>
                <div className="task-body">
                  <p className={`task-text ${task.status === 'done' ? 'done' : ''}`}>{task.text}</p>
                  <div className="task-meta">
                    <span className="task-meta-item">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                        <line x1="16" y1="2" x2="16" y2="6" />
                        <line x1="8" y1="2" x2="8" y2="6" />
                        <line x1="3" y1="10" x2="21" y2="10" />
                      </svg>
                      Due {formatDateLabel(task.due_date)}
                    </span>
                    {task.email_sender && (
                      <span className="task-meta-item">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                          <polyline points="22,6 12,13 2,6" />
                        </svg>
                        {task.email_sender}
                      </span>
                    )}
                  </div>
                  {task.suggested_actions?.length > 0 && (
                    <ul className="task-actions-list" style={{ marginTop: '8px' }}>
                      {task.suggested_actions.map((act, idx) => (
                        <li key={idx}>{act}</li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="card">
            <div className="empty-state" style={{ padding: '24px' }}>
              <p style={{ color: 'var(--text-tertiary)', fontSize: '13px' }}>
                No deadlines scheduled for {selectedDate ? formatDateLabel(selectedDate) : 'this selection'}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function formatDateLabel(dateStr) {
  if (!dateStr) return 'Unscheduled';
  const d = new Date(dateStr + 'T00:00:00');
  const today = new Date('2026-08-12T00:00:00');
  const tomorrow = new Date('2026-08-13T00:00:00');

  if (d.getTime() === today.getTime()) return 'Today (Aug 12)';
  if (d.getTime() === tomorrow.getTime()) return 'Tomorrow (Aug 13)';

  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', weekday: 'short' });
}

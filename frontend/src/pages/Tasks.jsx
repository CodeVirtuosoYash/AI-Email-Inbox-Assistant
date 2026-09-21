import { useState, useEffect } from 'react';
import { getTasks } from '../api/client';
import TaskCard from '../components/TaskCard';
import LoadingState from '../components/LoadingState';

export default function Tasks() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // all | pending | done

  useEffect(() => {
    getTasks()
      .then(setTasks)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  function handleStatusChange(id, newStatus) {
    setTasks((prev) =>
      prev.map((t) => (t.id === id ? { ...t, status: newStatus } : t))
    );
  }

  const filtered = tasks.filter((t) => {
    if (filter === 'pending') return t.status === 'pending';
    if (filter === 'done') return t.status === 'done';
    return true;
  });

  const pendingCount = tasks.filter((t) => t.status === 'pending').length;
  const doneCount = tasks.filter((t) => t.status === 'done').length;

  if (loading) return <LoadingState message="Loading tasks…" />;

  return (
    <div className="page">
      <div className="page-header">
        <h2>Tasks</h2>
        <p>
          {pendingCount} pending · {doneCount} completed
        </p>
      </div>

      {/* Filter tabs */}
      <div style={{ display: 'flex', gap: '4px', marginBottom: '24px' }}>
        {[
          { key: 'all', label: `All (${tasks.length})` },
          { key: 'pending', label: `Pending (${pendingCount})` },
          { key: 'done', label: `Done (${doneCount})` },
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

      {filtered.length > 0 ? (
        <div className="card-grid">
          {filtered.map((task, i) => (
            <TaskCard key={task.id} task={task} index={i} onStatusChange={handleStatusChange} />
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <div className="empty-state-icon">✓</div>
          <h3>
            {filter === 'pending'
              ? 'All caught up!'
              : filter === 'done'
              ? 'No completed tasks yet'
              : 'No tasks extracted'}
          </h3>
          <p>
            {tasks.length === 0
              ? 'Run Summarize from the Dashboard to extract tasks from your emails.'
              : 'Try changing the filter.'}
          </p>
        </div>
      )}
    </div>
  );
}

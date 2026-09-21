export default function MessageCard({ message, index = 0 }) {
  const initials = message.email_sender
    ? message.email_sender.split('@')[0].slice(0, 2)
    : '??';

  const delayClass = index < 5 ? `fade-in-delay-${index + 1}` : '';

  return (
    <div className={`card message-card fade-in ${delayClass}`} id={`message-${message.id}`}>
      <div className="message-card-header">
        <div className="message-sender">
          <div className="avatar">{initials}</div>
          <span className="message-sender-name">
            {message.email_sender?.split('@')[0] || 'Unknown'}
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className={`priority-badge ${message.priority}`}>
            <span className={`priority-dot ${message.priority}`} />
            {message.priority}
          </span>
          {message.email_received_at && (
            <span className="message-time">{formatTime(message.email_received_at)}</span>
          )}
        </div>
      </div>

      <p className="message-subject">{message.email_subject}</p>
      <p className="message-summary">{message.summary}</p>

      {message.priority_reason && (
        <div className="message-reason">
          {message.priority_reason}
        </div>
      )}
    </div>
  );
}

function formatTime(isoStr) {
  const d = new Date(isoStr);
  return d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
}

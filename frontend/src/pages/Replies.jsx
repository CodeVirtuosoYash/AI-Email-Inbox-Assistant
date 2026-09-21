import { useState, useEffect } from 'react';
import { getMessages } from '../api/client';
import { SummaryCard } from './Messages';
import LoadingState from '../components/LoadingState';

export default function Replies() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMessages()
      .then(setMessages)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingState message="Loading draft replies…" />;

  // Filter summaries that have suggested replies
  const itemsWithReplies = messages.filter(
    (m) => m.suggested_reply || m.category === 'important_message'
  );

  return (
    <div className="page">
      <div className="page-header">
        <h2>Draft Replies</h2>
        <p>Email summaries paired with AI-drafted responses — adjust tone and regenerate in-place</p>
      </div>

      {itemsWithReplies.length > 0 ? (
        <div className="card-grid">
          {itemsWithReplies.map((item, i) => (
            <SummaryCard key={item.id} item={item} index={i} defaultOpenReply={true} />
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <div className="empty-state-icon">✉️</div>
          <h3>No draft replies</h3>
          <p>
            Replies are generated for emails classified as important messages.
            Run Summarize from the Dashboard to get started.
          </p>
        </div>
      )}
    </div>
  );
}

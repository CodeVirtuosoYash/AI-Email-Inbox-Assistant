import { useState } from 'react';
import { regenerateReply } from '../api/client';

const TONES = ['friendly', 'professional', 'concise', 'empathetic'];

export default function ReplyEditor({ reply, emailId, defaultReply, defaultTone = 'friendly', initialOpen = false }) {
  const replyText = reply?.suggested_reply || defaultReply || '';
  const initialTone = reply?.tone || defaultTone;

  const [currentReply, setCurrentReply] = useState(replyText);
  const [selectedTone, setSelectedTone] = useState(initialTone);
  const [regenerating, setRegenerating] = useState(false);
  const [isOpen, setIsOpen] = useState(initialOpen);

  const targetId = reply?.id || emailId || 1;

  async function handleRegenerate(tone) {
    setSelectedTone(tone);
    setRegenerating(true);
    try {
      const updated = await regenerateReply(targetId, tone);
      if (updated?.suggested_reply) {
        setCurrentReply(updated.suggested_reply);
      }
    } catch (err) {
      console.error('Regenerate failed:', err);
    } finally {
      setRegenerating(false);
    }
  }

  if (!replyText) return null;

  return (
    <div className="summary-reply-box fade-in">
      <div
        className="summary-reply-header"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ width: 13, height: 13, color: 'var(--accent)' }}>
            <polyline points="9 17 4 12 9 7" />
            <path d="M20 18v-2a4 4 0 0 0-4-4H4" />
          </svg>
          <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>
            Suggested Reply
          </span>
          <span className="priority-badge low" style={{ fontSize: '10px', padding: '1px 6px' }}>
            {selectedTone}
          </span>
        </div>
        <button className="task-actions-toggle" style={{ pointerEvents: 'none' }}>
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            style={{
              width: 12,
              height: 12,
              transform: isOpen ? 'rotate(90deg)' : 'rotate(0deg)',
              transition: 'transform 0.15s ease',
            }}
          >
            <polyline points="9 18 15 12 9 6" />
          </svg>
          {isOpen ? 'Hide Reply' : 'View Draft Reply'}
        </button>
      </div>

      {isOpen && (
        <div className="summary-reply-body fade-in">
          <div className="reply-content">
            {regenerating ? (
              <div className="loading-overlay" style={{ padding: '16px 0' }}>
                <div className="loading-spinner" style={{ width: 20, height: 20 }} />
                <p className="loading-text" style={{ fontSize: 12 }}>Redrafting in {selectedTone} tone…</p>
              </div>
            ) : (
              currentReply
            )}
          </div>

          <div className="reply-toolbar" style={{ marginTop: '8px' }}>
            {TONES.map((tone) => (
              <button
                key={tone}
                className={`tone-btn ${selectedTone === tone ? 'active' : ''}`}
                onClick={() => handleRegenerate(tone)}
                disabled={regenerating}
              >
                {tone}
              </button>
            ))}

            <button
              className={`regenerate-btn ${regenerating ? 'loading' : ''}`}
              onClick={() => handleRegenerate(selectedTone)}
              disabled={regenerating}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="23 4 23 10 17 10" />
                <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
              </svg>
              Regenerate
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

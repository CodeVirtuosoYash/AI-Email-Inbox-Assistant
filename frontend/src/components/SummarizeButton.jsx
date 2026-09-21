import { useState } from 'react';
import { postSummarize } from '../api/client';

export default function SummarizeButton({ onComplete }) {
  const [loading, setLoading] = useState(false);

  async function handleClick() {
    setLoading(true);
    try {
      const data = await postSummarize();
      onComplete?.(data);
    } catch (err) {
      console.error('Summarize failed:', err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <button
      className={`summarize-btn ${loading ? 'loading' : ''}`}
      onClick={handleClick}
      disabled={loading}
      id="summarize-trigger"
    >
      {loading ? (
        <>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
          </svg>
          Processing…
        </>
      ) : (
        <>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
          </svg>
          Summarize Inbox
        </>
      )}
    </button>
  );
}

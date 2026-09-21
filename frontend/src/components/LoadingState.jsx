export default function LoadingState({ count = 0, message }) {
  return (
    <div className="loading-overlay fade-in">
      <div className="loading-spinner" />
      <p className="loading-text">
        {message || (count > 0
          ? `Agent reading ${count} email${count === 1 ? '' : 's'}…`
          : 'Processing your inbox…')}
      </p>
      <p className="loading-subtext">
        Classifying, extracting tasks, and drafting replies
      </p>
    </div>
  );
}

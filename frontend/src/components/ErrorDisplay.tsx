interface ErrorDisplayProps {
  message: string;
  onRetry?: () => void;
}

export default function ErrorDisplay({ message, onRetry }: ErrorDisplayProps) {
  return (
    <div className="bg-safeflow-bg-secondary border border-safeflow-error/30 rounded-lg p-6 text-center">
      <div className="text-safeflow-error mb-4">
        <svg
          className="w-12 h-12 mx-auto"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      </div>
      <h3 className="text-lg font-medium text-safeflow-text-primary mb-2">出现错误</h3>
      <p className="text-safeflow-text-secondary mb-4">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="btn-secondary">
          重试
        </button>
      )}
    </div>
  );
}

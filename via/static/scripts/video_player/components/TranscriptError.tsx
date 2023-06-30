import type { APIError } from '../utils/api';

export type TranscriptErrorProps = {
  error: APIError;
};

export default function TranscriptError({ error }: TranscriptErrorProps) {
  return (
    <div className="p-3">
      <h2 className="text-lg">Unable to load transcript</h2>
      <p className="mb-3">{error.error?.title ?? error.message}</p>
      {error.error?.detail && (
        <details>
          <summary className="mb-2">Error details:</summary>
          <p>{error.error.detail}</p>
        </details>
      )}
    </div>
  );
}

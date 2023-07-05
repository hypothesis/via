import { Callout, CautionIcon } from '@hypothesis/frontend-shared';

import type { APIError } from '../utils/api';

export type TranscriptErrorProps = {
  error: APIError;
};

export default function TranscriptError({ error }: TranscriptErrorProps) {
  return (
    <Callout role="alert" status="error" icon={CautionIcon}>
      <h2 className="text-lg">Unable to load transcript</h2>
      <p>{error.error?.title ?? error.message}</p>
    </Callout>
  );
}

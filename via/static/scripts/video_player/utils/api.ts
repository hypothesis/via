/** Data needed to call an API method. */
export type APIMethod = {
  /** Headers to include with the request. */
  headers: Record<string, string>;

  /** HTTP method. */
  method: string;

  /** Endpoint URL. */
  url: string;
};

export class APIError extends Error {
  /** The HTTP status code of the response. */
  status: number;

  /**
   * Payload of the response.
   */
  data: unknown;

  constructor(status: number, data: unknown) {
    super('API call failed');

    this.status = status;
    this.data = data;
  }
}

/**
 * Structure of a JSON API response.
 *
 * See https://jsonapi.org/format/#document-structure.
 */
export type JSONAPIObject<Properties extends object> = {
  data: {
    type: string;
    id: string;
    attributes: Properties;
  };
};

/**
 * Make an API call to the backend.
 *
 * API request/response formats follow [JSON:API](https://jsonapi.org).
 */
export async function callAPI<T = unknown>(api: APIMethod): Promise<T> {
  const headers = { ...api.headers };
  headers['Content-Type'] = 'application/json; charset=UTF-8';

  const result = await fetch(api.url, {
    method: api.method,
    headers,
  });

  const resultData = await result.json().catch(() => null);

  if (result.status >= 400 && result.status < 600) {
    throw new APIError(result.status, resultData);
  }

  return resultData;
}

/** Data needed to call an API method. */
export type APIMethod = {
  /** Headers to include with the request. */
  headers: Record<string, string>;

  /** HTTP method. */
  method: string;

  /** Endpoint URL. */
  url: string;
};

/**
 * Structure of a JSON API error.
 *
 * See https://jsonapi.org/format/#error-objects.
 */
export type JSONAPIError = {
  status: number;
  code: string;
  title: string;
  detail: string;
};

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
    errors: JSONAPIError[];
  };
};

export class APIError extends Error {
  /** The HTTP status code of the response. */
  status: number;

  /** Error details returned by the API. */
  error: JSONAPIError | undefined;

  constructor(status: number, error?: JSONAPIError) {
    super('API call failed');

    this.status = status;
    this.error = error;
  }
}

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
    let error;
    if (
      resultData &&
      Array.isArray(resultData.errors) &&
      resultData.errors.length > 0
    ) {
      error = resultData.errors[0];
    }
    throw new APIError(result.status, error);
  }

  return resultData;
}

import type { ZodSchema } from "zod";

export class ApiError extends Error {
  status: number;
  details?: unknown;

  constructor(message: string, status: number, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

const buildHeaders = (headers?: HeadersInit) => {
  const requestId = crypto.randomUUID();
  return {
    "X-Request-Id": requestId,
    ...headers
  };
};

export async function apiFetch<T>(
  path: string,
  options: RequestInit & { schema?: ZodSchema<T> } = {}
): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: buildHeaders(options.headers)
  });

  const contentType = response.headers.get("content-type") ?? "";
  const isJson = contentType.includes("application/json");
  const payload = isJson ? await response.json().catch(() => null) : await response.text();

  if (!response.ok) {
    const message =
      typeof payload === "object" && payload && "message" in payload
        ? String((payload as { message: string }).message)
        : `Request failed with status ${response.status}`;
    throw new ApiError(message, response.status, payload);
  }

  if (options.schema) {
    return options.schema.parse(payload);
  }

  return payload as T;
}

export const apiStream = (path: string, options?: { withCredentials?: boolean }) => {
  // TODO: Extend to support auth headers, reconnect logic, and structured SSE payload parsing.
  return new EventSource(`${BASE_URL}${path}`, { withCredentials: options?.withCredentials });
};

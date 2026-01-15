import type { ZodSchema } from "zod";
import { trackError, trackEvent } from "../telemetry/telemetry";

export class ApiError extends Error {
  status: number;
  details?: unknown;
  requestId?: string;

  constructor(message: string, status: number, details?: unknown, requestId?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
    this.requestId = requestId;
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
  const headers = buildHeaders(options.headers);
  const requestId =
    typeof headers === "object" && headers && "X-Request-Id" in headers
      ? String(headers["X-Request-Id"])
      : undefined;
  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers
  });

  const responseRequestId = response.headers.get("x-request-id") ?? requestId;

  const contentType = response.headers.get("content-type") ?? "";
  const isJson = contentType.includes("application/json");
  const payload = isJson ? await response.json().catch(() => null) : await response.text();

  if (!response.ok) {
    const message =
      typeof payload === "object" && payload && "message" in payload
        ? String((payload as { message: string }).message)
        : `Request failed with status ${response.status}`;
    const error = new ApiError(message, response.status, payload, responseRequestId);
    trackError(error, {
      path,
      method: options.method ?? "GET",
      status: response.status,
      requestId: responseRequestId
    });
    throw error;
  }

  trackEvent("api.success", {
    path,
    method: options.method ?? "GET",
    status: response.status,
    requestId: responseRequestId
  });

  if (options.schema) {
    return options.schema.parse(payload);
  }

  return payload as T;
}

export const apiStream = (path: string, options?: { withCredentials?: boolean }) => {
  // TODO: Extend to support auth headers, reconnect logic, and structured SSE payload parsing.
  return new EventSource(`${BASE_URL}${path}`, { withCredentials: options?.withCredentials });
};

export const apiStreamJson = <T>(path: string, onMessage: (data: T) => void) => {
  // TODO: replace with a robust SSE parser that validates payloads with Zod.
  const source = apiStream(path);
  source.addEventListener("message", (event) => {
    try {
      const parsed = JSON.parse((event as MessageEvent).data) as T;
      onMessage(parsed);
    } catch (error) {
      trackError(error, { path, type: "sse.parse" });
    }
  });
  return source;
};

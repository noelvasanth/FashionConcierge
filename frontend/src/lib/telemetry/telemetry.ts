type TelemetryPayload = Record<string, unknown> | undefined;

export type TelemetryRecord = {
  id: string;
  name: string;
  type: "event" | "error" | "span.start" | "span.end";
  timestamp: string;
  props?: Record<string, unknown>;
};

const TELEMETRY_KEY = "telemetry.records";
const TELEMETRY_ERROR_KEY = "telemetry.lastErrorId";
const MAX_RECORDS = 50;

let inMemoryRecords: TelemetryRecord[] = [];
let lastErrorId: string | null = null;

const loadRecords = (): TelemetryRecord[] => {
  const stored = localStorage.getItem(TELEMETRY_KEY);
  if (!stored) {
    return [];
  }
  try {
    const parsed = JSON.parse(stored) as TelemetryRecord[];
    if (Array.isArray(parsed)) {
      return parsed;
    }
  } catch {
    return [];
  }
  return [];
};

const persistRecords = (records: TelemetryRecord[]) => {
  localStorage.setItem(TELEMETRY_KEY, JSON.stringify(records.slice(-MAX_RECORDS)));
};

const createRecord = (name: string, type: TelemetryRecord["type"], props?: TelemetryPayload) => {
  const record: TelemetryRecord = {
    id: crypto.randomUUID(),
    name,
    type,
    timestamp: new Date().toISOString(),
    props: props ? { ...props } : undefined
  };

  inMemoryRecords = [...inMemoryRecords, record].slice(-MAX_RECORDS);
  const stored = loadRecords();
  persistRecords([...stored, record]);

  return record;
};

export const trackEvent = (name: string, props?: TelemetryPayload) => {
  const record = createRecord(name, "event", props);
  console.info("[telemetry] event", record);
  return record.id;
};

export const trackError = (error: unknown, props?: TelemetryPayload) => {
  const record = createRecord("error", "error", {
    message: error instanceof Error ? error.message : String(error),
    stack: error instanceof Error ? error.stack : undefined,
    ...props
  });
  lastErrorId = record.id;
  localStorage.setItem(TELEMETRY_ERROR_KEY, record.id);
  console.error("[telemetry] error", record);
  return record.id;
};

export const startSpan = (name: string, props?: TelemetryPayload) => {
  const record = createRecord(name, "span.start", props);
  console.info("[telemetry] span.start", record);
  return record.id;
};

export const endSpan = (spanId: string, props?: TelemetryPayload) => {
  const record = createRecord("span.end", "span.end", { spanId, ...props });
  console.info("[telemetry] span.end", record);
  return record.id;
};

export const getLastErrorId = () => {
  if (lastErrorId) {
    return lastErrorId;
  }
  return localStorage.getItem(TELEMETRY_ERROR_KEY);
};

export const formatErrorMessage = (error: unknown) => {
  if (error instanceof Error && "requestId" in error) {
    const requestId = (error as Error & { requestId?: string }).requestId;
    if (requestId) {
      return `${error.message} (trace ${requestId})`;
    }
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Please try again.";
};

export const getTelemetryRecords = () => {
  if (inMemoryRecords.length > 0) {
    return inMemoryRecords;
  }
  return loadRecords();
};

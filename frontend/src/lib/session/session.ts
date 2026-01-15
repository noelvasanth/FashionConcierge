export type SessionState = {
  userId: string;
  sessionId: string;
};

const SESSION_KEY = "fashion.session";
const USER_ID_KEY = "userId";
const SESSION_ID_KEY = "sessionId";

const isValidSession = (value: unknown): value is SessionState => {
  if (!value || typeof value !== "object") {
    return false;
  }
  const record = value as Record<string, unknown>;
  return typeof record.userId === "string" && typeof record.sessionId === "string";
};

export const getSession = (): SessionState | null => {
  const stored = localStorage.getItem(SESSION_KEY);
  if (stored) {
    try {
      const parsed = JSON.parse(stored) as unknown;
      if (isValidSession(parsed)) {
        return parsed;
      }
    } catch {
      return null;
    }
  }

  const legacySessionId = localStorage.getItem(SESSION_ID_KEY);
  const legacyUserId = localStorage.getItem(USER_ID_KEY);
  if (legacySessionId && legacyUserId) {
    return { sessionId: legacySessionId, userId: legacyUserId };
  }

  return null;
};

export const setSession = (session: SessionState) => {
  localStorage.setItem(SESSION_KEY, JSON.stringify(session));
  localStorage.setItem(SESSION_ID_KEY, session.sessionId);
  localStorage.setItem(USER_ID_KEY, session.userId);
};

export const clearSession = () => {
  localStorage.removeItem(SESSION_KEY);
  localStorage.removeItem(SESSION_ID_KEY);
};

export const getSessionId = () => getSession()?.sessionId ?? null;

export const getUserId = () => {
  const session = getSession();
  if (session) {
    return session.userId;
  }
  return localStorage.getItem(USER_ID_KEY);
};

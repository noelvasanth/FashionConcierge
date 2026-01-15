import type { FeedbackRecord } from "../contracts";

const FEEDBACK_KEY = "feedback.records";
const MAX_RECORDS = 20;

export const loadFeedbackRecords = (): FeedbackRecord[] => {
  const stored = localStorage.getItem(FEEDBACK_KEY);
  if (!stored) {
    return [];
  }
  try {
    const parsed = JSON.parse(stored) as FeedbackRecord[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
};

export const storeFeedbackRecord = (record: FeedbackRecord) => {
  const existing = loadFeedbackRecords();
  const next = [record, ...existing].slice(0, MAX_RECORDS);
  localStorage.setItem(FEEDBACK_KEY, JSON.stringify(next));
};

import { useMemo } from "react";
import { useFeedbackList } from "../lib/api/hooks";
import { loadFeedbackRecords } from "../lib/feedback/feedbackStore";

const ReviewerPage = () => {
  const { data, error, isLoading } = useFeedbackList();

  const localFallback = useMemo(() => loadFeedbackRecords(), []);
  const items = data?.items ?? (error ? localFallback : []);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Reviewer</h1>
        <p className="text-sm text-muted-foreground">
          Inspect recent feedback responses for QA and debugging.
        </p>
      </header>

      {error && (
        <div className="rounded-2xl border border-dashed bg-white p-4 text-sm text-muted-foreground">
          Backend unavailable. Showing the last {items.length} feedback entries stored locally.
        </div>
      )}

      <div className="space-y-4">
        {isLoading && <p className="text-sm text-muted-foreground">Loading feedback...</p>}
        {!isLoading && items.length === 0 && (
          <p className="text-sm text-muted-foreground">No feedback captured yet.</p>
        )}
        {items.map((entry) => (
          <div key={entry.id} className="rounded-2xl border bg-white p-4 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="text-sm font-semibold">
                {entry.rating === "up" ? "👍 Positive" : "👎 Needs work"}
              </div>
              <div className="text-xs text-muted-foreground">{entry.createdAt}</div>
            </div>
            <p className="mt-2 text-sm text-muted-foreground">Page: {entry.page}</p>
            {entry.traceId && (
              <p className="mt-1 text-xs text-muted-foreground">Trace: {entry.traceId}</p>
            )}
            {entry.comment && <p className="mt-3 text-sm">{entry.comment}</p>}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ReviewerPage;

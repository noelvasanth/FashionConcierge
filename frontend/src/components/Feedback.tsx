import { useMemo, useState } from "react";
import { useLocation } from "react-router-dom";
import { Button } from "./ui/button";
import { useToast } from "./ui/use-toast";
import { useFeedbackCreate } from "../lib/api/hooks";
import { storeFeedbackRecord } from "../lib/feedback/feedbackStore";
import { getSessionId, getUserId } from "../lib/session/session";
import { formatErrorMessage } from "../lib/telemetry/telemetry";

type FeedbackProps = {
  pageLabel?: string;
  traceId?: string;
};

export const Feedback = ({ pageLabel, traceId }: FeedbackProps) => {
  const { toast } = useToast();
  const location = useLocation();
  const feedbackMutation = useFeedbackCreate();
  const [rating, setRating] = useState<"up" | "down" | null>(null);
  const [comment, setComment] = useState("");

  const userId = useMemo(() => getUserId() ?? "guest", []);
  const sessionId = useMemo(() => getSessionId() ?? "unknown", []);
  const page = pageLabel ?? location.pathname;

  const submitFeedback = async (nextRating: "up" | "down") => {
    const payload = {
      userId,
      sessionId,
      page,
      traceId,
      rating: nextRating,
      comment: nextRating === "down" ? comment.trim() || undefined : undefined,
      createdAt: new Date().toISOString()
    };

    try {
      const result = await feedbackMutation.mutateAsync(payload);
      storeFeedbackRecord(result);
      setRating(null);
      setComment("");
      toast({
        title: "Feedback sent",
        description: "Thanks for helping the concierge improve."
      });
    } catch (error) {
      storeFeedbackRecord({ id: `local-${crypto.randomUUID()}`, ...payload });
      toast({
        variant: "destructive",
        title: "Unable to send feedback",
        description: formatErrorMessage(error)
      });
    }
  };

  return (
    <div className="rounded-2xl border bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold">Was this helpful?</h3>
          <p className="text-xs text-muted-foreground">Share quick feedback for this view.</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant={rating === "up" ? "default" : "outline"}
            onClick={() => submitFeedback("up")}
          >
            👍
          </Button>
          <Button
            type="button"
            variant={rating === "down" ? "default" : "outline"}
            onClick={() => setRating("down")}
          >
            👎
          </Button>
        </div>
      </div>
      {rating === "down" && (
        <div className="mt-4 space-y-3">
          <textarea
            className="w-full rounded-lg border border-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            rows={3}
            placeholder="Tell us what went wrong"
            value={comment}
            onChange={(event) => setComment(event.target.value)}
          />
          <Button type="button" onClick={() => submitFeedback("down")}>
            Send feedback
          </Button>
        </div>
      )}
    </div>
  );
};

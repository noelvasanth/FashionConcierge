import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "../components/ui/button";
import { useToast } from "../components/ui/use-toast";
import { useOrchestrateContext, useOrchestrateOutfit } from "../lib/api/hooks";
import type {
  OrchestrateContextResponse,
  OrchestrateOutfitResponse
} from "../lib/contracts";

const plannerSchema = z.object({
  date: z.string().min(1, "Select a date"),
  location: z.string().min(1, "Enter a location"),
  mood: z.enum(["casual", "business", "active", "trendy", "festive", "urban"]),
  contextOnly: z.boolean().default(false)
});

type PlannerFormValues = z.infer<typeof plannerSchema>;

const PlannerPage = () => {
  const { toast, dismiss } = useToast();
  const [outfits, setOutfits] = useState<OrchestrateOutfitResponse["outfits"] | null>(null);
  const [context, setContext] = useState<OrchestrateContextResponse["context"] | null>(null);
  const orchestrateOutfit = useOrchestrateOutfit();
  const orchestrateContext = useOrchestrateContext();

  const sessionId = useMemo(() => localStorage.getItem("sessionId"), []);
  const userId = useMemo(() => localStorage.getItem("userId") ?? "guest", []);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting }
  } = useForm<PlannerFormValues>({
    resolver: zodResolver(plannerSchema),
    defaultValues: {
      date: "",
      location: "",
      mood: "casual",
      contextOnly: false
    }
  });

  const onSubmit = async (values: PlannerFormValues) => {
    const toastId = toast({
      title: values.contextOnly ? "Fetching context" : "Fetching outfits",
      description: "Talking to the orchestrator..."
    });

    try {
      if (!sessionId) {
        throw new Error("Missing session. Please re-onboard.");
      }

      const payload = {
        userId,
        sessionId,
        date: values.date,
        location: values.location,
        mood: values.mood
      };

      if (values.contextOnly) {
        const response = await orchestrateContext.mutateAsync(payload);
        setContext(response.context);
        setOutfits(null);
      } else {
        const response = await orchestrateOutfit.mutateAsync(payload);
        setOutfits(response.outfits);
        setContext(null);
      }
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Planner request failed",
        description: error instanceof Error ? error.message : "Please try again."
      });
    } finally {
      dismiss(toastId);
    }
  };

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Outfit planner</h1>
        <p className="text-sm text-muted-foreground">
          Share the day&apos;s context and the orchestrator will compose recommendations.
        </p>
      </header>

      <form
        className="space-y-4 rounded-2xl border bg-white p-5 shadow-sm"
        onSubmit={handleSubmit(onSubmit)}
      >
        <div>
          <label className="text-sm font-medium" htmlFor="date">
            Date
          </label>
          <input
            id="date"
            type="date"
            className="mt-2 w-full rounded-lg border border-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            {...register("date")}
          />
          {errors.date && <p className="mt-1 text-xs text-destructive">{errors.date.message}</p>}
        </div>
        <div>
          <label className="text-sm font-medium" htmlFor="location">
            Location
          </label>
          <input
            id="location"
            type="text"
            placeholder="San Francisco, CA"
            className="mt-2 w-full rounded-lg border border-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            {...register("location")}
          />
          {errors.location && (
            <p className="mt-1 text-xs text-destructive">{errors.location.message}</p>
          )}
        </div>
        <div>
          <label className="text-sm font-medium" htmlFor="mood">
            Mood
          </label>
          <select
            id="mood"
            className="mt-2 w-full rounded-lg border border-input bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            {...register("mood")}
          >
            <option value="casual">Casual</option>
            <option value="business">Business</option>
            <option value="active">Active</option>
            <option value="trendy">Trendy</option>
            <option value="festive">Festive</option>
            <option value="urban">Urban</option>
          </select>
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" className="h-4 w-4" {...register("contextOnly")} />
          Request context only
        </label>
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Submitting..." : "Generate plan"}
        </Button>
      </form>

      {outfits && (
        <div className="grid gap-4 md:grid-cols-2">
          {outfits.map((outfit) => (
            <div key={outfit.outfitId} className="rounded-2xl border bg-white p-4 shadow-sm">
              <h2 className="text-lg font-semibold">{outfit.name}</h2>
              <p className="mt-2 text-sm text-muted-foreground">{outfit.rationale}</p>
              <div className="mt-4 flex flex-wrap gap-2 text-xs text-muted-foreground">
                {outfit.itemIds.map((itemId) => (
                  <span key={itemId} className="rounded-full bg-muted px-3 py-1">
                    {itemId}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {context && (
        <div className="rounded-2xl border bg-white p-4 shadow-sm">
          <h2 className="text-lg font-semibold">Context payload</h2>
          <pre className="mt-3 whitespace-pre-wrap text-xs text-muted-foreground">
            {JSON.stringify(context, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

export default PlannerPage;

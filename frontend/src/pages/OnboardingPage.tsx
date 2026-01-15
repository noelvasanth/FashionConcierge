import { useMemo, useState, type FormEvent } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { useToast } from "../components/ui/use-toast";
import { useCreateSession } from "../lib/api/hooks";

const OnboardingPage = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [userId, setUserId] = useState(
    () => localStorage.getItem("userId") ?? crypto.randomUUID()
  );
  const createSession = useCreateSession();

  const hasSession = useMemo(() => Boolean(localStorage.getItem("sessionId")), []);

  if (hasSession) {
    return <Navigate to="/app/planner" replace />;
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      const result = await createSession.mutateAsync({ userId });
      localStorage.setItem("userId", userId);
      toast({
        title: "Session created",
        description: `Session ${result.sessionId} is ready.`
      });
      navigate("/app/planner");
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Unable to create session",
        description: error instanceof Error ? error.message : "Please try again."
      });
    }
  };

  return (
    <div className="mx-auto flex min-h-[70vh] max-w-xl flex-col justify-center gap-6">
      <header className="space-y-2 text-center">
        <p className="text-sm font-semibold uppercase text-muted-foreground">Get started</p>
        <h1 className="text-3xl font-semibold">Create your planning session</h1>
        <p className="text-sm text-muted-foreground">
          We&apos;ll save a session token so the planner can talk to the orchestrator.
        </p>
      </header>
      <form className="rounded-2xl border bg-white p-6 shadow-sm" onSubmit={handleSubmit}>
        <label className="text-sm font-medium" htmlFor="userId">
          User ID
        </label>
        <input
          id="userId"
          className="mt-2 w-full rounded-lg border border-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          value={userId}
          onChange={(event) => setUserId(event.target.value)}
          required
        />
        <Button className="mt-4 w-full" type="submit" disabled={createSession.isPending}>
          {createSession.isPending ? "Creating session..." : "Start planning"}
        </Button>
      </form>
    </div>
  );
};

export default OnboardingPage;

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { server } from "../mocks/server";
import { Feedback } from "../components/Feedback";
import { ToastContextProvider } from "../components/ui/use-toast";
import { Toaster } from "../components/ui/toaster";
import { setSession } from "../lib/session/session";

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } }
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <ToastContextProvider>
        <MemoryRouter>{children}</MemoryRouter>
        <Toaster />
      </ToastContextProvider>
    </QueryClientProvider>
  );
};

describe("Feedback", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("captures thumbs down feedback and posts it", async () => {
    const user = userEvent.setup();
    const requestSpy = vi.fn();

    setSession({ userId: "user-123", sessionId: "session-456" });

    server.use(
      http.post("/feedback", async ({ request }) => {
        requestSpy(await request.json());
        return HttpResponse.json({
          id: "feedback-99",
          userId: "user-123",
          sessionId: "session-456",
          page: "/test",
          rating: "down",
          comment: "Needs more outfits",
          createdAt: "2024-10-01T00:00:00.000Z"
        });
      })
    );

    render(<Feedback pageLabel="/test" />, { wrapper: createWrapper() });

    await user.click(screen.getByRole("button", { name: "👎" }));
    await user.type(screen.getByPlaceholderText(/tell us what went wrong/i), "Needs more outfits");
    await user.click(screen.getByRole("button", { name: /send feedback/i }));

    expect(requestSpy).toHaveBeenCalled();

    const stored = JSON.parse(localStorage.getItem("feedback.records") ?? "[]") as Array<{
      rating: string;
      comment?: string;
    }>;

    expect(stored[0].rating).toBe("down");
    expect(stored[0].comment).toBe("Needs more outfits");
  });
});

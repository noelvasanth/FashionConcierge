import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { describe, expect, it, vi, beforeEach } from "vitest";
import type { ReactNode } from "react";
import { server } from "../mocks/server";
import { useCreateSession } from "../lib/api/hooks";

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } }
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe("useCreateSession", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("calls /sessions, returns the sessionId, and stores it in localStorage", async () => {
    const requestSpy = vi.fn();
    server.use(
      http.post("/sessions", async ({ request }) => {
        requestSpy(await request.json());
        return HttpResponse.json({ sessionId: "session-123" });
      })
    );

    const { result } = renderHook(() => useCreateSession(), { wrapper: createWrapper() });

    const response = await result.current.mutateAsync({ userId: "user-123" });

    expect(requestSpy).toHaveBeenCalledWith({ userId: "user-123" });
    expect(response.sessionId).toBe("session-123");

    await waitFor(() => {
      expect(localStorage.getItem("sessionId")).toBe("session-123");
    });
  });
});

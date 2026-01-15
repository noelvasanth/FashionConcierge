import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it } from "vitest";
import type { ReactNode } from "react";
import { server } from "../mocks/server";
import PlannerPage from "../pages/PlannerPage";
import { ToastContextProvider } from "../components/ui/use-toast";

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } }
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <ToastContextProvider>{children}</ToastContextProvider>
    </QueryClientProvider>
  );
};

describe("PlannerPage", () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem("sessionId", "session-123");
    localStorage.setItem("userId", "user-123");
    server.use(
      http.post("/orchestrate/outfit", () => {
        return HttpResponse.json({
          outfits: [
            {
              outfitId: "plan-1",
              name: "Test Outfit One",
              itemIds: ["item-1"],
              rationale: "Test rationale."
            },
            {
              outfitId: "plan-2",
              name: "Test Outfit Two",
              itemIds: ["item-2"],
              rationale: "Another rationale."
            }
          ]
        });
      }),
      http.post("/orchestrate/context", () => {
        return HttpResponse.json({
          context: { weather: { summary: "Clear" } }
        });
      })
    );
  });

  it("submits the planner form and renders outfit cards", async () => {
    const user = userEvent.setup();
    render(<PlannerPage />, { wrapper: createWrapper() });

    await user.type(screen.getByLabelText(/date/i), "2024-11-05");
    await user.type(screen.getByLabelText(/location/i), "New York, NY");
    await user.selectOptions(screen.getByLabelText(/mood/i), "trendy");
    await user.click(screen.getByRole("button", { name: /generate plan/i }));

    expect(await screen.findByText("Test Outfit One")).toBeInTheDocument();
    expect(screen.getByText("Test Outfit Two")).toBeInTheDocument();
  });
});

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it } from "vitest";
import type { ReactNode } from "react";
import ChatPage from "../pages/ChatPage";

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } }
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe("ChatPage", () => {
  it("sends a message and renders assistant reply", async () => {
    const user = userEvent.setup();
    render(<ChatPage />, { wrapper: createWrapper() });

    await user.type(screen.getByLabelText(/message/i), "Hello stylist");
    await user.click(screen.getByRole("button", { name: /send/i }));

    expect(await screen.findByText("Hello stylist")).toBeInTheDocument();
    expect(await screen.findByText(/mocked response for: hello stylist/i)).toBeInTheDocument();
  });
});

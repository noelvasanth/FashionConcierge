import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { registerSW } from "virtual:pwa-register";
import App from "./app/App";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { Toaster } from "./components/ui/toaster";
import { ToastContextProvider } from "./components/ui/use-toast";
import "./styles.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false
    }
  }
});

async function enableMocks() {
  if (import.meta.env.DEV && !import.meta.env.VITE_DISABLE_MSW) {
    const { worker } = await import("./mocks/browser");
    await worker.start({
      onUnhandledRequest: "bypass"
    });
  }
}

enableMocks();

registerSW({
  immediate: true
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ToastContextProvider>
          <ErrorBoundary>
            <App />
            <Toaster />
          </ErrorBoundary>
        </ToastContextProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
);

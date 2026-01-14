import * as React from "react";

type ToastProps = {
  title?: string;
  description?: string;
  variant?: "default" | "destructive";
};

type ToastState = ToastProps & { id: string };

type ToastContextValue = {
  toasts: ToastState[];
  toast: (toast: ToastProps) => void;
  dismiss: (toastId?: string) => void;
};

const ToastContext = React.createContext<ToastContextValue | undefined>(undefined);

export const ToastContextProvider = ({ children }: { children: React.ReactNode }) => {
  const [toasts, setToasts] = React.useState<ToastState[]>([]);

  const toast = React.useCallback((toastData: ToastProps) => {
    const id = crypto.randomUUID();
    setToasts((prev) => [...prev, { ...toastData, id }]);
    return id;
  }, []);

  const dismiss = React.useCallback((toastId?: string) => {
    setToasts((prev) => (toastId ? prev.filter((toastItem) => toastItem.id !== toastId) : []));
  }, []);

  return <ToastContext.Provider value={{ toasts, toast, dismiss }}>{children}</ToastContext.Provider>;
};

export const useToast = () => {
  const context = React.useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return context;
};

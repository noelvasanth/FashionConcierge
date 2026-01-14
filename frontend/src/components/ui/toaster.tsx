import {
  Toast,
  ToastDescription,
  ToastProvider as RadixToastProvider,
  ToastTitle,
  ToastViewport
} from "./toast";
import { useToast } from "./use-toast";

const ToastRenderer = () => {
  const { toasts, dismiss } = useToast();

  return (
    <RadixToastProvider>
      {toasts.map((toast) => (
        <Toast key={toast.id} variant={toast.variant} onOpenChange={(open) => !open && dismiss(toast.id)}>
          <div className="grid gap-1">
            {toast.title && <ToastTitle>{toast.title}</ToastTitle>}
            {toast.description && <ToastDescription>{toast.description}</ToastDescription>}
          </div>
        </Toast>
      ))}
      <ToastViewport />
    </RadixToastProvider>
  );
};

export const Toaster = () => <ToastRenderer />;

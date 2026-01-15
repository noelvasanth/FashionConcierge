import { useMemo, useState } from "react";
import { Button } from "../components/ui/button";
import { useChatSend } from "../lib/api/hooks";
import { getSessionId, getUserId } from "../lib/session/session";
import { endSpan, formatErrorMessage, startSpan, trackEvent } from "../lib/telemetry/telemetry";

const ChatPage = () => {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<{ id: string; role: "user" | "assistant"; text: string }[]>(
    []
  );
  const chatMutation = useChatSend();
  const sessionId = useMemo(() => getSessionId(), []);
  const userId = useMemo(() => getUserId() ?? "guest", []);

  const handleSend = async () => {
    if (!message.trim()) {
      return;
    }

    const spanId = startSpan("chat.send", { userId, sessionId });
    const userMessage = { id: crypto.randomUUID(), role: "user" as const, text: message.trim() };
    setMessages((prev) => [...prev, userMessage]);
    setMessage("");

    try {
      const response = await chatMutation.mutateAsync({ message: userMessage.text, mood: "trendy" });
      const assistantMessage = {
        id: crypto.randomUUID(),
        role: "assistant" as const,
        text: response.reply
      };
      setMessages((prev) => [...prev, assistantMessage]);
      trackEvent("chat.reply.success", { userId, sessionId });
    } catch (error) {
      const assistantMessage = {
        id: crypto.randomUUID(),
        role: "assistant" as const,
        text: `Unable to send message. ${formatErrorMessage(error)}`
      };
      setMessages((prev) => [...prev, assistantMessage]);
      trackEvent("chat.reply.error", { userId, sessionId });
    } finally {
      endSpan(spanId);
    }
  };

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Chat</h1>
        <p className="text-sm text-muted-foreground">
          Ask the concierge for recommendations and get a conversational response.
        </p>
      </header>

      <div className="rounded-2xl border bg-white p-4 shadow-sm">
        <div className="space-y-4">
          {messages.length === 0 && (
            <p className="text-sm text-muted-foreground">Start the conversation to see replies.</p>
          )}
          {messages.map((chat) => (
            <div
              key={chat.id}
              className={`flex ${chat.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm shadow-sm ${
                  chat.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-foreground"
                }`}
              >
                {chat.text}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-2xl border bg-white p-4 shadow-sm">
        <label className="text-sm font-medium" htmlFor="chat-input">
          Message
        </label>
        <textarea
          id="chat-input"
          className="mt-2 w-full rounded-lg border border-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          rows={3}
          value={message}
          onChange={(event) => setMessage(event.target.value)}
        />
        <Button className="mt-3" onClick={handleSend} disabled={chatMutation.isPending}>
          {chatMutation.isPending ? "Sending..." : "Send"}
        </Button>
      </div>
    </div>
  );
};

export default ChatPage;

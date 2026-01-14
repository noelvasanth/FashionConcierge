import { useState } from "react";
import { Button } from "../components/ui/button";
import { useChat } from "../lib/api/hooks";

const ChatPage = () => {
  const [message, setMessage] = useState("Plan outfits for tomorrow in a trendy mood.");
  const chatMutation = useChat();

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Chat</h1>
        <p className="text-sm text-muted-foreground">
          Ask the concierge for recommendations and watch the structured response.
        </p>
      </header>
      <div className="rounded-2xl border bg-white p-4 shadow-sm">
        <label className="text-sm font-medium">Message</label>
        <textarea
          className="mt-2 w-full rounded-lg border border-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          rows={4}
          value={message}
          onChange={(event) => setMessage(event.target.value)}
        />
        <Button
          className="mt-3"
          onClick={() => chatMutation.mutate({ message, mood: "trendy" })}
          disabled={chatMutation.isPending}
        >
          {chatMutation.isPending ? "Sending..." : "Send"}
        </Button>
      </div>
      <div className="rounded-2xl border bg-white p-4 shadow-sm">
        <h2 className="text-lg font-semibold">Response</h2>
        <pre className="mt-3 whitespace-pre-wrap text-xs text-muted-foreground">
          {chatMutation.data ? JSON.stringify(chatMutation.data, null, 2) : "Awaiting response."}
        </pre>
      </div>
    </div>
  );
};

export default ChatPage;

import { http, HttpResponse } from "msw";

let wardrobeItems = [
  {
    id: "wardrobe-1",
    name: "Navy Trench",
    category: "outerwear",
    color: "navy",
    season: ["cold_weather"],
    imageUrl: "https://placehold.co/300x300",
    tags: ["business", "casual"]
  },
  {
    id: "wardrobe-2",
    name: "White Tee",
    category: "top",
    color: "white",
    season: ["all_year"],
    imageUrl: "https://placehold.co/300x300",
    tags: ["casual"]
  },
  {
    id: "wardrobe-3",
    name: "Charcoal Trousers",
    category: "bottom",
    color: "charcoal",
    season: ["all_year"],
    imageUrl: "https://placehold.co/300x300",
    tags: ["business"]
  }
];

let nextWardrobeId = 4;
let feedbackItems: Array<{
  id: string;
  userId: string;
  sessionId: string;
  page: string;
  traceId?: string;
  rating: "up" | "down";
  comment?: string;
  createdAt: string;
}> = [];
let nextFeedbackId = 1;

export const handlers = [
  http.post("/chat", async ({ request }) => {
    const body = (await request.json()) as { message: string; mood?: string };
    return HttpResponse.json({
      reply: `Mocked response for: ${body.message}`,
      outfits: [
        {
          outfitId: "outfit-1",
          name: "City Ready",
          itemIds: ["top-1", "bottom-2", "shoes-1"],
          rationale: "Balanced casual layers for an urban mood."
        }
      ]
    });
  }),
  http.post("/orchestrate/chat", async ({ request }) => {
    const body = (await request.json()) as { message: string };
    return HttpResponse.json({
      reply: `Mocked orchestrator reply for: ${body.message}`
    });
  }),
  http.get("/outfits", () => {
    return HttpResponse.json({
      outfits: [
        {
          outfitId: "outfit-2",
          name: "Warm Commute",
          itemIds: ["coat-1", "knit-3", "pants-2"],
          rationale: "Warm layers for a cool morning with office polish."
        },
        {
          outfitId: "outfit-3",
          name: "Relaxed Evening",
          itemIds: ["tee-4", "jeans-1", "sneaker-2"],
          rationale: "Casual silhouette for a laid-back evening."
        }
      ]
    });
  }),
  http.get("/wardrobe", () => {
    return HttpResponse.json({ items: wardrobeItems });
  }),
  http.post("/wardrobe", async ({ request }) => {
    const body = (await request.json()) as Omit<(typeof wardrobeItems)[number], "id">;
    const item = { id: `wardrobe-${nextWardrobeId++}`, ...body };
    wardrobeItems = [...wardrobeItems, item];
    return HttpResponse.json(item);
  }),
  http.put("/wardrobe/:id", async ({ request, params }) => {
    const body = (await request.json()) as Omit<(typeof wardrobeItems)[number], "id">;
    const { id } = params;
    const index = wardrobeItems.findIndex((item) => item.id === id);
    if (index === -1) {
      return HttpResponse.json({ message: "Wardrobe item not found" }, { status: 404 });
    }
    const updated = { id: String(id), ...body };
    wardrobeItems = wardrobeItems.map((item) => (item.id === id ? updated : item));
    return HttpResponse.json(updated);
  }),
  http.delete("/wardrobe/:id", ({ params }) => {
    const { id } = params;
    wardrobeItems = wardrobeItems.filter((item) => item.id !== id);
    return HttpResponse.json({ ok: true });
  }),
  http.post("/sessions", async ({ request }) => {
    const body = (await request.json()) as { userId?: string };
    return HttpResponse.json({
      sessionId: body.userId ? `session-${body.userId}` : "session-1"
    });
  }),
  http.post("/orchestrate/outfit", async () => {
    return HttpResponse.json({
      outfits: [
        {
          outfitId: "plan-1",
          name: "Downtown Layers",
          itemIds: ["jacket-1", "top-2", "pants-3"],
          rationale: "Layered pieces balanced for an urban mood."
        },
        {
          outfitId: "plan-2",
          name: "Smart Casual Mix",
          itemIds: ["blazer-1", "shirt-4", "loafer-2"],
          rationale: "Polished but relaxed for a flexible schedule."
        }
      ]
    });
  }),
  http.post("/orchestrate/context", async () => {
    return HttpResponse.json({
      context: {
        weather: { summary: "Clear", highF: 72, lowF: 58 },
        calendar: { summary: "Office day with evening social plan" }
      }
    });
  }),
  http.get("/feedback", () => {
    return HttpResponse.json({ items: feedbackItems.slice(0, 20) });
  }),
  http.post("/feedback", async ({ request }) => {
    const body = (await request.json()) as Omit<(typeof feedbackItems)[number], "id">;
    const record = { id: `feedback-${nextFeedbackId++}`, ...body };
    feedbackItems = [record, ...feedbackItems].slice(0, 20);
    return HttpResponse.json(record);
  })
];

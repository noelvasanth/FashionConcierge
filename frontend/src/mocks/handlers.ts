import { http, HttpResponse } from "msw";

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
    return HttpResponse.json({
      items: [
        {
          itemId: "coat-1",
          userId: "user-1",
          imageUrl: "https://placehold.co/300x300",
          sourceUrl: "https://example.com/coat",
          category: "outerwear",
          subCategory: "coat",
          colors: ["navy"],
          materials: ["wool"],
          brand: "Everlane",
          fit: "relaxed",
          seasonTags: ["cold_weather"],
          styleTags: ["business", "casual"]
        },
        {
          itemId: "tee-4",
          userId: "user-1",
          imageUrl: "https://placehold.co/300x300",
          sourceUrl: "https://example.com/tee",
          category: "top",
          subCategory: "tee",
          colors: ["white"],
          materials: ["cotton"],
          brand: "COS",
          fit: "slim",
          seasonTags: ["all_year"],
          styleTags: ["casual"]
        },
        {
          itemId: "pants-2",
          userId: "user-1",
          imageUrl: "https://placehold.co/300x300",
          sourceUrl: "https://example.com/pants",
          category: "bottom",
          subCategory: "trousers",
          colors: ["charcoal"],
          materials: ["cotton"],
          brand: "Uniqlo",
          fit: "slim",
          seasonTags: ["all_year"],
          styleTags: ["business"]
        }
      ]
    });
  })
];

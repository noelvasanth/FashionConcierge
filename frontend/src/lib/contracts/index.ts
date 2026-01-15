import { z } from "zod";

export const ChatRequestSchema = z.object({
  message: z.string().min(1),
  mood: z.enum(["happy", "neutral", "trendy", "casual", "festive", "urban"]).optional(),
  date: z.string().optional()
});

export type ChatRequest = z.infer<typeof ChatRequestSchema>;

export const ChatResponseSchema = z.object({
  reply: z.string(),
  outfits: z
    .array(
      z.object({
        outfitId: z.string(),
        name: z.string(),
        itemIds: z.array(z.string()),
        rationale: z.string()
      })
    )
    .optional()
});

export type ChatResponse = z.infer<typeof ChatResponseSchema>;

export const OutfitRecommendationResponseSchema = z.object({
  outfits: z.array(
    z.object({
      outfitId: z.string(),
      name: z.string(),
      itemIds: z.array(z.string()),
      rationale: z.string()
    })
  )
});

export type OutfitRecommendationResponse = z.infer<typeof OutfitRecommendationResponseSchema>;

export const WardrobeItemSchema = z.object({
  itemId: z.string(),
  userId: z.string(),
  imageUrl: z.string().url(),
  sourceUrl: z.string().url().optional(),
  category: z.string(),
  subCategory: z.string().optional(),
  colors: z.array(z.string()),
  materials: z.array(z.string()),
  brand: z.string(),
  fit: z.string(),
  seasonTags: z.array(z.string()),
  styleTags: z.array(z.string())
});

export type WardrobeItem = z.infer<typeof WardrobeItemSchema>;

export const WardrobeResponseSchema = z.object({
  items: z.array(WardrobeItemSchema)
});

export const SessionResponseSchema = z.object({
  sessionId: z.string()
});

export type SessionResponse = z.infer<typeof SessionResponseSchema>;

export const OrchestrateRequestSchema = z.object({
  userId: z.string(),
  sessionId: z.string().optional(),
  date: z.string(),
  location: z.string(),
  mood: z.string()
});

export type OrchestrateRequest = z.infer<typeof OrchestrateRequestSchema>;

export const OrchestrateOutfitResponseSchema = z.object({
  outfits: z.array(
    z.object({
      outfitId: z.string(),
      name: z.string(),
      itemIds: z.array(z.string()),
      rationale: z.string()
    })
  )
});

export type OrchestrateOutfitResponse = z.infer<typeof OrchestrateOutfitResponseSchema>;

export const OrchestrateContextResponseSchema = z.object({
  context: z.record(z.unknown())
});

export type OrchestrateContextResponse = z.infer<typeof OrchestrateContextResponseSchema>;

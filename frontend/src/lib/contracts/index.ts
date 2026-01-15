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
  id: z.string(),
  name: z.string(),
  category: z.string(),
  color: z.string().optional(),
  season: z.array(z.string()).optional(),
  imageUrl: z.string().url().optional(),
  tags: z.array(z.string()).optional()
});

export type WardrobeItem = z.infer<typeof WardrobeItemSchema>;

export const WardrobeListResponseSchema = z.object({
  items: z.array(WardrobeItemSchema)
});

export const WardrobeMutationResponseSchema = WardrobeItemSchema;

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

export const FeedbackSchema = z.object({
  id: z.string(),
  userId: z.string(),
  sessionId: z.string(),
  page: z.string(),
  traceId: z.string().optional(),
  rating: z.enum(["up", "down"]),
  comment: z.string().optional(),
  createdAt: z.string()
});

export type FeedbackRecord = z.infer<typeof FeedbackSchema>;

export const FeedbackListResponseSchema = z.object({
  items: z.array(FeedbackSchema)
});

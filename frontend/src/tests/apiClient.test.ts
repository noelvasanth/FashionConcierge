import { describe, expect, it, vi } from "vitest";
import { apiFetch, ApiError } from "../lib/api/apiClient";

const mockFetch = (response: Response) => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(response);
};

describe("apiFetch", () => {
  it("throws ApiError with details on non-ok responses", async () => {
    const errorPayload = { message: "Bad request", code: "INVALID" };
    mockFetch(
      new Response(JSON.stringify(errorPayload), {
        status: 400,
        headers: { "content-type": "application/json" }
      })
    );

    await expect(apiFetch("/test"))
      .rejects.toBeInstanceOf(ApiError)
      .then((error) => {
        const apiError = error as ApiError;
        expect(apiError.message).toBe("Bad request");
        expect(apiError.status).toBe(400);
        expect(apiError.details).toEqual(errorPayload);
      });

    vi.restoreAllMocks();
  });
});

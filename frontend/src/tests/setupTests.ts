import "@testing-library/jest-dom";
import { webcrypto } from "node:crypto";
import { afterAll, afterEach, beforeAll } from "vitest";
import { server } from "../mocks/server";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));

afterEach(() => server.resetHandlers());

afterAll(() => server.close());

if (!globalThis.crypto) {
  globalThis.crypto = webcrypto;
}

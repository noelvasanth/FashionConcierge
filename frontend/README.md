# Fashion Concierge Frontend (Phase 1)

This is the minimal Vite + React + TypeScript frontend foundation for the Fashion Concierge MVP.
It provides routing, a responsive shell layout, typed API contracts, TanStack Query, MSW mocks,
and a lightweight UI system with Tailwind + shadcn UI components.

## Setup

```bash
cd frontend
npm install
```

## Development

```bash
npm run dev
```

The dev server runs with MSW enabled by default (only in dev mode). API calls are mocked unless
you set a real backend URL.

## Environment Variables

Create a `.env` file in `frontend/`:

```
VITE_API_BASE_URL=http://localhost:8000
VITE_CHAT_ENDPOINT=/chat
VITE_DISABLE_MSW=false
```

If `VITE_API_BASE_URL` is not set, the frontend uses relative URLs which work with MSW and any
proxy setup.

## MSW Usage

MSW starts automatically in dev. Mock handlers live in `src/mocks/handlers.ts`.

To turn off MSW, either build for production (`npm run build`) or set `VITE_DISABLE_MSW=true` in
your `.env` file.

## Chat Endpoint Configuration

Set `VITE_CHAT_ENDPOINT` to override the default `/chat` endpoint. This is useful if your backend
exposes `/orchestrate/chat` or another route.

## PWA Testing

1. Run `npm run dev` (PWA service workers are enabled in dev).
2. Open the app in Chrome and look for the install icon in the address bar.
3. Use DevTools → Application → Service Workers to confirm registration.
4. Use DevTools → Application → Manifest to verify the manifest configuration.

## Pointing to a Real Backend

1. Start the backend server.
2. Set `VITE_API_BASE_URL` to the backend URL.
3. If the chat route is not `/chat`, set `VITE_CHAT_ENDPOINT` accordingly.
4. Restart the dev server so the env var is picked up.
5. Disable MSW in dev by setting `VITE_DISABLE_MSW=true` or by running a production build/preview.
6. Confirm the Phase 2 flows by visiting `/onboarding` to create a session, then `/app/planner`
   to call the real orchestrator endpoints.

## Scripts

- `npm run dev` — Start Vite dev server
- `npm run build` — Production build
- `npm run preview` — Preview production build
- `npm run lint` — ESLint
- `npm run typecheck` — TypeScript typecheck
- `npm run test` — Run Vitest tests
- `npm run test:watch` — Run Vitest in watch mode

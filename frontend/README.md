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
```

If `VITE_API_BASE_URL` is not set, the frontend uses relative URLs which work with MSW and any
proxy setup.

## MSW Usage

MSW starts automatically in dev. Mock handlers live in `src/mocks/handlers.ts`.

To turn off MSW, either build for production (`npm run build`) or remove the `enableMocks()` call
in `src/main.tsx`.

## Pointing to a Real Backend

1. Start the backend server.
2. Set `VITE_API_BASE_URL` to the backend URL.
3. Restart the dev server so the env var is picked up.
4. Disable MSW in dev by commenting out `enableMocks()` in `src/main.tsx` or by running a
   production build/preview.
5. Confirm the Phase 2 flows by visiting `/onboarding` to create a session, then `/app/planner`
   to call the real orchestrator endpoints.

## Scripts

- `npm run dev` — Start Vite dev server
- `npm run build` — Production build
- `npm run preview` — Preview production build
- `npm run lint` — ESLint
- `npm run typecheck` — TypeScript typecheck
- `npm run test` — Run Vitest tests

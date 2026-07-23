# React Frontend

The frontend is a React and TypeScript application for operating Lain5G-Lab
through the FastAPI backend. The operator interface is English-only; browser
preferences cover appearance, text size, and font style, not language.

## Local Development

```bash
make frontend-install
make frontend-dev
```

`make frontend-install` uses `npm ci` exclusively and preserves the dependency
closure and integrity values in `frontend/package-lock.json`.

The Vite server listens on `http://127.0.0.1:5173` and proxies `/api` to
`http://127.0.0.1:8000`.

## Variables

Example from `frontend/.env.example`:

```env
VITE_API_BASE_URL=
```

Leave it empty to use relative `/api` paths. To connect to another backend while
developing, set a value such as
`VITE_API_BASE_URL=http://127.0.0.1:8000`.

## Scripts

```bash
make frontend-build
make frontend-test
```

The same checks can be run directly from `frontend/`:

```bash
npm ci
npm run build
npm test
```

## Main Routes

- `/`: backend and deployment status plus `start`, `stop`, `restart`, and
  `validate` actions.
- `/scenarios`: scenario catalog and guarded workspaces.
- `/deployments`: profile editing, validation, comparison, and application.
- `/subscribers`: Open5GS subscriber administration.
- `/validation`: latest validation report and manual execution.
- `/logs`: deployment logs by service and line count.
- `/runs`: execution history.
- `/runs/:runId`: execution details.

## Production

The Docker image builds the frontend with Vite and serves `dist/` with Nginx.
Nginx also proxies `/api` to the application stack's backend service.

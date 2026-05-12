# Frontend

React + Vite dashboard cho AI Marketing system.

## Local development

```bash
npm ci
npm run dev
```

Mặc định dev server proxy:

- `/api/*` -> `http://localhost:8000`
- `/run` -> `http://localhost:8000`

## Environment

Set `VITE_API_BASE_URL` nếu frontend deploy tách khỏi backend:

```env
VITE_API_BASE_URL=https://your-api-host
```

Nếu biến này để trống, frontend sẽ dùng relative path.

## Build

```bash
npm run build
```

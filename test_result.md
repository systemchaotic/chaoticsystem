# user_problem_statement
an app for developing an idle game with thematically coherent content

# context_summary
- Repo was empty. I scaffolded a FastAPI backend and React frontend following platform rules.
- Backend: /api routes, Mongo via MONGO_URL env, UUIDs used (no ObjectId).
- Frontend: React 18 with Tailwind; uses REACT_APP_BACKEND_URL for calls.
- Pending: AI generation endpoints (awaiting provider + key), richer UI polish, tests.

# backend_endpoints
- GET /api/health -> { ok, collections }
- POST /api/packs -> ContentPack
- GET /api/packs -> [ContentPack]
- GET /api/packs/{id} -> ContentPack
- PUT /api/packs/{id} -> ContentPack
- DELETE /api/packs/{id} -> { ok }

Schema: ContentPack { id, title, theme, summary?, author_email?, resources[], upgrades[], areas[], factions[] }
Nested types have id/key/name/description plus fields.

# notes_for_test_agent
- Use REACT_APP_BACKEND_URL for frontend calls; backend requires /api prefix.
- Mongo URL is taken from backend/.env. No hardcoding in code.

# next_steps
- Receive AI provider choice and API key from user; then implement AI generation endpoint and minimal UI to trigger it.
- Run backend deep tests after confirming Mongo connectivity works in this environment.
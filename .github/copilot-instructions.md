**Project Overview**
- **Backend:** Flask app in `src/` exposing many REST blueprints (see `src/__init__.py`). Uses `mongoengine` and connects to multiple MongoDB aliases: `apografi`, `psped`, `resources`.
- **Frontend:** Angular 17 app lives in sibling folder `thryallis-frontend/` (build and dev commands in `thryallis-frontend/package.json`).

**How the backend is structured**
- **App bootstrap:** `src/__init__.py` creates the Flask app, configures JWT, CORS, registers blueprints and connects to MongoDB. Use `main.py` for local dev (`python main.py`) or `wsgi.py`/`gunicorn` for production.
- **Blueprints:** All endpoints are under `src/blueprints/` (e.g. `ota.py`, `apografi.py`, `psped.py`). Blueprints are registered with prefixes (e.g. `/ota`, `/remit`). When adding routes, follow existing patterns (Response + json.dumps + mimetype).
- **Models:** Domain models live under `src/models/` (e.g. `psped/`, `ota/`, `apografi/`). They use `mongoengine` Document classes and helper methods like `to_dict()` / `to_mongo()`.
- **Change logging:** Mutations typically create a `Change` document (see `src/blueprints/ota.py`) capturing `who`, `what`, and `change` for audit/history.

**Frontend structure & conventions**
- **Angular modules:** Main app code under `thryallis-frontend/src/app/`. Reusable services under `src/app/shared/services/` and components under `src/app/components/`.
- **Environments:** `environments/` contains `environment.ts`, `environment.development.ts`, and `environment.test.ts` used by build configurations.
- **Common services:** Many UI patterns rely on small services: `ConstOtaService` for grid defaults, `ModalService` to open detail modals, `OtaService`/`LegalProvisionService` for API calls. Inspect service names when adding features.

**Key developer workflows / commands**
- Backend (dev): `python main.py` (runs Flask dev server). Production: use `gunicorn wsgi:app` or `deploy.sh` / `supervisor` as project uses.
- Backend deps: use `requirements.txt` (pip install -r requirements.txt). Note: `src/config.py` contains connection constants and secrets (replace with environment variables in CI/production).
- Frontend: from `thryallis-frontend/` run `npm start` (alias `ng serve`) for dev, `npm run build` to build, `npm run build-test` to build test config, and `npm test` for unit tests.
- Deploy helper: `thryallis-backend/deploy.sh` rsyncs code and reloads supervisor on host `lola`.

**Patterns & conventions specific to this repo**
- Responses: endpoints return `flask.Response(json.dumps(...), mimetype="application/json", status=...)` rather than `flask.jsonify` consistently.
- DB connections: `mongoengine.connect()` is called multiple times with `alias` to target different logical DBs — use `Model._get_collection()` or `Model.objects(db_alias='...')` patterns carefully.
- Authentication: endpoints that mutate data use `@jwt_required()` and `get_jwt_identity()`; follow this when adding protected endpoints.
- Error handling: Many routes catch Exception and return HTTP 500 with a localized error message; keep this existing pattern for uniform UX.
- Large file uploads: `UPLOAD_FOLDER` and `MAX_CONTENT_LENGTH` defined in `src/config.py`; handlers enforce 413 and custom error message.

**Integration points & external dependencies**
- MongoDB (Atlas) via `MONGO_URI` in `src/config.py`.
- OAuth / GSIS integration: configuration values (CLIENT_ID, TOKEN_URL, etc.) are in `src/config.py` — inspect these when working on login flows.
- Frontend uses `ag-grid-angular`, `ngx-extended-pdf-viewer`, `@ngrx/store` — check `package.json` for exact versions before upgrading.

**Files to read first when onboarding**
- `src/__init__.py` — app wiring and blueprint registration
- `src/config.py` — environment keys, DB URIs, JWT secret (do not commit new secrets)
- `src/blueprints/ota.py` — representative CRUD + change logging pattern
- `src/models/` — domain models and helper serialization methods
- `thryallis-frontend/package.json` and `thryallis-frontend/src/app/shared/services/` — frontend build and API integration patterns

**Safety & practical notes for AI agents**
- Do not introduce secrets into source files. This repo currently contains secrets in `src/config.py`; prefer suggesting use of environment variables instead of editing the file to add keys.
- Follow existing response and error patterns; avoid changing API response format without updating all callers (frontend services expect the current shape).
- When adding backend endpoints, update any frontend service that consumes them in `thryallis-frontend/src/app/shared/services/`.

If anything here is unclear or you'd like me to expand specific areas (example: add a short example of a `mongoengine` model or an Angular service pattern), tell me which area and I'll iterate.

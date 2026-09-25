# Walkthrough: Adding A2UI to ApexMath

We integrated **A2UI** into ApexMath using the `enable-a2ui` skill so that the agent emits structured UI surfaces (cards, columns, rows, text, images) rendered natively in the ADK dev UI (`adk web`).

---

## 1. SDK Dependencies
- Added `a2ui-agent-sdk>=0.4.0,<0.5.0` (which provides `A2uiSchemaManager` and `BasicCatalog`).
- Added `sse-starlette` and configured `override-dependencies = ["a2a-sdk>=1.0,<2"]` in [`pyproject.toml`](apexmath/pyproject.toml) to cleanly satisfy `a2a-sdk[http-server]` requirements.

---

## 2. Callback Integration
- Copied [`a2ui_utils.py`](apexmath/app/a2ui_utils.py) into `apexmath/app/`.
- This callback parses the raw A2UI JSON output from the model and wraps it into `<a2a_datapart_json>{"kind":"data","metadata":{"mimeType":"application/json+a2ui"},"data":{...}}</a2a_datapart_json>` parts recognized by the `adk web` renderer.

---

## 3. System Prompt & Agent Wiring
In [`apexmath/app/agent.py`](apexmath/app/agent.py):
- Initialized `A2uiSchemaManager` targeting version **`0.8`** with `BasicCatalog.get_config("0.8")`.
- Generated the agent's system prompt using `schema_manager.generate_system_prompt(...)` with the ApexMath role description, pedagogical guidelines, and component constraints (Card, Column, Row, Text, Image).
- Attached `after_model_callback=a2ui_callback` to `root_agent` alongside existing `after_agent_callback=generate_memories_callback`.

---

## 4. Verification & Testing
1. **End-to-End Query:** Tested via `agents-cli run --mode adk "Introduce yourself in a card"`.
   - The model generated valid A2UI 0.8 components (`Card` > `Column` > `Text` headings and body).
   - `a2ui_callback` successfully intercepted and wrapped the messages into `application/json+a2ui` dataparts.
2. **Linting & Code Quality:** Ran `agents-cli lint`:
   - `ruff check`, `ruff format`, `codespell`, and `ty check` all passed with 0 errors.
3. **Playground Active:** Relaunched local playground with:
   ```bash
   uv run adk web . --port 8080 --reload_agents --memory_service_uri=agentengine://7022297092605345792
   ```
   Server is live at **http://127.0.0.1:8080**.

---

## 5. Redeployment to Agent Platform (Agent Runtime)
- **Deployed via `agents-cli deploy`** with `--project qwiklabs-gcp-04-47563a3307b3 --region us-east1` and `--update-env-vars`:
  - `GOOGLE_GENAI_USE_VERTEXAI=true`
  - `GOOGLE_CLOUD_PROJECT=qwiklabs-gcp-04-47563a3307b3`
  - `GOOGLE_CLOUD_LOCATION=us-east1`
  - `MEMORY_BANK_ID=7022297092605345792`
  - `MEMORY_SERVICE_URI=agentengine://7022297092605345792`
  - `STORAGE_BUCKET_NAME=apexmath-visuals-47563a3307b3`
- **New Agent Runtime Resource**: `projects/210430842247/locations/us-east1/reasoningEngines/8622095307112448000`
- **Updated `deployment_metadata.json`**:
  ```json
  {
    "remote_agent_runtime_id": "projects/210430842247/locations/us-east1/reasoningEngines/8622095307112448000",
    "deployment_target": "agent_runtime",
    "is_a2a": true,
    "agent_directory": "app",
    "deployment_timestamp": "2026-09-25T22:42:45.601050+00:00"
  }
  ```
- **Verified Remote Query**: Successfully queried the deployed Reasoning Engine via `agents-cli run --mode adk`.

---

## 6. Service Account IAM Permissions
Granted the required roles to the deployed agent's service account (`service-210430842247@gcp-sa-aiplatform-re.iam.gserviceaccount.com`):
1. **Firestore**: `roles/datastore.user` bound at the project level (`qwiklabs-gcp-04-47563a3307b3`).
2. **Cloud Storage**: `roles/storage.objectAdmin` bound directly to the image bucket (`gs://apexmath-visuals-47563a3307b3`).

---

## 7. Chat Frontend (`./frontend`)
- **Template Copied**: Extracted minimal FastAPI proxy and plain chat UI template from `build-agent-frontend` into `./frontend` (`apexmath/frontend` and linked at root `frontend`).
- **Configuration & Wiring**:
  - `AGENT_ENGINE_RESOURCE_NAME`: `projects/210430842247/locations/us-east1/reasoningEngines/8622095307112448000`
  - `AGENT_DIRECTORY`: `app`
  - Configured in [`.env`](apexmath/frontend/.env) and [`main.py`](apexmath/frontend/main.py) with fallback defaults.
- **Protocol & Rendering**:
  - Communicates directly with deployed Agent Engine over the A2A JSON-RPC protocol via ADC.
  - Proxy extracts both plain text and rich `application/json+a2ui` data parts.
  - Native client-side renderer in [`index.html`](apexmath/frontend/static/index.html) renders A2UI Cards, Columns, Rows, Texts, and Images without third-party frameworks.
- **Verification**:
  - Tested single-turn prompt (`/chat`) producing rendered A2UI cards.
  - Tested multi-turn conversational memory over A2A carrying `context_id` across turns.
  - Live server running on **`http://localhost:8080`** (serving static HTML/JS and proxying `/chat`).
  - Verified via `curl http://localhost:8080/` (200 OK) and `POST /chat` returning A2UI card updates.

---

## 8. Frontend Deployment to Cloud Run
- **IAM Role**: Granted `roles/aiplatform.user` to the Cloud Run service account (`210430842247-compute@developer.gserviceaccount.com`) so it can authenticate and invoke the Reasoning Engine via A2A.
- **Service Name**: `apexmath-frontend`
- **Region**: `us-east1`
- **Service URL**: [https://apexmath-frontend-210430842247.us-east1.run.app](https://apexmath-frontend-210430842247.us-east1.run.app)
- **Environment Variables**:
  - `AGENT_ENGINE_RESOURCE_NAME`: `projects/210430842247/locations/us-east1/reasoningEngines/8622095307112448000`
  - `AGENT_DIRECTORY`: `app`
- **Verification**:
  - Root URL returns HTTP 200 with the static chat UI.
  - `/chat` endpoint successfully reaches the remote agent and returns rich A2UI cards.

---

## 9. Demo Video Recording with Upbeat Lo-Fi Soundtrack
- **Demo Video File**: [`apexmath_demo.mp4`](apexmath_demo.mp4) (Artifact copy: [`apexmath_demo.mp4`](apexmath_demo.mp4)).
- **Video Specifications**: 1280x720 (720p HD), H.264 progressive @ 25fps, AAC stereo 44.1kHz audio, 49.88 seconds duration.
- **Audio Track**: Synthesized 86 BPM upbeat lo-fi hip-hop soundtrack with Rhodes electric piano (Dm9 - G13 - Cmaj9 - Am9), warm sub-bass, boom-bap swing percussion, and vinyl warmth.
- **Scenarios Captured**:
  1. **Core Feature**: AP Calculus problem retrieval with progressive hint scaffolding, rendered in an A2UI card.
  2. **Rich Tool Call**: Firestore database scorecard lookup (`get_student_scorecard`) combined with multimodal image generation (`gemini-3.1-flash-lite-image` via `generate_concept_diagram`), rendered directly within an A2UI card displaying mastery stats and a high-resolution Unit Circle diagram.

---

## 10. Project Documentation & Looping Demo GIF
- **README Generated**: [`README.md`](README.md) and [`apexmath/README.md`](apexmath/README.md).
- **Embedded Demo GIF**: [`assets/demo.gif`](assets/demo.gif) (2.2 MB, 10 fps, 720p scaled, two-pass palette generated for crisp text/graphics and infinite looping).
- **Accurate Scope**: Grounded strictly in implemented code (`app/` and `agents-cli-manifest.yaml`). Documents wired services (Vertex AI Memory Bank, Firestore, Cloud Storage, Gemini 3.1 Flash Lite Image, A2UI 0.8) and marks planned features (SymPy sandbox proofs) as not yet implemented.
- **Clean Run Instructions**: Provided reproducible local CLI commands without ephemeral URLs or localhost hyperlinks.

---

## 11. GitHub Publication & Swag Submission
- **GitHub Repository**: [https://github.com/rajaramreddy/buildwithgemini-apexmath](https://github.com/rajaramreddy/buildwithgemini-apexmath)
- **Demo Video Asset**: [assets/apexmath_demo.mp4](assets/apexmath_demo.mp4) (Direct link in repo)
- **GitHub Release with Demo Video**: [ApexMath v1.0.0 Release](https://github.com/rajaramreddy/buildwithgemini-apexmath/releases/tag/v1.0.0)
- **Visibility**: Public
- **Committed By**: `rajaramreddy <rajaramreddy@users.noreply.github.com>`
- **Swag & Gallery Submission Form**: [Pre-filled Google Form](https://docs.google.com/forms/d/e/1FAIpQLSfvbIUMrHLf2iUYVgQkr981unQwuLdigLB7yJp3VdtYH85Dzw/viewform?usp=pp_url&entry.896374137=https%3A%2F%2Fgithub.com%2Frajaramreddy%2Fbuildwithgemini-apexmath&entry.339694639=ApexMath%20%28Pre-Calc%20%26%20AP%20Calculus%20Tutor%29&entry.82550013=A%20conversational%20agent%20that%20helps%20high%20school%20students%20master%20Pre-Calculus%20and%20AP%20Calculus%20concepts%20to%20score%20high%20on%20AP%20exams%2C%20with%20a%20catalog%20of%20curriculum%20units%2C%20targeted%20problem%20banks%2C%20and%20diagnostic%20review%20materials.)









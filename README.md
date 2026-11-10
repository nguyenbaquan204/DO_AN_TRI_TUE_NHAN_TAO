# AI Recruitment Assistant – Intelligent CV Screening & Job Matching System

## 1. Project Overview
This project is a full-stack AI recruitment platform built with FastAPI + React. It supports recruiter workflows such as job management, CV upload, JD analysis, AI-driven candidate matching, and dashboard analytics.

## 2. Features
- JWT authentication for admin and recruiter roles
- Job creation, editing, listing, and status management
- CV and JD upload with validation and file storage
- Text extraction from PDF and DOCX files, with Vietnamese/English OCR fallback
  for scanned PDF pages
- Job description import through public Greenhouse and Lever job APIs, with
  best-effort structured HTML import for other public job pages
- JD paste and PDF, DOCX, or TXT upload fallback for websites that block
  automated reading or render descriptions only in the browser
- Candidate profile extraction, user review and correction before saving
- Explainable hybrid ranking with multilingual E5 embeddings and TF-IDF
- Optional Sentence Transformer semantic similarity
- Candidate ranking and filtering
- Dashboard metrics and database persistence
- Optional trained Random Forest suitability classifier
- API docs via Swagger and ReDoc

## 3. Architecture
The system is split into frontend, backend, AI services, and data modules.

## 4. Tech Stack
- Frontend: React + Vite + React Router
- Backend: FastAPI + SQLAlchemy + Pydantic
- AI: scikit-learn, sentence-transformers, pdfplumber, PyMuPDF,
  Tesseract OCR, python-docx
- Storage: SQLite for local development

## 5. Current System
- CV parser for PDF and DOCX files
- JD parser
- Skill extraction and normalization
- TF-IDF matching baseline
- Evidence-based scoring using skills, experience, education, projects, and text similarity
- Candidate ranking
- Dashboard aggregation
- SQLite database persistence

## 6. Semantic Model and Ranking
The semantic signal uses the pretrained `intfloat/multilingual-e5-small` text
embedding model, which supports Vietnamese. It maps CV and job-description
chunks into vectors; cosine similarity estimates how closely the meaning of a
job requirement matches parts of a CV. It is a pretrained model, not a model
trained or fine-tuned on this project's candidate records.

The final ranking remains explainable: required skills 40%, text similarity
20%, experience 15%, education 15%, and project signal 10%. When E5 is ready,
the text portion is split evenly between E5 semantic similarity and TF-IDF.
When E5 is disabled or unavailable, the full text portion uses TF-IDF and the
API reports that fallback. Scores are ranking signals, not probabilities of
being hired.

Docker installs the embedding library and enables E5 by default. The first
matching request downloads the model weights; Docker Compose keeps them in the
`embedding-cache` volume for later runs. A blocked download or model loading
problem falls back to TF-IDF instead of preventing the app from starting. To
run locally, install `backend/requirements-embeddings.txt` and set
`ENABLE_SENTENCE_TRANSFORMERS=true` in `.env`. Set it to `false` to force the
lighter TF-IDF fallback.

## 7. Trained Suitability Model

The project includes a reproducible `RandomForestClassifier` pipeline for the
candidate-job suitability task. It predicts `HIGH`, `MEDIUM`, or `LOW` and
returns `predict_proba()` as model confidence. The model uses numeric features
built from the actual candidate and job text:

- required and preferred skill overlap;
- candidate and required experience;
- experience gap and match ratio;
- education match;
- project relevance;
- TF-IDF similarity;
- semantic similarity only when the optional model is genuinely available.

The model was trained on the 93,733-record merged resume/job dataset documented
under `data/training/resume-job-fit-merged-v1/`. The large Parquet shards are
not committed to this GitHub repository; download the dataset from
[Hugging Face](https://huggingface.co/datasets/med2425/resume-job-fit-merged-v1)
and place its three Parquet files under
`data/training/resume-job-fit-merged-v1/data/` to retrain. It contains generated
and synthetic records. Evaluation splits are grouped by resume to prevent the
same resume appearing in both training and test. This does not make the data an
independent human-labelled benchmark; see
[data/training/README.md](data/training/README.md) for metrics and limitations.
The model is experimental decision support and is not validated for automated
hiring decisions.

Train the model with:

```bash
python backend/training/train_model.py
```

The artifact is written to
`backend/models/candidate_job_suitability_model.joblib` and metadata is written
to `backend/models/model_metadata.json`.

Model screening responses include `prediction_mode`. It is
`trained-model` only when the artifact is loaded; otherwise the existing
evidence-based rule/TF-IDF flow is returned as `fallback`.

Model status is available at:

```text
GET /api/model/status
```

## 8. Database
The app uses SQLite by default for local development and supports a relational schema for users, jobs, candidates, audits, and matching results.

## 9. Installation
1. Copy `.env.example` to `.env` and review the development settings.
2. For local scanned-PDF support, install Tesseract OCR with English and
   Vietnamese language data and make it available on `PATH`. Docker installs
   these automatically.
3. In `backend/`, create and activate a virtual environment, then install
   `requirements-dev.txt` and `requirements-embeddings.txt` for the full local
   semantic-matching flow.
4. In `frontend/`, run `npm install`.
5. Start the backend and frontend with the commands below.

## 10. Environment Variables
See `.env.example`.

## 11. Running Frontend
```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

## 12. Running Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 13. Running Docker
```bash
docker compose up --build
```

## 14. API Documentation
- Swagger: http://localhost:8000/docs
- Redoc: http://localhost:8000/redoc

## 15. Dataset
Training data and its source notes are under `data/training/`. The resume/job
dataset includes generated examples and model-assisted labels; it is not an
independently human-labelled production benchmark. Small examples under
`data/sample_cvs/` and `data/sample_jds/` are for demos.

## 16. Evaluation
The `reviewed-profile-v2` scoring pipeline uses the stored structured CV fields
for ranking and classifier features. Explicitly cleared fields and zero years
are preserved. Raw text is used for legacy profiles without structured fields.
Existing saved matches must be screened again; their detail page shows a notice.

The evaluation CLI uses the same input adapter as the API, rejects duplicate or
missing labeled pairs, and records the scoring version and input fingerprint.
When E5 is unavailable, `semantic_comparison_valid` is false and the hybrid
metrics are null: fallback results are not presented as an E5 comparison.

To compare the TF-IDF baseline with the E5 + TF-IDF ranking, run:

```bash
python backend/evaluation/run_evaluation.py --data data/evaluation/matches.json --k 5
```

This reports NDCG@5 and MRR@5 per job. The relevance labels must be independently
reviewed by people before the resulting numbers are used in the thesis. See
`data/evaluation/README.md` for the annotation rubric and metric limitations.
The separate Random Forest holdout evaluation is available with
`python backend/training/evaluate_model.py`; that classifier is an additional
reference signal and does not determine the main ranking order.

## 17. Demo Quick Start
For the local demo profile, keep `SEED_DEMO_DATA=true` in `.env` (Docker Compose
enables it automatically). Disable it for deployments that should not create a
known demo login, and set a private `JWT_SECRET` before exposing the service.
Local development enables demo data by default. The seeded admin credentials
can be overridden with `DEMO_ADMIN_EMAIL` and `DEMO_ADMIN_PASSWORD`.

Admin demo login:

```text
Email: admin@example.com
Password: admin123
```

Recruiter demo login:

```text
Email: recruiter@example.com
Password: password123
```

Run the backend and frontend using the commands above, then use the Jobs page
to create a structured job, upload a JD, upload one or more CVs, screen the
candidates, inspect ranking and match detail, and view the dashboard.

Run the backend tests:

```bash
cd backend
python -m pytest -q
```

If the backend was installed with only `requirements.txt`, install the test
dependency first with `pip install -r requirements-dev.txt`.

Install frontend dependencies and build:

```bash
cd frontend
npm install
npm run build
```

## 18. Screenshots
Add screenshots here in a real deployment.

## 19. Limitations
- CV extraction accuracy depends on document quality
- Local SQLite is suitable for demos but not for large production workloads
- The Random Forest's grouped test macro F1 is 0.5645; its accuracy (0.7128)
  is below the majority-class baseline (0.7434) on the imbalanced evaluation
  set. See the training report before interpreting model scores.
- Candidate parsing is heuristic and may return null/empty fields
- Sentence Transformer availability depends on the local PyTorch/runtime
  environment; TF-IDF is the stable fallback

## 20. Future Improvements
- Deploy PostgreSQL and Celery
- Add more robust resume parser
- Fine-tune a model only after collecting a larger labeled dataset
- Expand admin tools, audit logs, and role-based workflows

## Human labelled evaluation workspace
Open `/experiments` after logging in. Prepare a frozen pool from up to 10 open
jobs and 20 existing candidates (at most 200 pairs). Preparation is idempotent.
These are local project samples, not newly collected web CVs or human labels.
Read each CV/JD, choose relevance 0/1/2 and record the reason. Labels persist in
`evaluation_pairs` in `backend/app.db`, with reviewer and timestamp. A job needs
at least five pairs, all labeled, with at least one relevant candidate before
comparison runs. Export includes frozen inputs and reviewer notes for checking.
Keep the test pool separate from model/weight tuning. Ideally have a second
person review labels independently before using results in the thesis.
NDCG@5 and MRR@5 are reported per job, with MRR treating labels 1 and 2 as relevant.
E5 results are omitted when unavailable. The current UI uses one final label per
pair; it does not implement independent multi-reviewer agreement statistics.

Demo sequence: create/import JD → review requirements → preview CV → correct
fields → save → screen candidates → inspect explanations → label evaluation
pairs → compare and export. Previously saved matches need re-screening.
For backup, stop the backend and copy `backend/app.db` and `backend/uploads`
together to a dated backup directory; restore both while the backend is stopped.
Do not remove Docker volumes to reset the demo. The E5 cache is a separate volume.

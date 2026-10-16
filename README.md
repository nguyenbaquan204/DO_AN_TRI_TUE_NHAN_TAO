# AI Recruitment Assistant – Intelligent CV Screening & Job Matching System

## 1. Project Overview
This project is a full-stack AI recruitment platform built with FastAPI + React. It supports recruiter workflows such as job management, CV upload, JD analysis, AI-driven candidate matching, and dashboard analytics.

## 2. Features
- JWT authentication for admin and recruiter roles
- Job creation, editing, listing, and status management
- CV and JD upload with validation and file storage
- Text extraction from PDF and DOCX files, with Vietnamese/English OCR fallback
  for scanned PDF pages
- Candidate profile extraction and skill normalization
- TF-IDF matching with evidence-based scoring
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
- AI: scikit-learn, optional sentence-transformers, pdfplumber, PyMuPDF,
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

## 6. Semantic Model
Sentence Transformer is optional. The configured model is
`sentence-transformers/all-MiniLM-L6-v2`.

The model is lazy-loaded only when semantic matching is requested. It is not
loaded while the backend starts. If it is unavailable, cannot be imported, or
cannot load its model weights, matching continues with TF-IDF and returns
`embedding_status = "tfidf-fallback"`. No fake semantic vector or score is
generated.

Install `backend/requirements-embeddings.txt` only if you want the optional
Sentence Transformer integration; the default backend dependencies stay
lighter and matching uses TF-IDF otherwise.

For a machine where the dependency and model are known to be stable, opt in
explicitly:

```powershell
$env:ENABLE_SENTENCE_TRANSFORMERS = "1"
```

The default is disabled (`0`) so a Windows/PyTorch native runtime problem
cannot crash the normal demo backend startup. This project does not train or
fine-tune a custom model.

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
   `requirements-dev.txt` (this includes the backend and test dependencies).
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
To reproduce the Random Forest's grouped holdout report, run:

```bash
python backend/training/evaluate_model.py
```

This reports Precision, Recall, F1, the confusion matrix, and a majority-class
baseline in `data/training/evaluation_report.md` and `.json`. The separate
matching evaluation on the small project examples is available with
`python backend/evaluation/run_evaluation.py`; it reports Sentence Transformer
results only when the optional model is actually available.

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

# LUNA Localization RAG Evaluator

LUNA is a local evaluation framework for game localization research. It uses a LangGraph workflow, optional ChromaDB retrieval, BGE-M3 embeddings, DeepSeek structured scoring, and adaptive routing between a fast path and a deeper audit path.

This export is the core research/engineering version. It does not include the questionnaire website, Vercel API, mock data, Steam depot files, local vector database files, or secrets.

## Repository Contents

- `luna/`: LangGraph graph, scoring agents, DeepSeek client, retriever, batch evaluation, and analysis tools.
- `tools/scripts/`: data extraction, corpus preparation, sampling, knowledge-base construction, and retrieval utilities.
- `data/survey/`: the current 100-item test set used for LUNA evaluation.
- `data/processed/luna_knowledge_base/`: processed evidence and terminology files used to build the local RAG knowledge base.
- `data/processed/luna_runs/survey_eval/`: selected real evaluation outputs for the final vertical architecture.
- `docs/`: architecture and data provenance notes.

## Excluded

- Steam depot downloads and game executables.
- Raw/interim extraction folders.
- Local ChromaDB files under `data/vector_db/`.
- Questionnaire web application and API code.
- Participant response database.
- API keys and local environment files.
- LaTeX build artifacts.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

For real DeepSeek evaluation, set `DEEPSEEK_API_KEY` in the current shell or local environment.

## Rebuild The Local Vector Database

The repository includes the processed evidence file, but not the ChromaDB database itself. Rebuild it locally:

```powershell
python -m tools.scripts.build_lore_vector_db `
  --use-curated `
  --evidence-jsonl data/processed/luna_knowledge_base/evidence.jsonl `
  --db-dir data/vector_db/luna_lore_chroma `
  --embedding-backend bge-m3
```

For a fast local smoke test without downloading BGE-M3:

```powershell
python -m tools.scripts.build_lore_vector_db `
  --use-curated `
  --evidence-jsonl data/processed/luna_knowledge_base/evidence.jsonl `
  --db-dir data/vector_db/luna_lore_chroma `
  --embedding-backend hash
```

## Run Evaluation

BGE-M3 RAG, final vertical architecture:

```powershell
python -m luna.batch_evaluate_survey `
  --survey-csv data/survey/survey_items_100.csv `
  --embedding-backend bge-m3 `
  --routing-threshold 0.45 `
  --low-score-threshold 2.0 `
  --low-average-threshold 2.5 `
  --run-name items100_bge_m3_t045_vertical_riskaware
```

No-RAG baseline:

```powershell
python -m luna.batch_evaluate_survey `
  --survey-csv data/survey/survey_items_100.csv `
  --no-rag `
  --embedding-backend hash `
  --routing-threshold 0.45 `
  --low-score-threshold 2.0 `
  --low-average-threshold 2.5 `
  --run-name items100_norag_t045_vertical_riskaware
```

## Included Result Files

For each selected run:

- `manifest.json`: run configuration.
- `scores.csv`: flattened sample-level scores and explanations.
- `analysis_report.md`: aggregate summary.
- `winner_by_item.csv`: item-level preferred version by LUNA score.
- `largest_score_spread.csv`: examples with larger version differences.

The full `raw_results.jsonl` files are not included in this export because the flattened `scores.csv` already contains the main reproducible outputs needed for inspection.

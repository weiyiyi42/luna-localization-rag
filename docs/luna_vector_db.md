# LUNA Local Lore Vector Database

This directory documents the first local vector-database pipeline for the LUNA artefact described in the thesis draft.

## Thesis Alignment

- Evidence is fetched into a local snapshot before evaluation.
- Each retrieved chunk has a stable `evidence_id`.
- ChromaDB stores evidence locally under `data/vector_db/luna_lore_chroma`.
- The production thesis configuration is `BAAI/bge-m3` for cross-lingual retrieval.
- A deterministic `hash` backend is available only for offline smoke tests.

## Build Steps

Fetch a local wiki snapshot:

```powershell
python tools\scripts\fetch_silksong_wiki.py
```

Prepare the curated evidence dataset:

```powershell
python tools\scripts\prepare_luna_dataset.py
```

Build a local Chroma database from the curated dataset:

```powershell
python tools\scripts\build_lore_vector_db.py --use-curated
```

Query the smoke-test database:

```powershell
python tools\scripts\query_lore_vector_db.py "钟道和 Pharloom 的背景"
```

Build the thesis-grade database after the BGE-M3 model is available locally:

```powershell
python tools\scripts\build_lore_vector_db.py --use-curated --embedding-backend bge-m3 --model-name BAAI/bge-m3
```

## Outputs

- `data/raw/silksong_wiki/pages.jsonl`: controlled wiki page snapshot.
- `data/raw/silksong_wiki/manifest.json`: source, fetch time, search terms, and page count.
- `data/processed/luna_knowledge_base/evidence.jsonl`: deduplicated, source-tiered evidence rows.
- `data/processed/luna_knowledge_base/terminology.jsonl`: extracted terminology candidates.
- `data/processed/luna_knowledge_base/processing_report.md`: dataset quality and count report.
- `data/vector_db/luna_lore_chroma/`: Chroma persistent store.
- `data/vector_db/luna_lore_chroma/manifest.json`: build configuration and document counts.

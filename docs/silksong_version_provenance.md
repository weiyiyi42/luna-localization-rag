# Silksong Version Provenance

The current survey and LUNA evaluation data use three Simplified Chinese localization versions.

## Version Mapping

| Code | Survey Label | Local Data Directory | Meaning |
| --- | --- | --- | --- |
| V1 | Initial official version | `data/processed/silksong_versions/V1_existing_steam_content_revision_28324_manifest_unknown` | Earlier official Simplified Chinese localization |
| V2 | Public-beta official revision | `data/processed/silksong_versions/V2_public_beta_1.0.28954_official_revision_manifest_2538255789859855032` | Intermediate public-beta official revision, revision 28954 |
| V3 | Patch 4 Team Cart Fix version | `data/processed/silksong_versions/V3_patch4_team_cart_fix_revision_29315_manifest_3545882420322545098` | Patch 4 version integrating the Team Cart Fix translation |

The survey master file `data/survey/survey_items_master.csv` preserves the same mapping through `V1_label`, `V2_label`, and `V3_label`.

## Interpretation Note

V3 is the final Patch 4 / Team Cart Fix version in the local dataset and should be treated as the version most closely associated with the later official adoption and community-recognized revision. If an automated evaluator consistently scores V3 below V2, this should be interpreted as a prompt, retrieval, or evaluation-design issue to investigate rather than accepted uncritically as ground truth.

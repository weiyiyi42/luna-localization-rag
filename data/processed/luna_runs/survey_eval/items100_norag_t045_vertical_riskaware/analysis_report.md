# LUNA Survey Evaluation Analysis

Run directory: `data\processed\luna_runs\survey_eval\items100_norag_t045_vertical_riskaware`
Rows: 300
Items: 100

## Version Summary

| version_code | overall_score count | overall_score mean | overall_score median | overall_score std | overall_score min | overall_score max | meaning_score count | meaning_score mean | meaning_score median | meaning_score std | meaning_score min | meaning_score max | lore_score count | lore_score mean | lore_score median | lore_score std | lore_score min | lore_score max | style_score count | style_score mean | style_score median | style_score std | style_score min | style_score max | uncertainty count | uncertainty mean | uncertainty median | uncertainty std | uncertainty min | uncertainty max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V1 | 100 | 3.897 | 4.0 | 0.743 | 1.67 | 5.0 | 100 | 3.84 | 4.0 | 0.907 | 1.0 | 5.0 | 100 | 3.95 | 4.0 | 0.796 | 1.0 | 5.0 | 100 | 3.9 | 4.0 | 0.659 | 2.0 | 5.0 | 100 | 0.08 | 0.0 | 0.12 | 0.0 | 0.667 |
| V2 | 100 | 4.192 | 4.33 | 0.805 | 1.5 | 5.0 | 100 | 4.17 | 4.0 | 0.954 | 1.0 | 5.0 | 100 | 4.23 | 4.0 | 0.851 | 1.0 | 5.0 | 100 | 4.19 | 4.0 | 0.72 | 2.0 | 5.0 | 100 | 0.093 | 0.0 | 0.123 | 0.0 | 0.667 |
| V3 | 100 | 4.44 | 4.67 | 0.528 | 2.67 | 5.0 | 100 | 4.49 | 5.0 | 0.674 | 2.0 | 5.0 | 100 | 4.46 | 5.0 | 0.61 | 3.0 | 5.0 | 100 | 4.37 | 4.0 | 0.525 | 3.0 | 5.0 | 100 | 0.091 | 0.0 | 0.11 | 0.0 | 0.222 |

## Dimension Means

| version_code | meaning_score | lore_score | style_score |
| --- | --- | --- | --- |
| V1 | 3.84 | 3.95 | 3.9 |
| V2 | 4.17 | 4.23 | 4.19 |
| V3 | 4.49 | 4.46 | 4.37 |

## Strict Winners

{
  "strict_winner_counts": {
    "V3": 30,
    "V2": 20,
    "V1": 6
  },
  "tie_count": 44
}

## Pairwise Version Comparisons

| comparison | mean_diff | V3_wins | V1_wins | ties | V2_wins |
| --- | --- | --- | --- | --- | --- |
| V3-V1 | 0.543 | 57.0 | 11.0 | 32 | nan |
| V3-V2 | 0.248 | 37.0 | nan | 39 | 24.0 |
| V2-V1 | 0.295 | nan | 14.0 | 36 | 50.0 |

## Route Summary

| version_code | deep_audit | finalize |
| --- | --- | --- |
| V1 | 8 | 92 |
| V2 | 8 | 92 |
| V3 | 1 | 99 |

## Deep Audit Rate By Version

| version_code | samples | deep_audit_count | deep_audit_rate |
| --- | --- | --- | --- |
| V1 | 100 | 8 | 0.08 |
| V2 | 100 | 8 | 0.08 |
| V3 | 100 | 1 | 0.01 |

## Route Reason Summary

| version_code | fast_path | high_uncertainty | low_dimension_score |
| --- | --- | --- | --- |
| V1 | 92 | 1 | 7 |
| V2 | 92 | 1 | 7 |
| V3 | 99 | 0 | 1 |

## Source Type Summary

| source_type | version_code | count | mean | median |
| --- | --- | --- | --- | --- |
| Belltown | V1 | 12 | 3.889 | 4.0 |
| Belltown | V2 | 12 | 4.25 | 4.0 |
| Belltown | V3 | 12 | 4.556 | 4.67 |
| Bonebottom | V1 | 2 | 3.835 | 3.835 |
| Bonebottom | V2 | 2 | 4.665 | 4.665 |
| Bonebottom | V3 | 2 | 4.835 | 4.835 |
| Caravan | V1 | 2 | 3.665 | 3.665 |
| Caravan | V2 | 2 | 4.335 | 4.335 |
| Caravan | V3 | 2 | 4.665 | 4.665 |
| City | V1 | 4 | 3.918 | 4.0 |
| City | V2 | 4 | 4.585 | 4.67 |
| City | V3 | 4 | 4.918 | 5.0 |
| Coral | V1 | 4 | 3.832 | 4.0 |
| Coral | V2 | 4 | 4.332 | 4.165 |
| Coral | V3 | 4 | 4.5 | 4.5 |
| Crawl | V1 | 2 | 3.0 | 3.0 |
| Crawl | V2 | 2 | 5.0 | 5.0 |
| Crawl | V3 | 2 | 4.0 | 4.0 |
| Enclave | V1 | 1 | 3.0 | 3.0 |
| Enclave | V2 | 1 | 3.33 | 3.33 |
| Enclave | V3 | 1 | 3.0 | 3.0 |
| Forge | V1 | 1 | 4.0 | 4.0 |
| Forge | V2 | 1 | 4.67 | 4.67 |
| Forge | V3 | 1 | 4.0 | 4.0 |
| Inspect | V1 | 12 | 4.193 | 4.0 |
| Inspect | V2 | 12 | 4.361 | 4.165 |
| Inspect | V3 | 12 | 4.306 | 4.165 |
| Journal | V1 | 10 | 3.567 | 3.835 |
| Journal | V2 | 10 | 3.542 | 3.835 |
| Journal | V3 | 10 | 4.733 | 5.0 |
| Lore | V1 | 6 | 4.278 | 4.165 |
| Lore | V2 | 6 | 4.39 | 4.5 |
| Lore | V3 | 6 | 4.333 | 4.33 |
| Peak | V1 | 1 | 4.0 | 4.0 |
| Peak | V2 | 1 | 4.0 | 4.0 |
| Peak | V3 | 1 | 5.0 | 5.0 |
| Quests | V1 | 1 | 2.0 | 2.0 |
| Quests | V2 | 1 | 2.33 | 2.33 |
| Quests | V3 | 1 | 5.0 | 5.0 |
| Shellwood | V1 | 2 | 2.835 | 2.835 |
| Shellwood | V2 | 2 | 3.835 | 3.835 |
| Shellwood | V3 | 2 | 3.835 | 3.835 |
| Shop | V1 | 1 | 5.0 | 5.0 |
| Shop | V2 | 1 | 4.0 | 4.0 |
| Shop | V3 | 1 | 3.33 | 3.33 |
| Titles | V1 | 5 | 3.134 | 3.0 |
| Titles | V2 | 5 | 2.55 | 2.0 |
| Titles | V3 | 5 | 4.002 | 3.67 |
| Tools | V1 | 11 | 4.365 | 4.33 |
| Tools | V2 | 11 | 4.516 | 4.67 |
| Tools | V3 | 11 | 4.485 | 4.67 |
| UI | V1 | 9 | 4.334 | 4.33 |
| UI | V2 | 9 | 4.518 | 4.33 |
| UI | V3 | 9 | 4.556 | 4.67 |
| Wanderers | V1 | 12 | 3.861 | 4.0 |
| Wanderers | V2 | 12 | 4.445 | 4.335 |
| Wanderers | V3 | 12 | 4.389 | 4.335 |
| Wilds | V1 | 2 | 3.335 | 3.335 |
| Wilds | V2 | 2 | 4.0 | 4.0 |
| Wilds | V3 | 2 | 4.335 | 4.335 |

## Length Bucket Summary

| length_bucket | version_code | count | mean | median |
| --- | --- | --- | --- | --- |
| long | V1 | 15 | 3.8 | 4.0 |
| long | V2 | 15 | 4.467 | 4.67 |
| long | V3 | 15 | 4.489 | 4.67 |
| medium | V1 | 73 | 3.987 | 4.0 |
| medium | V2 | 73 | 4.311 | 4.33 |
| medium | V3 | 73 | 4.475 | 4.67 |
| micro | V1 | 7 | 3.524 | 4.0 |
| micro | V2 | 7 | 3.011 | 2.25 |
| micro | V3 | 7 | 3.906 | 3.67 |
| short | V1 | 5 | 3.398 | 4.0 |
| short | V2 | 5 | 3.282 | 4.0 |
| short | V3 | 5 | 4.532 | 4.33 |

## Largest Version Score Spread

| item_id | V1 | V2 | V3 | top_score | winners | range |
| --- | --- | --- | --- | --- | --- | --- |
| Titles_ARCHITECT_MAIN | 3.0 | 1.5 | 5.0 | 5.0 | V3 | 3.5 |
| Journal_NOTE_SONG_AUTOMATON_01 | 1.67 | 1.67 | 5.0 | 5.0 | V3 | 3.33 |
| Journal_NOTE_SLAB_FLY_LARGE | 2.0 | 1.75 | 5.0 | 5.0 | V3 | 3.25 |
| Quests_QUEST_FINEPINS_DESC_WALL | 2.0 | 2.33 | 5.0 | 5.0 | V3 | 3.0 |
| Journal_NOTE_SLAB_FLY_SMALL | 2.33 | 2.33 | 5.0 | 5.0 | V3 | 2.67 |
| Wilds_HUNTRESS_TALK_CITADEL | 1.67 | 4.0 | 4.0 | 4.0 | V2,V3 | 2.33 |
| Crawl_BLUE_SCIENTIST_ACCEPT_ZANGO | 3.0 | 5.0 | 4.0 | 5.0 | V2 | 2.0 |
| Crawl_BLUE_SCIENTIST_ACCEPT | 3.0 | 5.0 | 4.0 | 5.0 | V2 | 2.0 |
| Titles_FIRST_WEAVER_MAIN | 4.0 | 2.25 | 3.67 | 4.0 | V1 | 1.75 |
| Shellwood_WOOD_WITCH_FLOWER_QUEST_REOFFER | 2.0 | 3.67 | 3.67 | 3.67 | V2,V3 | 1.67 |
| Titles_SILK_MAIN | 2.0 | 2.0 | 3.67 | 3.67 | V3 | 1.67 |
| Shop_THUNTER_ITEM_PEAKLANDS | 5.0 | 4.0 | 3.33 | 5.0 | V1 | 1.67 |
| Coral_PINSTRESS_INTERIOR_STAND_MEET | 3.33 | 4.0 | 4.67 | 4.67 | V3 | 1.3399999999999999 |
| Inspect_SHAMAN_STONE_CHAPEL | 3.33 | 4.0 | 4.67 | 4.67 | V3 | 1.3399999999999999 |
| Bonebottom_MOSSCREEP_TRADE_INTRO | 3.67 | 5.0 | 5.0 | 5.0 | V2,V3 | 1.33 |

## Notes

- `deep_audit` count indicates how often adaptive routing selected the expensive path.
- A high number of ties suggests the current scoring prompt/model may be conservative or coarse-grained.
- The current run uses the embedding backend recorded in the run manifest; interpret retrieval quality accordingly.

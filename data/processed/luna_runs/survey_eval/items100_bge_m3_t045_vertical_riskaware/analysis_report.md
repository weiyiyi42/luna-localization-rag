# LUNA Survey Evaluation Analysis

Run directory: `data\processed\luna_runs\survey_eval\items100_bge_m3_t045_vertical_riskaware`
Rows: 300
Items: 100

## Version Summary

| version_code | overall_score count | overall_score mean | overall_score median | overall_score std | overall_score min | overall_score max | meaning_score count | meaning_score mean | meaning_score median | meaning_score std | meaning_score min | meaning_score max | lore_score count | lore_score mean | lore_score median | lore_score std | lore_score min | lore_score max | style_score count | style_score mean | style_score median | style_score std | style_score min | style_score max | uncertainty count | uncertainty mean | uncertainty median | uncertainty std | uncertainty min | uncertainty max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V1 | 100 | 3.836 | 4.0 | 0.746 | 1.33 | 5.0 | 100 | 3.84 | 4.0 | 0.961 | 1.0 | 5.0 | 100 | 3.76 | 4.0 | 0.878 | 1.0 | 5.0 | 100 | 3.91 | 4.0 | 0.588 | 2.0 | 5.0 | 100 | 0.127 | 0.0 | 0.226 | 0.0 | 1.556 |
| V2 | 100 | 4.157 | 4.165 | 0.782 | 1.67 | 5.0 | 100 | 4.25 | 4.0 | 0.903 | 1.0 | 5.0 | 100 | 4.12 | 4.0 | 0.891 | 1.0 | 5.0 | 100 | 4.1 | 4.0 | 0.718 | 2.0 | 5.0 | 100 | 0.1 | 0.0 | 0.182 | 0.0 | 1.556 |
| V3 | 100 | 4.294 | 4.33 | 0.477 | 2.33 | 5.0 | 100 | 4.45 | 5.0 | 0.672 | 1.0 | 5.0 | 100 | 4.21 | 4.0 | 0.64 | 2.0 | 5.0 | 100 | 4.22 | 4.0 | 0.44 | 3.0 | 5.0 | 100 | 0.136 | 0.222 | 0.181 | 0.0 | 1.556 |

## Dimension Means

| version_code | meaning_score | lore_score | style_score |
| --- | --- | --- | --- |
| V1 | 3.84 | 3.76 | 3.91 |
| V2 | 4.25 | 4.12 | 4.1 |
| V3 | 4.45 | 4.21 | 4.22 |

## Strict Winners

{
  "strict_winner_counts": {
    "V2": 28,
    "V3": 25,
    "V1": 7
  },
  "tie_count": 40
}

## Pairwise Version Comparisons

| comparison | mean_diff | V3_wins | V1_wins | ties | V2_wins |
| --- | --- | --- | --- | --- | --- |
| V3-V1 | 0.457 | 54.0 | 11.0 | 35 | nan |
| V3-V2 | 0.137 | 29.0 | nan | 39 | 32.0 |
| V2-V1 | 0.32 | nan | 11.0 | 36 | 53.0 |

## Route Summary

| version_code | deep_audit | finalize |
| --- | --- | --- |
| V1 | 13 | 87 |
| V2 | 8 | 92 |
| V3 | 1 | 99 |

## Deep Audit Rate By Version

| version_code | samples | deep_audit_count | deep_audit_rate |
| --- | --- | --- | --- |
| V1 | 100 | 13 | 0.13 |
| V2 | 100 | 8 | 0.08 |
| V3 | 100 | 1 | 0.01 |

## Route Reason Summary

| version_code | fast_path | high_uncertainty | low_dimension_score |
| --- | --- | --- | --- |
| V1 | 87 | 5 | 8 |
| V2 | 92 | 1 | 7 |
| V3 | 99 | 1 | 0 |

## Source Type Summary

| source_type | version_code | count | mean | median |
| --- | --- | --- | --- | --- |
| Belltown | V1 | 12 | 3.833 | 4.0 |
| Belltown | V2 | 12 | 4.249 | 4.0 |
| Belltown | V3 | 12 | 4.251 | 4.33 |
| Bonebottom | V1 | 2 | 4.0 | 4.0 |
| Bonebottom | V2 | 2 | 4.67 | 4.67 |
| Bonebottom | V3 | 2 | 4.5 | 4.5 |
| Caravan | V1 | 2 | 3.5 | 3.5 |
| Caravan | V2 | 2 | 4.335 | 4.335 |
| Caravan | V3 | 2 | 4.5 | 4.5 |
| City | V1 | 4 | 3.832 | 4.0 |
| City | V2 | 4 | 4.5 | 4.5 |
| City | V3 | 4 | 4.668 | 4.67 |
| Coral | V1 | 4 | 3.668 | 4.0 |
| Coral | V2 | 4 | 4.332 | 4.165 |
| Coral | V3 | 4 | 4.332 | 4.33 |
| Crawl | V1 | 2 | 3.335 | 3.335 |
| Crawl | V2 | 2 | 4.835 | 4.835 |
| Crawl | V3 | 2 | 4.0 | 4.0 |
| Enclave | V1 | 1 | 3.0 | 3.0 |
| Enclave | V2 | 1 | 3.33 | 3.33 |
| Enclave | V3 | 1 | 3.0 | 3.0 |
| Forge | V1 | 1 | 4.0 | 4.0 |
| Forge | V2 | 1 | 4.33 | 4.33 |
| Forge | V3 | 1 | 3.67 | 3.67 |
| Inspect | V1 | 12 | 4.111 | 4.0 |
| Inspect | V2 | 12 | 4.278 | 4.0 |
| Inspect | V3 | 12 | 4.138 | 4.0 |
| Journal | V1 | 10 | 3.401 | 3.67 |
| Journal | V2 | 10 | 3.434 | 3.67 |
| Journal | V3 | 10 | 4.568 | 4.67 |
| Lore | V1 | 6 | 4.39 | 4.5 |
| Lore | V2 | 6 | 4.445 | 4.5 |
| Lore | V3 | 6 | 4.335 | 4.335 |
| Peak | V1 | 1 | 4.0 | 4.0 |
| Peak | V2 | 1 | 4.0 | 4.0 |
| Peak | V3 | 1 | 4.67 | 4.67 |
| Quests | V1 | 1 | 2.0 | 2.0 |
| Quests | V2 | 1 | 2.0 | 2.0 |
| Quests | V3 | 1 | 4.67 | 4.67 |
| Shellwood | V1 | 2 | 3.165 | 3.165 |
| Shellwood | V2 | 2 | 4.0 | 4.0 |
| Shellwood | V3 | 2 | 4.0 | 4.0 |
| Shop | V1 | 1 | 5.0 | 5.0 |
| Shop | V2 | 1 | 4.0 | 4.0 |
| Shop | V3 | 1 | 3.33 | 3.33 |
| Titles | V1 | 5 | 3.064 | 3.33 |
| Titles | V2 | 5 | 2.534 | 2.0 |
| Titles | V3 | 5 | 4.066 | 4.0 |
| Tools | V1 | 11 | 4.151 | 4.0 |
| Tools | V2 | 11 | 4.332 | 4.33 |
| Tools | V3 | 11 | 4.302 | 4.33 |
| UI | V1 | 9 | 4.334 | 4.33 |
| UI | V2 | 9 | 4.631 | 4.67 |
| UI | V3 | 9 | 4.519 | 4.67 |
| Wanderers | V1 | 12 | 3.804 | 4.0 |
| Wanderers | V2 | 12 | 4.472 | 4.335 |
| Wanderers | V3 | 12 | 4.25 | 4.165 |
| Wilds | V1 | 2 | 3.165 | 3.165 |
| Wilds | V2 | 2 | 4.0 | 4.0 |
| Wilds | V3 | 2 | 4.165 | 4.165 |

## Length Bucket Summary

| length_bucket | version_code | count | mean | median |
| --- | --- | --- | --- | --- |
| long | V1 | 15 | 3.799 | 4.0 |
| long | V2 | 15 | 4.467 | 4.67 |
| long | V3 | 15 | 4.289 | 4.33 |
| medium | V1 | 73 | 3.904 | 4.0 |
| medium | V2 | 73 | 4.251 | 4.33 |
| medium | V3 | 73 | 4.329 | 4.33 |
| micro | V1 | 7 | 3.57 | 4.0 |
| micro | V2 | 7 | 3.049 | 2.33 |
| micro | V3 | 7 | 3.951 | 4.0 |
| short | V1 | 5 | 3.334 | 3.67 |
| short | V2 | 5 | 3.4 | 4.0 |
| short | V3 | 5 | 4.266 | 4.33 |

## Largest Version Score Spread

| item_id | V1 | V2 | V3 | top_score | winners | range |
| --- | --- | --- | --- | --- | --- | --- |
| Titles_ARCHITECT_MAIN | 3.33 | 1.67 | 5.0 | 5.0 | V3 | 3.33 |
| Journal_NOTE_SLAB_FLY_LARGE | 2.0 | 2.0 | 5.0 | 5.0 | V3 | 3.0 |
| Journal_NOTE_SONG_AUTOMATON_01 | 2.0 | 2.0 | 5.0 | 5.0 | V3 | 3.0 |
| Quests_QUEST_FINEPINS_DESC_WALL | 2.0 | 2.0 | 4.67 | 4.67 | V3 | 2.67 |
| Wilds_HUNTRESS_TALK_CITADEL | 1.33 | 4.0 | 4.0 | 4.0 | V2,V3 | 2.67 |
| Titles_SILK_MAIN | 1.33 | 1.67 | 4.0 | 4.0 | V3 | 2.67 |
| Journal_NOTE_SLAB_FLY_SMALL | 2.0 | 2.0 | 4.33 | 4.33 | V3 | 2.33 |
| Titles_FIRST_WEAVER_MAIN | 4.0 | 2.0 | 4.0 | 4.0 | V1,V3 | 2.0 |
| Crawl_BLUE_SCIENTIST_ACCEPT | 3.0 | 5.0 | 4.0 | 5.0 | V2 | 2.0 |
| Wanderers_SHERMA_CORAL_NOBENCH | 2.33 | 4.0 | 4.0 | 4.0 | V2,V3 | 1.67 |
| Shop_THUNTER_ITEM_PEAKLANDS | 5.0 | 4.0 | 3.33 | 5.0 | V1 | 1.67 |
| Shellwood_WOOD_WITCH_FLOWER_QUEST_REOFFER | 2.33 | 3.67 | 4.0 | 4.0 | V3 | 1.67 |
| Coral_PINSTRESS_INTERIOR_STAND_MEET | 2.67 | 4.0 | 4.33 | 4.33 | V3 | 1.6600000000000001 |
| Journal_NOTE_SWAMP_DRIFTER | 3.33 | 3.33 | 4.67 | 4.67 | V3 | 1.3399999999999999 |
| City_GOURMAND_SERVANT_MOSSSTEW | 3.33 | 4.33 | 4.67 | 4.67 | V3 | 1.3399999999999999 |

## Notes

- `deep_audit` count indicates how often adaptive routing selected the expensive path.
- A high number of ties suggests the current scoring prompt/model may be conservative or coarse-grained.
- The current run uses the embedding backend recorded in the run manifest; interpret retrieval quality accordingly.

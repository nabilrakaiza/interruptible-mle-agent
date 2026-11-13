# Error taxonomy

63 runs, 5381 nodes.

## Node categories by condition

| condition | generation_error | leakage | pruned | runtime_error | timeout | working |
|---|---|---|---|---|---|---|
| A1-off | 4 (0.5%) | 0 (0.0%) | 0 (0.0%) | 19 (2.6%) | 11 (1.5%) | 700 (95.4%) |
| A4-off | 6 (0.7%) | 1 (0.1%) | 0 (0.0%) | 14 (1.7%) | 11 (1.4%) | 769 (96.0%) |
| C1 | 8 (0.7%) | 2 (0.2%) | 0 (0.0%) | 23 (2.0%) | 19 (1.7%) | 1098 (95.5%) |
| C4 | 11 (0.8%) | 0 (0.0%) | 23 (1.7%) | 32 (2.4%) | 20 (1.5%) | 1261 (93.6%) |
| C5 | 9 (0.7%) | 0 (0.0%) | 0 (0.0%) | 9 (0.7%) | 18 (1.3%) | 1313 (97.3%) |

## Runtime errors by exception

| subtype | nodes |
|---|---|
| type_error | 33 |
| other | 22 |
| value_error | 10 |
| attribute_error | 6 |
| name_error | 6 |
| import_error | 5 |
| missing_key_or_column | 4 |
| shape_mismatch | 4 |
| index_error | 3 |
| syntax_error | 3 |
| out_of_memory | 1 |

Example of each:

| subtype | run | node | exception |
|---|---|---|---|
| type_error | A1-off_detecting-insults-in-social-commentary_seed0 | n4 | TypeError: only integer scalar arrays can be converted to a scalar index |
| other | A1-off_detecting-insults-in-social-commentary_seed1 | n2 |  |
| attribute_error | A1-off_detecting-insults-in-social-commentary_seed1 | n39 | AttributeError: 'BM25Transformer' object has no attribute 'fit_transform'. Did you mean: 'transform'? |
| import_error | A1-off_detecting-insults-in-social-commentary_seed1 | n79 | ImportError: cannot import name 'BM25Transformer' from 'sklearn.feature_extraction.text' (/tmp/venv/lib/python3.13/site-packages/sklearn/feature_extraction/text.py) |
| name_error | A1-off_detecting-insults-in-social-commentary_seed2 | n51 | NameError: name 'Pipeline' is not defined |
| value_error | A1-off_random-acts-of-pizza_seed1 | n1 | ValueError: Input contains NaN. |
| missing_key_or_column | A1-off_spooky-author-identification_seed2 | n14 | KeyError: 0 |
| shape_mismatch | A4-off_detecting-insults-in-social-commentary_seed0 | n45 | ValueError: axis 0 index 20793 exceeds matrix dimension 6414 |
| index_error | A4-off_random-acts-of-pizza_seed1 | n52 | IndexError: boolean index did not match indexed array along axis 0; size of axis is 1 but size of corresponding boolean axis is 403 |
| syntax_error | C1_detecting-insults-in-social-commentary_seed0 | n4 | SyntaxError: (unicode error) 'unicodeescape' codec can't decode bytes in position 31-32: truncated \xXX escape |
| out_of_memory | C4_spooky-author-identification_seed2 | n57 |  |

## Categories by operator

| operator | generation_error | leakage | pruned | runtime_error | timeout | working |
|---|---|---|---|---|---|---|
| debug | 6 | 0 | 0 | 11 | 1 | 99 |
| draft | 20 | 0 | 0 | 17 | 0 | 279 |
| improve | 12 | 3 | 23 | 69 | 78 | 4763 |

## Labels on working nodes

`no_gain` and `no_change` are out of working improve nodes; the others out of all working nodes.

| label | nodes | of |
|---|---|---|
| no_change | 158 | 4763 |
| no_gain | 3008 | 4763 |
| validation_overfitting | 111 | 5141 |

## Runs

| run | condition | task | seed | nodes | working_rate | longest_no_new_best | nodes_after_final_best | failures_debugged | debug_chains_fixed | mean_attempts_to_fix | final_node | selection_regret | regret_basis | stop_reason | done |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A1-off_detecting-insults-in-social-commentary_seed0 | A1-off | detecting-insults-in-social-commentary | 0 | 86 | 0.965 | 29 | 5 | 2 | 2 | 1.0 | n80 | 0.0046 | test | budget | True |
| A1-off_detecting-insults-in-social-commentary_seed1 | A1-off | detecting-insults-in-social-commentary | 1 | 118 | 0.924 | 56 | 2 | 6 | 5 | 1.2 | n115 | 0.0052 | test | budget | True |
| A1-off_detecting-insults-in-social-commentary_seed2 | A1-off | detecting-insults-in-social-commentary | 2 | 74 | 0.946 | 17 | 8 | 3 | 3 | 1.0 | n65 | 0.0016 | test | budget | True |
| A1-off_random-acts-of-pizza_seed0 | A1-off | random-acts-of-pizza | 0 | 28 | 0.929 | 8 | 8 | 0 | 0 |  | n19 | 0.0074 | test | budget | True |
| A1-off_random-acts-of-pizza_seed1 | A1-off | random-acts-of-pizza | 1 | 113 | 0.965 | 24 | 2 | 2 | 2 | 1.5 | n110 | 0.0034 | test | budget | True |
| A1-off_random-acts-of-pizza_seed2 | A1-off | random-acts-of-pizza | 2 | 84 | 0.952 | 22 | 22 | 2 | 2 | 1.0 | n61 | 0.0086 | test | budget | True |
| A1-off_spooky-author-identification_seed0 | A1-off | spooky-author-identification | 0 | 73 | 0.959 | 3 | 2 | 2 | 2 | 1.0 | n70 | 0.0211 | test | budget | True |
| A1-off_spooky-author-identification_seed1 | A1-off | spooky-author-identification | 1 | 80 | 0.963 | 5 | 1 | 1 | 0 |  | n78 | 0.0938 | test | budget | True |
| A1-off_spooky-author-identification_seed2 | A1-off | spooky-author-identification | 2 | 78 | 0.974 | 24 | 2 | 1 | 1 | 1.0 | n75 | 0.0 | test | budget | True |
| A4-off_detecting-insults-in-social-commentary_seed0 | A4-off | detecting-insults-in-social-commentary | 0 | 51 | 0.941 | 10 | 10 | 1 | 1 | 2.0 | n40 | 0.0012 | test | budget | True |
| A4-off_detecting-insults-in-social-commentary_seed1 | A4-off | detecting-insults-in-social-commentary | 1 | 200 | 0.99 | 145 | 0 | 1 | 1 | 1.0 | n199 | 0.0 | test | max_nodes | True |
| A4-off_detecting-insults-in-social-commentary_seed2 | A4-off | detecting-insults-in-social-commentary | 2 | 129 | 0.977 | 53 | 53 | 0 | 0 |  | n75 | 0.0022 | test | budget | True |
| A4-off_random-acts-of-pizza_seed0 | A4-off | random-acts-of-pizza | 0 | 64 | 0.938 | 42 | 42 | 2 | 2 | 1.0 | n21 | 0.0142 | test | budget | True |
| A4-off_random-acts-of-pizza_seed1 | A4-off | random-acts-of-pizza | 1 | 109 | 0.945 | 30 | 29 | 1 | 1 | 3.0 | n79 | 0.0 | test | budget | True |
| A4-off_random-acts-of-pizza_seed2 | A4-off | random-acts-of-pizza | 2 | 67 | 0.925 | 27 | 3 | 4 | 4 | 1.0 | n63 | 0.0071 | test | budget | True |
| A4-off_spooky-author-identification_seed0 | A4-off | spooky-author-identification | 0 | 56 | 0.911 | 8 | 1 | 3 | 3 | 1.33 | n54 | 0.0 | test | budget | True |
| A4-off_spooky-author-identification_seed1 | A4-off | spooky-author-identification | 1 | 82 | 0.976 | 16 | 3 | 1 | 1 | 1.0 | n78 | 0.0016 | test | budget | True |
| A4-off_spooky-author-identification_seed2 | A4-off | spooky-author-identification | 2 | 43 | 0.953 | 12 | 1 | 1 | 1 | 1.0 | n41 | 0.0 | test | budget | True |
| C1_detecting-insults-in-social-commentary_seed0 | C1 | detecting-insults-in-social-commentary | 0 | 67 | 0.97 | 22 | 22 | 1 | 1 | 1.0 | n44 | 0.0048 | test | budget | True |
| C1_detecting-insults-in-social-commentary_seed1 | C1 | detecting-insults-in-social-commentary | 1 | 75 | 0.987 | 19 | 19 | 1 | 1 | 1.0 | n55 | 0.0018 | test | budget | True |
| C1_detecting-insults-in-social-commentary_seed2 | C1 | detecting-insults-in-social-commentary | 2 | 81 | 0.963 | 22 | 22 | 2 | 2 | 1.0 | n58 | 0.0026 | test | budget | True |
| C1_detecting-insults-in-social-commentary_seed3 | C1 | detecting-insults-in-social-commentary | 3 | 63 | 0.952 | 11 | 1 | 0 | 0 |  | n61 | 0.0166 | test | budget | True |
| C1_detecting-insults-in-social-commentary_seed4 | C1 | detecting-insults-in-social-commentary | 4 | 104 | 0.99 | 29 | 13 | 0 | 0 |  | n90 | 0.0038 | test | budget | True |
| C1_random-acts-of-pizza_seed0 | C1 | random-acts-of-pizza | 0 | 42 | 0.857 | 31 | 1 | 1 | 1 | 2.0 | n40 | 0.0085 | test | budget | True |
| C1_random-acts-of-pizza_seed1 | C1 | random-acts-of-pizza | 1 | 134 | 0.978 | 47 | 21 | 2 | 2 | 1.0 | n112 | 0.0167 | test | budget | True |
| C1_random-acts-of-pizza_seed2 | C1 | random-acts-of-pizza | 2 | 147 | 0.952 | 44 | 18 | 6 | 6 | 1.0 | n128 | 0.0 | test | budget | True |
| C1_random-acts-of-pizza_seed3 | C1 | random-acts-of-pizza | 3 | 100 | 0.97 | 17 | 1 | 2 | 2 | 1.0 | n98 | 0.0021 | test | budget | True |
| C1_random-acts-of-pizza_seed4 | C1 | random-acts-of-pizza | 4 | 80 | 0.925 | 50 | 50 | 2 | 1 | 1.0 | n29 | 0.0021 | test | budget | True |
| C1_spooky-author-identification_seed0 | C1 | spooky-author-identification | 0 | 51 | 0.902 | 12 | 5 | 3 | 3 | 1.33 | n45 | 0.0012 | test | budget | True |
| C1_spooky-author-identification_seed1 | C1 | spooky-author-identification | 1 | 67 | 0.94 | 25 | 12 | 3 | 3 | 1.0 | n54 | 0.0019 | test | budget | True |
| C1_spooky-author-identification_seed2 | C1 | spooky-author-identification | 2 | 59 | 0.932 | 12 | 12 | 3 | 3 | 1.0 | n46 | 0.0 | test | budget | True |
| C1_spooky-author-identification_seed3 | C1 | spooky-author-identification | 3 | 32 | 0.969 | 10 | 1 | 0 | 0 |  | n30 | 0.0 | test | budget | True |
| C1_spooky-author-identification_seed4 | C1 | spooky-author-identification | 4 | 48 | 0.938 | 22 | 2 | 1 | 1 | 1.0 | n45 | 0.0 | test | budget | True |
| C4_detecting-insults-in-social-commentary_seed0 | C4 | detecting-insults-in-social-commentary | 0 | 82 | 0.976 | 40 | 20 | 1 | 1 | 1.0 | n61 | 0.0091 | test | budget | True |
| C4_detecting-insults-in-social-commentary_seed1 | C4 | detecting-insults-in-social-commentary | 1 | 150 | 0.96 | 42 | 11 | 4 | 4 | 1.0 | n138 | 0.0039 | test | budget | True |
| C4_detecting-insults-in-social-commentary_seed2 | C4 | detecting-insults-in-social-commentary | 2 | 117 | 0.991 | 25 | 1 | 0 | 0 |  | n115 | 0.0017 | test | budget | True |
| C4_detecting-insults-in-social-commentary_seed3 | C4 | detecting-insults-in-social-commentary | 3 | 108 | 0.972 | 38 | 23 | 1 | 1 | 2.0 | n84 | 0.0004 | test | budget | True |
| C4_detecting-insults-in-social-commentary_seed4 | C4 | detecting-insults-in-social-commentary | 4 | 80 | 0.988 | 39 | 1 | 0 | 0 |  | n78 | 0.0052 | test | budget | True |
| C4_random-acts-of-pizza_seed0 | C4 | random-acts-of-pizza | 0 | 53 | 0.774 | 42 | 42 | 3 | 2 | 1.0 | n10 | 0.0134 | test | budget | True |
| C4_random-acts-of-pizza_seed1 | C4 | random-acts-of-pizza | 1 | 79 | 0.861 | 15 | 15 | 4 | 4 | 1.25 | n63 | 0.0063 | test | budget | True |
| C4_random-acts-of-pizza_seed2 | C4 | random-acts-of-pizza | 2 | 116 | 0.966 | 34 | 6 | 3 | 3 | 1.0 | n109 | 0.0348 | test | budget | True |
| C4_random-acts-of-pizza_seed3 | C4 | random-acts-of-pizza | 3 | 83 | 0.928 | 14 | 2 | 3 | 2 | 1.0 | n80 | 0.0102 | test | budget | True |
| C4_random-acts-of-pizza_seed4 | C4 | random-acts-of-pizza | 4 | 111 | 0.766 | 95 | 95 | 6 | 6 | 1.0 | n15 | 0.0168 | test | budget | True |
| C4_spooky-author-identification_seed0 | C4 | spooky-author-identification | 0 | 46 | 0.957 | 19 | 19 | 1 | 1 | 1.0 | n26 | 0.0024 | test | budget | True |
| C4_spooky-author-identification_seed1 | C4 | spooky-author-identification | 1 | 49 | 0.939 | 6 | 2 | 2 | 2 | 1.0 | n46 | 0.0 | test | budget | True |
| C4_spooky-author-identification_seed2 | C4 | spooky-author-identification | 2 | 59 | 0.915 | 8 | 2 | 4 | 3 | 1.0 | n56 | 0.0089 | test | budget | True |
| C4_spooky-author-identification_seed3 | C4 | spooky-author-identification | 3 | 55 | 0.964 | 7 | 1 | 1 | 1 | 1.0 | n53 | 0.0 | test | budget | True |
| C4_spooky-author-identification_seed4 | C4 | spooky-author-identification | 4 | 159 | 0.987 | 40 | 8 | 1 | 1 | 1.0 | n150 | 0.0 | test | budget | True |
| C5_detecting-insults-in-social-commentary_seed0 | C5 | detecting-insults-in-social-commentary | 0 | 74 | 0.986 | 46 | 46 | 0 | 0 |  | n27 | 0.0079 | test | budget | True |
| C5_detecting-insults-in-social-commentary_seed1 | C5 | detecting-insults-in-social-commentary | 1 | 138 | 0.971 | 49 | 49 | 3 | 3 | 1.0 | n88 | 0.0024 | test | budget | True |
| C5_detecting-insults-in-social-commentary_seed2 | C5 | detecting-insults-in-social-commentary | 2 | 82 | 0.988 | 29 | 7 | 0 | 0 |  | n74 | 0.0 | test | budget | True |
| C5_detecting-insults-in-social-commentary_seed3 | C5 | detecting-insults-in-social-commentary | 3 | 35 | 0.971 | 9 | 1 | 0 | 0 |  | n33 | 0.0048 | test | budget | True |
| C5_detecting-insults-in-social-commentary_seed4 | C5 | detecting-insults-in-social-commentary | 4 | 112 | 0.982 | 32 | 5 | 1 | 1 | 1.0 | n106 | 0.0021 | test | budget | True |
| C5_random-acts-of-pizza_seed0 | C5 | random-acts-of-pizza | 0 | 47 | 0.936 | 29 | 5 | 0 | 0 |  | n41 | 0.0058 | test | budget | True |
| C5_random-acts-of-pizza_seed1 | C5 | random-acts-of-pizza | 1 | 116 | 0.966 | 64 | 2 | 0 | 0 |  | n113 | 0.0197 | test | budget | True |
| C5_random-acts-of-pizza_seed2 | C5 | random-acts-of-pizza | 2 | 119 | 0.983 | 37 | 9 | 1 | 1 | 1.0 | n109 | 0.0168 | test | budget | True |
| C5_random-acts-of-pizza_seed3 | C5 | random-acts-of-pizza | 3 | 109 | 0.972 | 34 | 34 | 1 | 1 | 1.0 | n74 | 0.0028 | test | budget | True |
| C5_random-acts-of-pizza_seed4 | C5 | random-acts-of-pizza | 4 | 95 | 0.958 | 70 | 70 | 1 | 1 | 1.0 | n24 | 0.0121 | test | budget | True |
| C5_spooky-author-identification_seed0 | C5 | spooky-author-identification | 0 | 116 | 0.983 | 23 | 11 | 1 | 1 | 1.0 | n104 | 0.0001 | test | budget | True |
| C5_spooky-author-identification_seed1 | C5 | spooky-author-identification | 1 | 68 | 0.956 | 12 | 1 | 2 | 2 | 1.0 | n66 | 0.0006 | test | budget | True |
| C5_spooky-author-identification_seed2 | C5 | spooky-author-identification | 2 | 58 | 0.948 | 9 | 2 | 1 | 0 |  | n55 | 0.0 | test | budget | True |
| C5_spooky-author-identification_seed3 | C5 | spooky-author-identification | 3 | 131 | 0.985 | 18 | 2 | 1 | 1 | 1.0 | n128 | 0.0 | test | budget | True |
| C5_spooky-author-identification_seed4 | C5 | spooky-author-identification | 4 | 49 | 0.98 | 4 | 2 | 0 | 0 |  | n46 | 0.0 | test | budget | True |

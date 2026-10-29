# Cost

Reference price: $0.044/M input, $0.133/M output tokens.

## Runs

| run | condition | task | seed | model | done | hours | nodes | calls | input_tokens | output_tokens | tokens_per_node | cost_usd | reference_cost_usd | reference_cost_per_hour |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A1-off_nomad2018-predict-transparent-conductors_seed0 | A1-off | nomad2018-predict-transparent-conductors | 0 | deepseek/deepseek-v4-flash-0731 | True | 2.473 | 34 | 42 | 238234 | 531629 | 22643 | 0.1663 | 0.0812 | 0.0328 |
| A1-off_nomad2018-predict-transparent-conductors_seed1 | A1-off | nomad2018-predict-transparent-conductors | 1 | deepseek/deepseek-v4-flash-0731 | True | 2.006 | 67 | 75 | 663281 | 844352 | 22502 | 0.1282 | 0.1415 | 0.0705 |
| A4-off_nomad2018-predict-transparent-conductors_seed0 | A4-off | nomad2018-predict-transparent-conductors | 0 | deepseek/deepseek-v4-flash-0731 | True | 2.0 | 79 | 80 | 701586 | 1010693 | 21674 | 0.1485 | 0.1653 | 0.0826 |
| A4-off_nomad2018-predict-transparent-conductors_seed1 | A4-off | nomad2018-predict-transparent-conductors | 1 | deepseek/deepseek-v4-flash-0731 | True | 2.0 | 98 | 99 | 697688 | 948393 | 16797 | 0.1403 | 0.1568 | 0.0784 |
| C1_nomad2018-predict-transparent-conductors_seed0 | C1 | nomad2018-predict-transparent-conductors | 0 | deepseek/deepseek-v4-flash-0731 | True | 2.0 | 54 | 61 | 398550 | 613776 | 18747 | 0.1889 | 0.0992 | 0.0496 |
| C1_nomad2018-predict-transparent-conductors_seed1 | C1 | nomad2018-predict-transparent-conductors | 1 | deepseek/deepseek-v4-flash-0731 | True | 2.757 | 17 | 23 | 120162 | 454893 | 33827 | 0.1383 | 0.0658 | 0.0239 |
| C1_nomad2018-predict-transparent-conductors_seed2 | C1 | nomad2018-predict-transparent-conductors | 2 | deepseek/deepseek-v4-flash-0731 | True | 3.722 | 14 | 17 | 92775 | 292760 | 27538 | 0.089 | 0.043 | 0.0116 |
| C4_nomad2018-predict-transparent-conductors_seed0 | C4 | nomad2018-predict-transparent-conductors | 0 | deepseek/deepseek-v4-flash-0731 | True | 2.01 | 82 | 91 | 683749 | 925674 | 19627 | 0.1386 | 0.1532 | 0.0762 |
| C4_nomad2018-predict-transparent-conductors_seed1 | C4 | nomad2018-predict-transparent-conductors | 1 | deepseek/deepseek-v4-flash-0731 | True | 2.018 | 72 | 80 | 563937 | 768343 | 18504 | 0.1145 | 0.127 | 0.0629 |
| C4_nomad2018-predict-transparent-conductors_seed2 | C4 | nomad2018-predict-transparent-conductors | 2 | deepseek/deepseek-v4-flash-0731 | True | 2.01 | 63 | 70 | 537986 | 689694 | 19487 | 0.1034 | 0.1154 | 0.0574 |
| C5_nomad2018-predict-transparent-conductors_seed0 | C5 | nomad2018-predict-transparent-conductors | 0 | deepseek/deepseek-v4-flash-0731 | True | 2.0 | 56 | 63 | 483972 | 797736 | 22888 | 0.1176 | 0.1274 | 0.0637 |
| C5_nomad2018-predict-transparent-conductors_seed1 | C5 | nomad2018-predict-transparent-conductors | 1 | deepseek/deepseek-v4-flash-0731 | True | 2.019 | 59 | 67 | 420027 | 719099 | 19307 | 0.2395 | 0.1141 | 0.0565 |
| C5_nomad2018-predict-transparent-conductors_seed2 | C5 | nomad2018-predict-transparent-conductors | 2 | deepseek/deepseek-v4-flash-0731 | True | 2.031 | 56 | 67 | 495976 | 780870 | 22801 | 0.251 | 0.1257 | 0.0619 |


## By condition

| condition | runs | mean_hours | mean_nodes | tokens_per_node | mean_cost_usd | mean_reference_cost_usd | total_cost_usd |
|---|---|---|---|---|---|---|---|
| A1-off | 2 | 2.2395 | 50.5 | 22572.5 | 0.1472 | 0.1114 | 0.2945 |
| A4-off | 2 | 2.0 | 88.5 | 19235.5 | 0.1444 | 0.161 | 0.2888 |
| C1 | 3 | 2.8263 | 28.3333 | 26704.0 | 0.1387 | 0.0693 | 0.4162 |
| C4 | 3 | 2.0127 | 72.3333 | 19206.0 | 0.1188 | 0.1319 | 0.3565 |
| C5 | 3 | 2.0167 | 57.0 | 21665.3333 | 0.2027 | 0.1224 | 0.6081 |

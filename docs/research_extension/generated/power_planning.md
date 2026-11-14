# Planning simulation for the CFP confirmation (generated; do not edit)

Source: `results/extension/planning/power_planning.json` (D-140). **Planning only, on pilot data; not a result.**
400 simulated sets per cell, 1000 inner resamples, seed 20261111. Shares count sets where the bootstrap p is below the threshold *and* the estimate has the predicted sign.

## Share of simulated sets in which each hypothesis would be supported

| Scenario | Bugs with a PF test | Hypothesis | p < 0.05 | p < 0.0125 (strictest Holm step) | Median 95% CI half-width |
|---|---|---|---|---|---|
| pilot_effect | 30 | C1 | 0.998 | 0.980 | 0.204 |
| pilot_effect | 30 | C2 | 0.993 | 0.963 | 0.098 |
| pilot_effect | 30 | C3 | 0.870 | 0.738 | 0.043 |
| pilot_effect | 30 | C4 | 0.573 | 0.302 | 5.0 |
| pilot_effect | 40 | C1 | 1.000 | 0.998 | 0.179 |
| pilot_effect | 40 | C2 | 0.998 | 0.998 | 0.086 |
| pilot_effect | 40 | C3 | 0.958 | 0.843 | 0.037 |
| pilot_effect | 40 | C4 | 0.805 | 0.520 | 6.0 |
| pilot_effect | 50 | C1 | 1.000 | 1.000 | 0.158 |
| pilot_effect | 50 | C2 | 1.000 | 1.000 | 0.077 |
| pilot_effect | 50 | C3 | 0.990 | 0.927 | 0.033 |
| pilot_effect | 50 | C4 | 0.930 | 0.748 | 7.0 |
| half_effect | 30 | C1 | 0.932 | 0.830 | 0.144 |
| half_effect | 30 | C2 | 0.542 | 0.362 | 0.085 |
| half_effect | 30 | C3 | 0.158 | 0.058 | 0.043 |
| half_effect | 30 | C4 | 0.312 | 0.128 | 3.5 |
| half_effect | 40 | C1 | 0.965 | 0.927 | 0.124 |
| half_effect | 40 | C2 | 0.705 | 0.500 | 0.073 |
| half_effect | 40 | C3 | 0.193 | 0.087 | 0.037 |
| half_effect | 40 | C4 | 0.448 | 0.175 | 4.0 |
| half_effect | 50 | C1 | 0.998 | 0.988 | 0.11 |
| half_effect | 50 | C2 | 0.760 | 0.552 | 0.067 |
| half_effect | 50 | C3 | 0.193 | 0.098 | 0.034 |
| half_effect | 50 | C4 | 0.685 | 0.362 | 5.0 |

## Exact one-sided 95% upper bound on the bug-loss rate

| Bugs with a PF test | 0 bugs lost | 1 bug lost | 2 bugs lost |
|---|---|---|---|
| 30 | 0.095 | 0.149 | 0.195 |
| 40 | 0.072 | 0.113 | 0.149 |
| 50 | 0.058 | 0.091 | 0.121 |

## Classification (rule fixed in D-140: share >= 0.80 at p < 0.0125, half effect, 30 bugs)

| Hypothesis | Classification |
|---|---|
| C1 | adequately powered |
| C2 | underpowered |
| C3 | underpowered |
| C4 | underpowered |

---
tipo: envio
n: 2
fecha: 2026-10-23
commit: cbe4927
rank_points: 100
f_max: 1.0
hipotesis_1: BUB1B AR_comphet
---
# SUB-2

## Cambios respecto del envío anterior
- Mismo CSV que [[SUB-1]] (`felipemoralesdev_mva-pipeline-v2.csv`, sha256 `3d0cdb134524…`).
- Informe de métodos pulido (confirmación de la evaluación, CADD excluido, seguimiento clínico) y README.

## Criterio de EPCR
Igual que SUB-1: softmax (T = 0,1) y override de la fila 1 a 0,85 ([[ADR-011-epcr-de-la-hipotesis-principal]]).

## Hipótesis enviadas

| # | gen | modelo | EPCR | tipo |
| --- | --- | --- | --- | --- |
| 1 | BUB1B | AR_comphet | 0.85 | primary |
| 2 | CTU2 | AR_hom | 0.0686 | primary |
| 3 | PEX5 | AR_hom | 0.0686 | primary |
| 4 | SLC22A1 | AR_hom | 0.0686 | primary |
| 5 | ADAMTS1 | AR_comphet | 0.0673 | primary |
| 6 | SERPINA1 | AR_comphet | 0.0665 | primary |
| 7 | HLA-DQA1 | AR_comphet | 0.053 | primary |
| 8 | HLA-DRB1 | AR_comphet | 0.053 | primary |
| 9 | POU6F2 | AR_comphet | 0.053 | primary |
| 10 | MT-CYB | AR_hom | 0.0524 | primary |

## Resultado
Rank points: **100** · F-max: **1,000** · Lectura del resultado: reenvío con el mismo CSV que SUB-1 (mismo sha256), solo para actualizar el informe que revisa el jurado; el evaluador es determinista y el leaderboard muestra solo el mejor envío.

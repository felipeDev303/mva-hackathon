---
tipo: envio
n: 1
fecha: 2026-10-22
commit: dadd363
rank_points: 100
f_max: 1.0
hipotesis_1: BUB1B AR_comphet
---
# SUB-1

## Cambios respecto del envío anterior
- Primer envío. Pipeline v2: REVEL, AlphaMissense y SpliceAI (panel); pesos solo con predictores presentes; una hipótesis por gen; sin filas intergénicas ([[ADR-010-predictores-de-vep-y-pesos-con-predictores-presentes]]).

## Criterio de EPCR
Softmax (T = 0,1) sobre el top-10; fila 1 (par BUB1B) con override a 0,85 ([[ADR-011-epcr-de-la-hipotesis-principal]]).

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
Rank points: **100** · F-max: **1,000** · Lectura del resultado: el par BUB1B c.2210T>G p.(Leu737*) + c.3006T>G p.(Asn1002Lys) en la fila 1 coincide exactamente con la respuesta confirmada clínicamente; la EPCR de la fila 1 queda estrictamente por encima del resto (F-max = 1).

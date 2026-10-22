---
tipo: corrida
fecha: 2026-10-21
fase: 2-priorizacion
comando: make real-prioritize
commit: f413273-dirty
estado: ok
outputs: ["outputs/funnel.json", "outputs/genes_ranked.tsv"]
decisiones: []
---
# RUN-2026-10-21-prioritize

## Qué cambió respecto de la corrida anterior
- 

## Resultado agregado

### Embudo

| paso | n |
| --- | --- |
| input | 6400670 |
| pass_filter | 6400670 |
| non_reference_gt | 6400670 |
| in_gene | 6400670 |
| rare_af_le_0.01 | 104384 |
| functional_or_known | 413 |
| genes_with_hypothesis | 128 |
| hypotheses | 146 |

### Top 10 genes

| rank_with_prior | rank_no_prior | gene | model | phase | score | score_no_prior | panel |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 11 | BUB1B | AR_comphet | unknown | 0.1432 | 0.1432 | mva_established |
| 2 | 1 | CTU2 | AR_hom | hom | 0.1225 | 0.245 | none |
| 3 | 2 | PEX5 | AR_hom | hom | 0.1225 | 0.245 | none |
| 4 | 3 | SLC22A1 | AR_hom | hom | 0.1225 | 0.245 | none |
| 5 | 4 | ADAMTS1 | AR_comphet | unknown | 0.1207 | 0.2415 | none |
| 6 | 5 | SERPINA1 | AR_comphet | unknown | 0.1196 | 0.2392 | none |
| 7 | 7 | . | AR_comphet | unknown | 0.098 | 0.196 | none |
| 8 | 6 | HLA-DQA1 | AR_comphet | unknown | 0.098 | 0.196 | none |
| 9 | 9 | HLA-DRB1 | AR_comphet | unknown | 0.098 | 0.196 | none |
| 10 | 8 | POU6F2 | AR_comphet | unknown | 0.098 | 0.196 | none |

## Interpretación
- 

## Siguiente paso
- [ ] 

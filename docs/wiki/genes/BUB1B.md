---
tipo: gen
gen: BUB1B
panel: mva_established
rank_con_prior: 
rank_sin_prior: 
---
# BUB1B

## Función y mecanismo
Codifica BUBR1, componente central del punto de control del ensamblaje del huso (SAC). Su déficit
permite la separación prematura de cromátidas y la aneuploidía. Locus 15q15.1.

## Fenotipo asociado
MVA1 (OMIM 257300), autosómica recesiva: restricción del crecimiento, microcefalia, aneuploidías
en mosaico y riesgo de cáncer infantil (incluido rabdomiosarcoma embrionario en las familias de [[hanks-2004]]).

## Alelos descritos (literatura pública)
- Truncante + missense en el dominio quinasa ([[hanks-2004]]).
- Un truncante + haplotipo hipomórfico ([[matsuura-2006]]); el hipomorfo es rs576524605,
  NC_000015.10:g.40117088G>A, upstream, reduce la expresión
  ([ClinGen](https://dosage.clinicalgenome.org/clingen_gene.cgi?sym=BUB1B), [GenCC](https://thegencc.org/submissions/SGC-105573.2)).
- Hipomorfo upstream + inserción Alu en el intrón 8 ([caso prenatal, PMC5462940](https://pmc.ncbi.nlm.nih.gov/articles/PMC5462940)).
- Homocigoto 2386-11A>G (splicing) con cáncer gastrointestinal en un adulto (GenCC).

## Implicaciones para el pipeline
- Rescate del hipomorfo vía `known_variants` ([[ADR-004-variantes-conocidas]]).
- Revisar inserciones y SV en el gen durante la revisión en IGV.

## Evidencia en este caso (nivel gen)
<!-- Rankings con y sin prior, modelo, fase. Sin genotipos. -->

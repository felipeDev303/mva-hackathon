# Literatura pública de referencia

## MVA: genes y mecanismos
| Gen (OMIM) | Referencia | Punto clave para el pipeline |
|---|---|---|
| BUB1B · MVA1 (#257300) | Hanks et al., *Nat Genet* 2004;36:1159 | Bialélico: truncante + missense en el dominio quinasa de BUBR1 (SAC). |
| BUB1B | Matsuura et al., *Am J Med Genet A* 2006;140A:358 | 7 familias japonesas con un solo truncante; el 2.º alelo es un haplotipo hipomórfico (6G3). |
| BUB1B | Ochiai et al. (PMID 28611924, citado por ClinGen/GenCC) | Hipomorfo identificado: rs576524605, NC_000015.10:g.40117088G>A (upstream, reduce expresión). |
| BUB1B | Caso prenatal PCS/MVA, 2017 (PMC5462940) | Compuesto: hipomorfo upstream + inserción Alu en intrón 8 → **revisar SV/inserciones**. |
| BUB1B | Rio Frio et al., *NEJM* 2010 | Homocigoto 2386-11A>G (splicing): cáncer GI, fenotipo atenuado. |
| BUB1B | Suijkerbuijk et al., *Cancer Res* 2010 | Mecanismos moleculares de disfunción de BUBR1 en MVA. |
| CEP57 · MVA2 (#614114) | Snape et al., *Nat Genet* 2011;43:527 | Truncantes homocigotos; fenotipo más leve, centrosoma. |
| CEP57 | Aziz et al., *JCI* 2018 | Haploinsuficiencia de Cep57 en ratón: aneuploidía y cáncer. |
| TRIP13 · MVA3 (#617598) | Yost et al., *Nat Genet* 2017;49:1148 | Bialélicos; todos con tumor de Wilms; defecto severo del SAC. |
| CENATAC/CCDC84 · MVA4 (#620153) | de Wolf et al., *EMBO J* 2021;40:e106536 | Truncantes bialélicos; espliceosoma menor (intrones AT-AN) → defecto de congresión. |
| KNL1, ZWINT | de Wolf, tesis UMC Utrecht 2021 | Otros reguladores mitóticos en pacientes MVA/MVA-like. |
| Revisión | García-Castillo et al., *AJMG A* 2008 | Subtipos clínicos y heterogeneidad. |

Implicaciones: (1) modelo AR con compuestos que pueden incluir **alelos no codificantes**;
(2) mirar variantes estructurales e inserciones en genes candidatos; (3) TRIP13 y BUB1B se asocian
a cánceres infantiles específicos (útil para correlación fenotipo y hallazgos secundarios).

## Métodos de priorización y evaluación
- Stenton et al., *Hum Genomics* 2024;18:44 — CAGI6 Rare Genomes Project (base del scoring: rank points, F-max, EPCR).
- Smedley et al., *Nat Protoc* 2015 — Exomiser; docs actuales: exomiser.readthedocs.io (v15.1, jun-2026).
- Notas de la release 15.0 de Exomiser — modelo reentrenado con casos resueltos del 100,000 Genomes Project.
- Richards et al., *Genet Med* 2015 — criterios ACMG/AMP. Abou Tayoun et al., *Hum Mutat* 2018 — PVS1.
- Walker et al., *AJHG* 2023 — ClinGen SVI: evidencia de splicing en ACMG/AMP.
- Pejaver et al., *AJHG* 2022 — calibración de predictores in silico (umbrales REVEL/CADD para PP3/BP4).

## Anotación y predictores
- McLaren et al., *Genome Biol* 2016 — Ensembl VEP (release 116, jun-2026).
- Chen et al., *Nature* 2024 — gnomAD v4.
- Rentzsch et al., *NAR* 2019 / Schubach et al., *NAR* 2024 — CADD.
- Ioannidis et al., *AJHG* 2016 — REVEL. Cheng et al., *Science* 2023 — AlphaMissense.
- Jaganathan et al., *Cell* 2019 — SpliceAI.
- Landrum et al., *NAR* 2018 — ClinVar. Gargano et al., *NAR* 2024 — HPO.
- Martin et al., *bioRxiv* 2016 / Patterson et al., *J Comput Biol* 2015 — WhatsHap (fase por lecturas).

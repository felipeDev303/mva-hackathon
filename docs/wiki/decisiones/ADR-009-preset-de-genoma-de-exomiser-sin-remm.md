---
tipo: decision
id: ADR-009
fecha: 2026-10-19
estado: aceptada
parametro: config/exomiser-genome-analysis.yml, scripts/40_exomiser.sh
reemplaza: 
---
# ADR-009 · Preset de genoma de Exomiser sin REMM

## Contexto
- Exomiser 15.1.0 cambió su línea de comandos: la muestra va como phenopacket (`--sample`), y el VCF, el ensamblaje y el
  análisis van por separado (`--vcf`, `--assembly`, `--analysis`). El script del scaffold usaba el formato antiguo.
- El preset de genoma de la distribución (`examples/preset-genome-analysis.yml`) incluye REMM entre sus fuentes de
  patogenicidad. REMM requiere un archivo aparte que no está disponible localmente; con él activo, Exomiser no arranca.
- `application.properties` traía activas `exomiser.hg19.data-version`, `remm.version` y `cadd.version` sin sus datos.
- El id del phenopacket debe coincidir con el nombre de la muestra en el VCF; `PROBAND01` es solo el id del Space.

## Opciones consideradas
1. Descargar REMM y usar el preset tal cual.
2. Versionar en el repo una copia del preset sin REMM y dejar solo los datos hg38 y phenotype en `application.properties`.

## Decisión
Opción 2. `config/exomiser-genome-analysis.yml` = preset de genoma 15.1.0 con
`pathogenicitySources: [REVEL, MVP, ALPHA_MISSENSE, SPLICE_AI]`. El phenopacket usa la muestra del VCF
(`bcftools query -l`), que vive solo en `work/`; los errores de Exomiser se muestran con el id enmascarado.

## Evidencia
- Corrida principal: [[RUN-2026-10-19-exomiser]] · sensibilidad: [[RUN-2026-10-22-exomiser]] (ver [[ADR-008-hpo-del-probando-sin-antecedente-familiar]]).
- Commit `ad80a0b`.

## Consecuencias
- Exomiser pierde REMM, su score específico para variantes no codificantes regulatorias. Conserva SpliceAI, AlphaMissense,
  REVEL y MVP desde sus propios datos 2512.
- El preset mantiene `priorityScoreFilter` (HiPhive ≥ 0,501): solo reporta genes con similitud fenotípica. Su top-50 es un
  ranking fenotípico, no un listado exhaustivo de variantes.

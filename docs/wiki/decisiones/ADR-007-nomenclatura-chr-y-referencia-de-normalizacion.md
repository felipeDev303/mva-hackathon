---
tipo: decision
id: ADR-007
fecha: 2026-10-18
estado: aceptada
parametro: paths.reference_fasta, scripts/20_normalize.sh 
reemplaza: 
---
# ADR-007 · Nomenclatura chr y referencia de normalización

## Contexto
- El VCF del dataset (GATK) usa contigs sin prefijo (`1`, `2`, …) y declara como referencia
  `GCA_000001405.15_GRCh38_no_alt_analysis_set_plus_hs38d1_maskedGRC_exclusions_v2_no_chr` (2580 contigs).
- El Space exige coordenadas GRCh38 con prefijo `chr` (p. ej. `chr15`).
- `bcftools norm` necesita un FASTA con los mismos nombres de contig que el VCF.

## Opciones consideradas
1. Conseguir o reconstruir la referencia exacta (enmascarada v2, sin `chr`) y trabajar sin prefijo hasta la entrega.
2. Renombrar el FASTA estándar a nombres sin `chr`.
3. Renombrar el VCF a `chr` al normalizar, conservar solo cromosomas primarios y usar
   `GCA_000001405.15_GRCh38_no_alt_plus_hs38d1_analysis_set` (NCBI, nombres UCSC).

## Decisión
Opción 3. `scripts/20_normalize.sh` aplica `bcftools annotate --rename-chrs` (`1`→`chr1` … `MT`/`M`→`chrM`),
filtra a chr1–22, X, Y, M y normaliza contra `ref/GRCh38.fa`.

## Evidencia
- Cabecera del VCF: 2580 contigs; contig `1` de 248 956 422 pb (GRCh38).
- FASTA usado: 2580 contigs; `chr1` de 248 956 422 pb.
- Corrida: `make real-normalize` → **0** diferencias de REF en `work/normalize.log` → [[RUN-2026-10-18-real-normalize]]
- Commit: `f315a13`

## Consecuencias
- Todo el pipeline queda en nomenclatura `chr`, igual que el Space, IGV y la referencia para realinear los FASTQ.
- Se descartan variantes en decoys (hs38d1) y contigs no primarios: el Space no los evalúa.
- La referencia del dataset enmascara con `N` regiones de falsa duplicación (exclusions v2). Ahí no hay llamadas,
  así que normalizar contra la versión sin enmascarar no cambia el REF de las variantes presentes.
  Se verifica con el conteo de diferencias de REF (esperado: 0 o casi 0).
- Limitación para el write-up: si se realinean los FASTQ, será contra la referencia sin enmascarar; en las regiones
  de falsa duplicación el mapeo puede diferir del original.

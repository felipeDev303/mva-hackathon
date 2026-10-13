# Methods write-up — plantilla (Track 1)

> Se entrega como `.md` o `.pdf` con tu usuario/equipo en el nombre. Lo evalúa un panel por rigor
> científico y profundidad. Sin datos a nivel genoma: unas pocas variantes nombradas sí; tablas no.

## 1. Resumen (≤150 palabras)
Hipótesis principal (gen, modelo, variantes en HGVS), confianza y por qué.

## 2. Datos y control de calidad
- Archivos usados (VCF/BAM), build GRCh38, caller (de la cabecera).
- `outputs/qc_summary.json`: SNVs, indels, Ti/Tv, het/hom. Interpretación breve.

## 3. Pipeline
Tabla con herramienta, versión y propósito (`make versions`): bcftools, VEP 116 (+CADD, REVEL,
SpliceAI), Exomiser 15.1 (datos 25xx), WhatsHap, igv-reports.

## 4. Filtrado y priorización
- Embudo (`outputs/funnel.json`) como tabla o figura.
- Umbrales y su justificación (AF ≤ 1 % por alelo en recesivo; impactos; SpliceAI ≥ 0.2).
- Fórmula de score (copiar de `src/mva/prioritize.py`) y pesos de `config.yaml`.
- Modelos de herencia evaluados (AR comp-het, AR hom, AD) y por qué se priorizó AR.
- **Ranking con y sin prior de genes** (`rank_with_prior` vs `rank_no_prior`): demuestra que el
  pipeline no depende de conocer los genes de MVA.

## 5. Interpretación de los candidatos
Para cada candidato principal: consecuencia, frecuencia poblacional, predictores, ClinVar,
fase (cis/trans/desconocida y cómo se determinó), revisión visual en IGV, criterios ACMG/AMP
aplicables (Richards 2015; PVS1 según Abou Tayoun 2018; splicing según ClinGen SVI 2023).
Concordancia con el fenotipo (HPO) y con la literatura de MVA.

## 6. EPCR
Cómo se calibraron (softmax T=…, ajustes manuales y su razón).

## 7. Hallazgos secundarios (opcional)
Variantes accionables no relacionadas con el fenotipo, con `finding_type=secondary`.

## 8. Limitaciones
Sin padres (fase por lecturas solamente), variantes estructurales/CNV no evaluadas (o sí),
regiones no codificantes, sesgos de los predictores.

## 9. Uso de LLM y datos
Línea de proveedor/tier/configuración (ver `DATA_POLICY.md`) y descripción de la frontera de datos.

## 10. Reproducibilidad
Repo, commit, `environment.yml`, `make real-all`.

## Agradecimiento (obligatorio)
"This work was made possible through the Hackathon, organized by Sage Bionetworks in partnership
with the MVA Society, Hugging Face, and BEACON (The Benchmarking, Evaluation, and Assessment
Consortium for Science), with prize sponsorship from AWS and Anthropic. We are deeply grateful to
the child and their family who generously contributed their data and their story to advance
research into this rare disease. We acknowledge their trust in making this Hackathon possible."

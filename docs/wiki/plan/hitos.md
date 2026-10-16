---
tipo: plan
---
# Hitos

Cada fase tiene fecha límite (calendario del instructivo, hora de Chile) y un criterio de "hecho"
verificable. Marca las tareas aquí o en el diario; el [[tablero]] las junta.

## Fase 0 · Setup y QC — 14-oct
Hecho cuando `outputs/qc_summary.json` existe, el build es GRCh38 y `make guard` pasa.
- [ ] `make setup` y `make test` (23+ tests en verde)
- [ ] Rutas en `config/config.yaml` y HPO del caso en `config/hpo_terms.txt`
- [ ] `make real-qc`; anotar Ti/Tv, het/hom y caller en la nota de corrida
- [ ] Id de la muestra en `guard.sample_ids` (sin pegarlo en el chat)
- [ ] `make fixtures` con la cabecera real sin muestras

## Fase 1 · Normalización y anotación — 16-oct
Hecho cuando existen `work/annotated.tsv` y `outputs/exomiser_genes_top50.tsv`, y el guard pasa.
- [ ] `make real-normalize`
- [ ] Caché VEP 116 + plugins CADD/REVEL/SpliceAI
- [ ] `make real-annotate` (de noche)
- [ ] Exomiser 15.1 + datos hg38/phenotype; `make real-exomiser`
- [ ] ¿Hay VCF de SV/CNV en el dataset? (ver [[preguntas]])

## Fase 2 · Priorización — 18-oct
Hecho cuando `outputs/top_pairs.tsv` tiene 10 hipótesis y cada parámetro no-default tiene su ADR.
- [ ] `make real-prioritize`
- [ ] Comparar ranking con y sin prior de genes
- [ ] Revisar el embudo: ¿algún filtro elimina demasiado?
- [ ] ADR aceptado o reemplazado para cada umbral (ADR-001 a ADR-004)

## Fase 3 · Fase cis/trans e IGV — 19-oct
Hecho cuando `outputs/phase_summary.tsv` existe y los top-3 están revisados en IGV.
- [ ] `make real-phase`
- [ ] `make real-prioritize PHASE=outputs/phase_summary.tsv`
- [ ] Revisión visual en `work/igv/` (capturas quedan ahí, no en la wiki)

## Primer envío — 19-oct
- [ ] `make fetch-eval real-submission` y `make wiki-sub`
- [ ] Anotar rank points y F-max en la nota del envío

## Write-up — 20 al 23-oct
Hecho cuando `docs/METHODS.md` cita una corrida y un commit por cada número.
- [ ] Borrador desde ADR y corridas
- [ ] ACMG/AMP del par principal
- [ ] Línea de uso del LLM (proveedor, tier, configuración)

## Envío final — 23-oct · Cierre — 24-oct 20:59
- [ ] Envío final y nota de envío
- [ ] `make guard` sobre todo el repo y revisión a ojo de la wiki
- [ ] Repo público

## Después del cierre — antes del 23-nov
- [ ] `scripts/90_delete_data.sh`
- [ ] Email de confirmación de borrado (plantilla en `docs/DATA_POLICY.md`)

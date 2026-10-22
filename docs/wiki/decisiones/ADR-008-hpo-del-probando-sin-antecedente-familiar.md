---
tipo: decision
id: ADR-008
fecha: 2026-10-19
estado: aceptada
parametro: config/hpo_terms.txt 
reemplaza: 
---
# ADR-008 · HPO del probando sin antecedente familiar

## Contexto
- El dataset trae 8 términos HPO (en los `docx` del caso).
- HP:0200067 (Recurrent spontaneous abortion) describe a los **padres**, no al probando.
- Exomiser compara el perfil HPO con el de cada gen; un rasgo ajeno al paciente puede desplazar el
  ranking hacia genes de pérdida gestacional.

## Opciones consideradas
1. Usar los 8 términos tal como vienen en el dataset.
2. Usar los 7 términos del probando y correr los 8 como análisis de sensibilidad.

## Decisión
Opción 2. `config/hpo_terms.txt` tiene 7 términos activos; HP:0200067 queda comentado para la corrida de sensibilidad.

## Evidencia
- Corrida principal (7 HPO): [[RUN-2026-10-19-exomiser]] · Exomiser 15.1.0, datos 2512 hg38, preset de genoma sin REMM.
  Top-3 (gen · MOI · p · combinado · fenotipo · variante):
  1. BUB1B · AD · 0,0004 · 0,546 · 0,547 · 1,000
  2. BUB1B · AR · 0,0007 · 0,488 · 0,766 · 0,961
  3. FANCD2 · AR · 0,021 · 0,181 · 0,640 · 0,900
- Con 7 HPO y sin prior de genes, BUB1B ocupa los dos primeros puestos; en AR el fenotipo calza mejor (0,77) con MVA1.
- Corrida de sensibilidad (8 HPO, con HP:0200067), 22-oct · resumen en `outputs/exomiser_genes_top50_8hpo.tsv`:
  1. BUB1B · AD · 0,0005 · 0,586 · 0,563 · 1,000
  2. BUB1B · AR · 0,0006 · 0,557 · 0,793 · 0,961
  3. FANCD2 · AR · 0,015 · 0,219 · 0,663 · 0,900
- **El resultado no cambia**: BUB1B queda #1 y #2 y FANCD2 #3 con 7 y con 8 HPO. El top-10 de genes coincide en 9 de 10
  (con 7 HPO entra COL7A1; con 8, LZTR1). Agregar el antecedente de los padres solo sube un poco los scores fenotípicos.

## Consecuencias
- El ranking fenotípico refleja solo rasgos del paciente.
- El write-up reporta ambas corridas como argumento de robustez: la conclusión no depende de incluir HP:0200067.
- El antecedente de abortos se usa como contexto clínico (portadores AR), no como rasgo del probando.


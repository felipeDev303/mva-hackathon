---
tipo: decision
id: ADR-008
fecha: 2026-10-19
estado: propuesta
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
- Corrida de sensibilidad (8 HPO, con HP:0200067): pendiente.
- ¿Cambia el top-10 o la posición de BUB1B al agregar HP:0200067? Pendiente.

## Consecuencias
- El ranking fenotípico refleja solo rasgos del paciente.
- El write-up reporta ambas corridas: si coinciden, es un argumento de robustez; si difieren, se discute.
- El antecedente de abortos se usa como contexto clínico (portadores AR), no como rasgo del probando.


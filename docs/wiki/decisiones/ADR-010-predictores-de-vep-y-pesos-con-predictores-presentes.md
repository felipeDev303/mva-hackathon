---
tipo: decision
id: ADR-010
fecha: 2026-10-22
estado: aceptada
parametro: scoring.weights, columns.alphamissense, scripts/05_vep_plugins.sh, scripts/06_spliceai_panel.sh, scripts/30_vep.sh
reemplaza: 
---
# ADR-010 · Predictores de VEP y pesos solo con predictores presentes

## Contexto
- La anotación v1 corrió sin plugins (sin CADD, REVEL ni SpliceAI). El score dividía por la suma de **todos** los pesos,
  así que el máximo posible quedaba en ~0,5 y el missense de BUB1B (AlphaMissense 0,92 en los datos de Exomiser) valía 0,19
  solo por su impacto. Con `min()` en el score del par, BUB1B caía al #11 sin prior.
- CADD v1.7 pesa ~80 GB y SpliceAI genómico (Ensembl, masked SNV, MANE v1.4) 28,6 GB. A la velocidad disponible
  (~0,2 MB/s) SpliceAI tardaría ~40 h: no llega antes del cierre.

## Opciones consideradas
1. Seguir sin predictores y defender el ranking sin prior solo con Exomiser.
2. Agregar los predictores que caben en el tiempo y repartir los pesos solo entre los presentes.
3. Esperar a CADD y SpliceAI completos.

## Decisión
Opción 2.
- **AlphaMissense** (genoma completo, 0,6 GB) y **REVEL v1.3** (0,7 GB, procesado a GRCh38) vía `scripts/05_vep_plugins.sh`.
- **SpliceAI dirigido**: consulta remota con tabix solo en los 29 genes del panel (`gene_prior`: MVA + punto de control
  mitótico, ±5 kb; 2,5 Mb; 5,5 M SNV) vía `scripts/06_spliceai_panel.sh`. El plugin exige archivo de indels: se usa uno vacío.
- **CADD**: no se usa.
- **Pesos**: `variant_score` reparte los pesos solo entre impacto, ClinVar y los predictores con algún valor en el set.
  AlphaMissense entra con peso 0,15 (igual que REVEL).
- Además: se descartan filas sin gen (`.`) y el top-10 lleva una hipótesis por gen.

## Evidencia
- Piloto en la región de BUB1B (chr15:40,10–40,25 Mb, 278 filas): REVEL 1 valor, AlphaMissense 1 valor (el missense),
  SpliceAI 9 valores. Los tres plugins leen sus archivos.
- Corrida completa: [[RUN-2026-10-22-annotate]] · 4 682 907 registros, 0 errores; filas con valor: REVEL 8 321,
  AlphaMissense 10 084, SpliceAI 1 791 (genes del panel).
- Priorización v2: [[RUN-2026-10-22-prioritize]] · embudo 3 427 054 filas en gen → 45 125 raras → 387 funcionales o
  conocidas → 127 genes / 142 hipótesis.
- **BUB1B pasa de #11 a #1 sin prior** (y sigue #1 con prior): score del par 0,317 frente a 0,258 del siguiente.
  El missense p.(Asn1002Lys) sube de 0,19 a 0,43; el nonsense p.(Leu737\*) queda en 0,45.
- El top-10 ya no tiene filas sin gen ni genes repetidos.
- Commit `a3f9f19`.

## Consecuencias
- El score de cada variante usa la evidencia disponible sin diluirla por la que falta; los números son comparables
  dentro de una corrida, no entre corridas con distintos plugins.
- SpliceAI solo cubre los genes del panel: fuera de ellos, el rescate por splicing del embudo (SpliceAI ≥ 0,2) no actúa.
  El splicing genómico queda cubierto por Exomiser (que usa SpliceAI de sus datos). Se declara como limitación.
- Sin CADD, las variantes no codificantes fuera del panel dependen del impacto de VEP y de ClinVar.
- Mejora futura: repartir los pesos **por variante** (solo predictores aplicables). Hoy un nonsense no recibe aporte de
  REVEL ni AlphaMissense (no aplican a un codón de parada) y esos pesos igual cuentan en el denominador.

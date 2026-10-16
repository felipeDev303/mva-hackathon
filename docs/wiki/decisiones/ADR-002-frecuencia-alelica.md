---
tipo: decision
id: ADR-002
fecha: 2026-10-13
estado: propuesta
parametro: filters.af_max_recessive, filters.af_max_dominant
reemplaza: 
---
# ADR-002 · Umbrales de frecuencia alélica

## Contexto
Un trastorno recesivo raro tolera alelos portadores más frecuentes que uno dominante.

## Opciones consideradas
1. AF ≤ 1 % por alelo en recesivo, ≤ 0.01 % en dominante (máximo entre gnomAD exomas, genomas y `MAX_AF`).
2. AF ≤ 0.5 % en recesivo (más estricto, menos candidatos).

## Decisión
Opción 1 (default del scaffold). Las variantes de `known_variants` se rescatan aunque superen el umbral (ver [[ADR-004-variantes-conocidas]]).

## Evidencia
- Corridas: revisar cuántas variantes elimina el paso `rare_af_le_0.01` en `outputs/funnel.json`.

## Consecuencias
Si el embudo deja demasiados candidatos, considerar la opción 2 y documentarlo aquí.

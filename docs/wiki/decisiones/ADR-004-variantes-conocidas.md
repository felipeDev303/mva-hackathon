---
tipo: decision
id: ADR-004
fecha: 2026-10-13
estado: propuesta
parametro: known_variants, scoring.known_variant_floor
reemplaza: 
---
# ADR-004 · Rescate de variantes conocidas de la literatura

## Contexto
En BUB1B, el segundo alelo puede ser un hipomorfo regulatorio upstream (rs576524605) que VEP marca como
MODIFIER y que los predictores puntúan bajo. Un filtro por impacto lo descartaría.

## Opciones consideradas
1. Sin rescate.
2. Rescatar las variantes listadas en `known_variants` y darles un piso de score de 0.8.

## Decisión
Opción 2 (default del scaffold).

## Evidencia
- Literatura: [[matsuura-2006]]; ClinGen/GenCC para BUB1B (ver [[BUB1B]]).

## Consecuencias
El write-up debe declarar el rescate y mostrar el ranking con y sin él.

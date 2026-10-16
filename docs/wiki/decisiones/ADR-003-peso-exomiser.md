---
tipo: decision
id: ADR-003
fecha: 2026-10-13
estado: propuesta
parametro: scoring.exomiser_pheno_weight
reemplaza: 
---
# ADR-003 · Peso del score fenotípico de Exomiser

## Contexto
El score del gen combina evidencia de variante (VEP + predictores) con similitud fenotípica (Exomiser + HPO).
Son señales independientes; ninguna debería dominar sola.

## Opciones consideradas
1. 0.0: solo evidencia de variante.
2. 0.3: el fenotipo modula hasta un 30 % del score del par.
3. 0.5 o más: el fenotipo pesa tanto como la variante.

## Decisión
Opción 2 (default del scaffold).

## Evidencia
- Corridas: comparar el top-10 con 0.0, 0.3 y 0.5 y registrar aquí cuánto cambia.

## Consecuencias
Con HPO poco específicos, un peso alto favorece genes muy estudiados.

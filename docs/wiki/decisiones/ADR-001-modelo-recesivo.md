---
tipo: decision
id: ADR-001
fecha: 2026-10-13
estado: propuesta
parametro: scoring.model_weights
reemplaza: 
---
# ADR-001 · Priorizar el modelo autosómico recesivo

## Contexto
Los cuatro genes de MVA establecidos (BUB1B, CEP57, TRIP13, CENATAC) son autosómicos recesivos, y el
`evaluation.py` del Space trata la respuesta como un par compuesto heterocigoto.

## Opciones consideradas
1. Pesos iguales para AR compuesto, AR homocigoto y AD.
2. AR con peso 1.0 y AD penalizado (×0.3), conservando AD como hipótesis alternativa.
3. Descartar AD.

## Decisión
Opción 2 (default del scaffold): `scoring.model_weights = {AR_comphet: 1.0, AR_hom: 1.0, AD_single: 0.3}`.

## Evidencia
- Literatura: [[hanks-2004]], [[matsuura-2006]], [[de-wolf-2021]]; genes [[BUB1B]], [[CEP57]], [[TRIP13]], [[CENATAC]].
- Corridas: pendiente (aceptar tras la primera `make real-prioritize`).

## Consecuencias
Una variante dominante ultra rara solo supera a un par AR si su score es más de 3 veces mayor.

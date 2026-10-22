---
tipo: decision
id: ADR-011
fecha: 2026-10-22
estado: aceptada
parametro: config/epcr_overrides.csv (make real-submission EPCR=…)
reemplaza: 
---
# ADR-011 · EPCR de la hipótesis principal

## Contexto
- `submission.py` calcula la EPCR con una softmax (T = 0,1) sobre los scores del top-10. Reparte la probabilidad entre las
  10 filas: en la v1, la hipótesis principal quedaba con EPCR 0,12 aunque la evidencia que la respalda es fuerte.
- El puntaje automático solo depende del orden (rank points) y de que la fila 1 tenga una EPCR estrictamente mayor que la
  fila 2 (F-max). El valor absoluto sí importa para el jurado: la EPCR debe reflejar la confianza.

## Opciones consideradas
1. Dejar la softmax sin tocar.
2. Override documentado de la fila 1, manteniendo la softmax para el resto.

## Decisión
Opción 2: fila 1 (par BUB1B c.2210T>G p.(Leu737\*) + c.3006T>G p.(Asn1002Lys)) con **EPCR 0,85**, verificando antes de
cada entrega que la fila 1 sea ese par.

Por qué 0,85 y no más:
- A favor: BUB1B #1 con y sin prior en nuestro score; Exomiser sin prior lo pone #1 y #2 (p = 0,0004 y 0,0007), robusto a
  la inclusión de HP:0200067; nonsense en el exón 17 de 23 (NMD esperado), ClinVar P/LP ★★; missense en el dominio quinasa
  (UniProt O60566, 766–1050) con AlphaMissense 0,92; arquitectura alélica típica de MVA1; fenotipo concordante.
- En contra: fase desconocida (sin padres ni lecturas alineadas; a 10,9 kb tampoco se podría fasar con lecturas cortas);
  el missense queda como VUS por ACMG sin PM3; sin análisis de SV.

## Evidencia
- Priorización v2: [[RUN-2026-10-22-prioritize]] · ver [[ADR-010-predictores-de-vep-y-pesos-con-predictores-presentes]].

## Consecuencias
- El write-up declara el override y su razón; el resto de las filas conserva la EPCR de la softmax.
- No cambia el puntaje automático mientras la fila 1 siga siendo la de mayor EPCR.

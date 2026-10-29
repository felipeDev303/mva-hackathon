---
tipo: decision
id: ADR-012
fecha: 2026-10-23
estado: aceptada
parametro: config/track2.yaml, src/mva/repurpose.py (make track2)
reemplaza: 
---
# ADR-012 · Método de reposicionamiento del Track 2

## Contexto
- El Track 2 pide fármacos **aprobados** plausibles para el mecanismo, como hipótesis. El panel puntúa rigor (35 %),
  impacto (25 %), innovación (25 %) y escalabilidad (15 %).
- El mecanismo es una pérdida de función bialélica de BUBR1, sensible a dosis: un nulo (p.Leu737\*, UGA, NMD) más un
  probable hipomorfo de estabilidad (p.Asn1002Lys en la pseudoquinasa).
- Para un trastorno de pérdida de función de un componente del punto de control no existen activadores aprobados de la
  vía. Buscar "fármacos que tocan BUB1B" no sirve.

## Opciones consideradas
1. Revisión de literatura curada a mano.
2. Búsqueda en bases fármaco–diana sobre la red de BUB1B, sin reglas de dirección.
3. **Pipeline con dirección del mecanismo:** red + bases fármaco–diana + reglas por rol del gen + ejes curados con
   PMID verificados + score transparente.

## Decisión
Opción 3, en `src/mva/repurpose.py` (`make track2`):
- **Red:** STRING (confianza ≥ 0,9, 25 socios) + participantes de Reactome R-HSA-69618 → 114 genes.
- **Fármacos:** Open Targets (`drugAndClinicalCandidates`) + DGIdb → 503 pares fármaco–gen.
- **Reglas por rol:**
  - `checkpoint`: inhibir = evitar, activar = compatible;
  - `checkpoint_target` (APC/C-CDC20): inhibir = compatible, activar = evitar;
  - el resto, incierto.
- **Ejes curados con proximidad mecanística:**
  - alelo 1,0: lectura a través;
  - nivel de proteína 0,8: NAD⁺/SIRT2, solo contexto;
  - vía 0,7;
  - consecuencia 0,6: senescencia;
  - cáncer 0,5: vulnerabilidad aneuploide.
- **Correcciones regulatorias:** Open Targets refleja la fase histórica en ChEMBL; quercetina = suplemento; ataluren
  no renovado en la UE.
- **Score:** `0,3·aprobado + 0,3·proximidad + 0,2·min(1, PMID verificados/2) + 0,2·min(1, log10(1+co-menciones)/2)`.
- **Vigilar:** venenos del huso, con evidencia contradictoria.

## Evidencia
- Corrida del 23-oct:
  - 114 genes (21 del punto de control, 14 de su diana, 79 otros);
  - **0 fármacos aprobados compatibles desde la red**;
  - 82 pares "evitar": 81 en investigación, sobre todo inhibidores de AURKB y PLK1; vorinostat, el único aprobado, solo por DGIdb;
  - 7 candidatos; 3 en "vigilar"; 10/10 PMID verificados.
- Ranking: gentamicina = ataluren 0,90 > dasatinib 0,88 > metformina 0,65 > cloroquina 0,62 > hidroxicloroquina 0,60 >
  quercetina 0,58 (no aprobada).
- Tests offline en `tests/test_repurpose.py`.

## Consecuencias
- Que la red no dé candidatos aprobados es un resultado: justifica actuar sobre el alelo, la dosis o la consecuencia.
- Los ejes curados dependen de la literatura disponible y quedan explícitos en la config, con su PMID.
- La co-mención en PubMed es una señal gruesa. Pesa solo 0,2 y satura.
- El pipeline es reutilizable para otros genes de MVA (CEP57, TRIP13, CENATAC) o síndromes de inestabilidad
  cromosómica cambiando `seed`, `roles` y `axes`.

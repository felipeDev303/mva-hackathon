---
tipo: plan
---
# Tablero

Requiere el plugin comunitario **Dataview**. Las rutas son relativas a la raíz del vault (`docs/wiki/`).

## Tareas abiertas
```dataview
TASK FROM "plan" OR "diario" OR "00-inicio" WHERE !completed AND text != ""
```

## Últimas corridas
```dataview
TABLE fase, estado, comando, commit FROM "corridas" WHERE tipo = "corrida" SORT fecha DESC, file.name DESC LIMIT 10
```

## Envíos (máximo 6)
```dataview
TABLE fecha, commit, rank_points, f_max, hipotesis_1 FROM "envios" WHERE tipo = "envio" SORT n ASC
```

## Decisiones
```dataview
TABLE estado, fecha, parametro FROM "decisiones" WHERE tipo = "decision" SORT file.name ASC
```

## Preguntas abiertas
```dataview
TASK FROM "preguntas" WHERE !completed
```

## Genes en seguimiento
```dataview
TABLE panel, rank_con_prior, rank_sin_prior FROM "genes" WHERE tipo = "gen" SORT rank_con_prior ASC
```

---
tipo: decision
id: ADR-006
fecha: 2026-10-16
estado: aceptada
parametro: docs/wiki
reemplaza: 
---
# ADR-006 · Wiki de conocimiento dentro del repo

## Contexto
El plan necesita seguimiento diario y el write-up necesita trazabilidad de cada número a una corrida y un commit.

## Opciones consideradas
1. Vault de Obsidian aparte, sincronizado en la nube.
2. `docs/wiki/` dentro del repo, abierta como vault, sincronizada solo con git.

## Decisión
Opción 2: queda versionada con el código, se publica con el repo, y `mva-guard` + pre-commit la revisan.

## Consecuencias
Nada que no pase el guard entra a la wiki; las capturas de IGV quedan en `work/igv/`.

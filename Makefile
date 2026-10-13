# ─────────────────────────────────────────────────────────────────────────────
# Objetivos SEGUROS (fixtures sintéticos; el asistente puede correrlos)
#   make setup | fixtures | test | guard | fetch-eval | versions
# Objetivos REALES (zona roja; los corre SOLO el humano)
#   make real-qc | real-normalize | real-annotate | real-exomiser
#   make real-prioritize | real-phase | real-submission | real-all
# ─────────────────────────────────────────────────────────────────────────────
SHELL := /bin/bash
.ONESHELL:
.SHELLFLAGS := -euo pipefail -c

CFG      ?= config/config.yaml
RAW_VCF  ?= $(shell python3 -c "import yaml;print(yaml.safe_load(open('$(CFG)'))['paths']['raw_vcf'])")
BAM      ?= $(shell python3 -c "import yaml;print(yaml.safe_load(open('$(CFG)'))['paths']['bam'])")
REF      ?= $(shell python3 -c "import yaml;print(yaml.safe_load(open('$(CFG)'))['paths']['reference_fasta'])")
NORM     := work/normalized.vcf.gz
PHASE    ?=
SPACE    := https://huggingface.co/spaces/SageBio/rare-disease-real-kid-mva-hackathon-2026/raw/main

.PHONY: setup fixtures test guard fetch-eval versions \
        real-qc real-normalize real-annotate real-exomiser real-prioritize real-phase real-submission real-all

# ── seguros ──────────────────────────────────────────────────────────────────
setup:
	mamba env create -f environment.yml || mamba env update -f environment.yml
	chmod +x scripts/*.sh .claude/hooks/*.py

fixtures:
	mva-fixtures $(if $(wildcard fixtures/header_nosamples.txt),--header fixtures/header_nosamples.txt,)

test: fixtures
	pytest -q

guard:
	mva-guard outputs submissions

fetch-eval:  ## descarga el evaluador oficial para validar el CSV localmente
	curl -fsSL $(SPACE)/evaluation.py -o vendor/evaluation.py
	@echo "vendor/evaluation.py descargado (no se versiona)."

versions:
	@for t in bcftools samtools vep whatshap java; do printf "%-9s " $$t; ($$t --version 2>&1 || true) | head -1; done
	@python3 --version

# ── reales (humano) ──────────────────────────────────────────────────────────
real-qc:
	scripts/10_header_and_qc.sh $(RAW_VCF)
	$(MAKE) guard

real-normalize:
	scripts/20_normalize.sh $(RAW_VCF) $(REF) $(NORM)

real-annotate: $(NORM)
	scripts/30_vep.sh $(NORM) work/vep.vcf.gz work/annotated.tsv

real-exomiser: $(NORM)
	scripts/40_exomiser.sh $(NORM)
	$(MAKE) guard

real-prioritize:
	EXO=$$(ls work/exomiser/*genes.tsv 2>/dev/null | head -1 || true)
	mva-prioritize $${EXO:+--exomiser-genes "$$EXO"} $(if $(PHASE),--phase $(PHASE),)
	$(MAKE) guard

real-phase:
	scripts/50_phase_and_review.sh $(NORM) $(BAM) $(REF)
	$(MAKE) guard

real-submission:
	mva-submission build outputs/top_pairs.tsv
	$(MAKE) guard

real-all: real-qc real-normalize real-annotate real-exomiser real-prioritize real-phase
	$(MAKE) real-prioritize PHASE=outputs/phase_summary.tsv
	$(MAKE) real-submission

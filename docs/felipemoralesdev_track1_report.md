# MVA Hackathon 2026 · Track 1 — Methods report (v2)

**Participant:** felipemoralesdev · **Repository:** https://github.com/felipeDev303/mva-hackathon (commit `c1877a6`)
**Submission file:** `felipemoralesdev_mva-pipeline-v2.csv` · **Date:** 22 Oct 2026

## 1. Summary

Our top hypothesis is **autosomal recessive mosaic variegated aneuploidy type 1 (MVA1, OMIM 257300)** caused by two
heterozygous variants in **BUB1B** (ENST00000287598.11):

- **c.2210T>G p.(Leu737\*)** (chr15:40209701 T>G): nonsense in exon 17 of 23, predicted to trigger NMD; ClinVar
  pathogenic/likely pathogenic (2 stars).
- **c.3006T>G p.(Asn1002Lys)** (chr15:40220612 T>G): missense in the BUBR1 kinase domain (UniProt O60566, residues
  766–1050); AlphaMissense 0.92.

We propose them as a compound heterozygous pair with **unknown phase**. This truncating plus kinase-domain missense
combination is the classic MVA1 allele architecture (Hanks et al. 2004).

The pair ranks **first in our pipeline both with and without a gene prior**. Exomiser 15.1, which uses no MVA gene list,
independently ranks BUB1B first and second (AD and AR models; p = 0.0004 and 0.0007). That result does not change when the
parental HPO term is added (§4).

Confidence: high for the gene, moderate–high for the pair (EPCR 0.85). The remaining uncertainty is phase, which cannot be
resolved from this dataset.

## 2. Data and quality control

- **Input:** single-sample WGS VCF (GATK) and FASTQ (not used). The dataset has no BAM/CRAM and no parental data.
- **Reference declared in the VCF:** GRCh38 no-alt analysis set + hs38d1, masked (GRC exclusions v2), contigs without the
  `chr` prefix (2,580 contigs). Build confirmed by chr1 length (248,956,422 bp).
- **Raw VCF:** 5,012,204 records · 4,086,641 SNVs · 930,181 indels · 66,860 multiallelic sites.
- **Ti/Tv:** 1.94 raw, **2.02 after PASS / GQ ≥ 20 / DP ≥ 8**, within the WGS range (2.0–2.1).
- **Het/hom ratio:** 1.63. No evidence of extensive homozygosity, consistent with compound heterozygosity rather than a
  homozygous (identity-by-descent) model.

## 3. Pipeline

| Step | Tool (version) | Purpose |
|---|---|---|
| Normalization | bcftools 1.21 | rename contigs to `chr`, keep primary chromosomes, split multiallelics, left-align, PASS, GQ ≥ 20, DP ≥ 8, non-reference GT |
| Reference | NCBI GRCh38 no-alt + hs38d1 analysis set | same base as the dataset reference, UCSC names |
| Annotation | Ensembl VEP 116.3, cache 116 GRCh38 | consequence (`--pick_allele_gene`, MANE/canonical), gnomAD exomes/genomes + MAX_AF, ClinVar, rsIDs |
| VEP plugins | REVEL v1.3, AlphaMissense (hg38), SpliceAI (Ensembl masked SNV, MANE v1.4) | missense and splicing predictors (see below) |
| Phenotype ranking | Exomiser 15.1.0, data 2512 (hg38, phenotype), Java 21 | gene ranking from HPO + variants, genome preset without REMM |
| Prioritization / submission | Python 3.11.9, `mva` package (this repo) | funnel, variant and pair scores, EPCR, validation with the official parser |

Each decision is recorded as an ADR in `docs/wiki/decisiones/`, and each step has a run note in `docs/wiki/corridas/`.

- **ADR-007:** contigs renamed to `chr`; normalization against the unmasked analysis set gave **0 REF mismatches**.
- **ADR-008:** the dataset lists 8 HPO terms. HP:0200067 (*Recurrent spontaneous abortion*) describes the parents, so the
  main analysis uses the **7 proband terms** (HP:0002859, HP:0000121, HP:0004322, HP:0001508, HP:0003202, HP:0001622,
  HP:0001518). An 8-term sensitivity run is also reported.
- **ADR-009:** Exomiser 15 CLI (phenopacket sample, separate VCF and analysis); a versioned copy of the genome preset
  without REMM, whose data were not available.
- **ADR-010, predictors:**
  - AlphaMissense and REVEL genome-wide.
  - **SpliceAI targeted to a 29-gene panel**: the 4 established MVA genes plus 25 mitotic-checkpoint genes, ±5 kb, queried
    remotely with tabix. The genome-wide file (28.6 GB) could not be downloaded in time.
  - CADD not used.
  - Weights are renormalized over the predictors present in the data.
- **ADR-011:** documented EPCR override for the top hypothesis.

## 4. Filtering and prioritization

| Funnel step | Variant × gene rows |
|---|---|
| Annotated input (4,682,907 normalized variants) | 6,400,670 |
| Within a gene (VEP gene symbol) | 3,427,054 |
| Rare (max population AF ≤ 1 % per allele) | 45,125 |
| Functional (HIGH/MODERATE, SpliceAI ≥ 0.2, ClinVar pathogenic) **or** known literature variant | 387 |
| Genes with ≥ 1 hypothesis / hypotheses | 127 / 142 |

**Variant score.** `s_v = Σ w_i c_i / Σ w_i`, with weights from `config/config.yaml`: impact 0.35, REVEL 0.15,
AlphaMissense 0.15, SpliceAI 0.15, ClinVar 0.15. A predictor enters the sum only if it has data in the run. Known
literature variants (`known_variants`, e.g. the BUB1B upstream hypomorph rs576524605) get a floor of 0.8.

**Pair score.** `s_pair = min(s_v1, s_v2) · f_phase · m_model · (1 − w_φ + w_φ · φ_gene)`, where:

- `f_phase` = 1.0 trans, 0.8 unknown, 0.2 cis;
- `m_model` = 1.0 for AR (compound-het or homozygous) and 0.3 for a single ultra-rare dominant variant;
- `w_φ` = 0.3 and `φ_gene` is the Exomiser phenotype score.

A gene prior (1.0 for established MVA genes, 0.8 for the mitotic-checkpoint panel, 0.5 for other genes) is applied last.
The top 10 keep one hypothesis per gene. Rankings are reported **with and without** the prior.

**Results**

| | BUB1B rank, with prior | BUB1B rank, **no prior** | Pair score | Next gene (no prior) |
|---|---|---|---|---|
| v1 (no VEP predictors) | 1 | 11 | 0.143 | 0.245 |
| **v2 (REVEL, AlphaMissense, SpliceAI panel)** | **1** | **1** | **0.317** | 0.258 |

In v1 the missense allele was scored on VEP impact alone (0.19) and capped the pair through `min()`. With AlphaMissense
and REVEL it scores 0.43, and the pair leads without any gene prior.

The rest of the top 10 consists of homozygous splice-site deletions in CTU2, PEX5 and SLC22A1, heterozygous pairs in HLA
genes and other genes, and a mitochondrial missense in MT-CYB. **None has phenotype support:** their Exomiser phenotype
score is 0, so they are below Exomiser's reporting threshold. HLA and splice-boundary deletions are known sources of
calling artifacts.

**Exomiser (no gene prior).**

| Run | #1 | #2 | #3 |
|---|---|---|---|
| 7 HPO (main) | BUB1B, AD, p = 0.0004, combined 0.546 | **BUB1B, AR**, p = 0.0007, phenotype 0.77, variant 0.96 | FANCD2 (AR), combined 0.18 |
| 8 HPO (sensitivity) | BUB1B, AD, p = 0.0005 | BUB1B, AR, p = 0.0006, phenotype 0.79 | FANCD2 (AR) |

The top-10 genes overlap 9/10 between runs. The variant score of 0.96 in the AR model means two qualifying BUB1B alleles,
the same pair. FANCD2 (Fanconi anemia) is the main differential and scores far lower.

## 5. Interpretation of the main candidate

| | Variant 1 | Variant 2 |
|---|---|---|
| Position (GRCh38) | chr15:40209701 T>G | chr15:40220612 T>G |
| HGVS (ENST00000287598.11) | c.2210T>G p.(Leu737\*) | c.3006T>G p.(Asn1002Lys) |
| Location | exon 17 of 23; 747 nt upstream of the last exon–exon junction | exon 23 (last); BUBR1 kinase domain (766–1050) |
| Max. population frequency | 0.0100 % (gnomAD exomes, NFE) | 0.00009 % (gnomAD exomes, NFE) |
| ClinVar | Pathogenic/Likely pathogenic (2 stars) | not interpreted |
| In-silico | — | AlphaMissense 0.92; REVEL 0.47 |
| SpliceAI (max Δ) | 0.03 (no predicted splicing effect) | 0.02 (no predicted splicing effect) |
| Exomiser ACMG | Pathogenic | Uncertain significance |
| Phase | unknown | |

Frequencies are Exomiser's maximum population frequency, expressed as a percentage.

ACMG/AMP (Richards et al. 2015, with ClinGen SVI updates):

- **Variant 1:** PVS1, because loss of function is the MVA1 mechanism and the premature stop lies 747 nt upstream of the
  last exon–exon junction, so NMD is expected. Even if the transcript escaped NMD, the truncated protein would lack the
  entire kinase domain. Also PM2_Supporting and ClinVar P/LP with 2 stars. → **Pathogenic.**
- **Variant 2:** PM2_Supporting; PP3 based on AlphaMissense (0.92). REVEL (0.47) falls in ClinGen's indeterminate range
  (0.291–0.643; Pejaver et al. 2022), so it does not add evidence either way. Asn1002 lies in the kinase domain, where the missense alleles of
  the original MVA1 families cluster (Hanks et al. 2004). → **Uncertain significance.** With PM3 (*trans* configuration
  confirmed) it would reach **likely pathogenic**.
- **PP4:** the phenotype (rhabdomyosarcoma, growth restriction, prematurity, small for gestational age) is concordant with
  MVA1, in which BUB1B patients have a high childhood cancer risk, including rhabdomyosarcoma (Hanks et al. 2004).

The genotype also fits the biology. Complete biallelic loss of BUBR1 is likely lethal, and MVA1 patients typically carry
one null allele plus one allele with residual function, as a kinase-domain missense on the second allele would be.

## 6. EPCR

- **Rows 2–10:** EPCR from a softmax (T = 0.1) over the top-10 hypothesis scores.
- **Row 1 (ADR-011):** the BUB1B pair is set to **0.85**.
- **For:** first with and without prior in our score and in Exomiser; robust to the HPO sensitivity analysis; a pathogenic
  nonsense allele; a deleterious kinase-domain missense; concordant phenotype.
- **Against:** unknown phase, missense classified as VUS without PM3, and no SV analysis.

## 7. Secondary findings

None reported.

## 8. Limitations

- **Phase.** There are no parental data or alignments, and the two variants are **10.9 kb apart**. Short-read phasing
  could not link them even with a BAM. Phase is "unknown" for every pair, and PM3 is not applied.
- **Structural variants.** No SV/CNV or mobile-element insertion analysis. A published BUB1B MVA case carried an intronic
  Alu insertion.
- **SpliceAI** covers only the 29-gene panel, so the splicing rescue in our funnel does not act genome-wide. Exomiser does
  include SpliceAI genome-wide. CADD was not used.
- **Weight renormalization** is per run, not per variant. A nonsense variant does not benefit from missense predictors
  whose weights still count in the denominator. A per-variant scheme is a planned improvement.
- **Exomiser preset:** no REMM, and the phenotype filter (HiPhive ≥ 0.501) restricts its output to genes with phenotype
  support.

## 9. LLM use and data handling

**Anthropic Claude Pro/Max subscription (Claude Code, VS Code extension), model Claude Opus 5.5; model-training opt-out
enabled for the whole project; no feedback (ratings) provided.** This configuration follows the organizers' updated
guidance in Discussion #2, which allows consumer-tier accounts with training opt-out and no feedback.

The assistant wrote and tested code on synthetic fixtures. It also read:

- guard-validated aggregates in `outputs/` (QC summary, funnel, gene rankings, top-10 hypotheses);
- header metadata and aggregate counts;
- the HPO terms;
- the two named candidate variants, which also appear in this submission.

Genotype-level data (VCF/FASTQ contents, read data, per-variant tables in `work/`) was never shared with it.

Two incidents occurred:

1. An Exomiser error message pasted during debugging contained the sample identifier (no genotypes). The pipeline now
   masks the identifier in all error output.
2. The scaffold's "sample-free" VCF header (used for synthetic fixtures) still contained the identifier and file paths in
   `##GATKCommandLine` lines. This was detected before any commit, and fixtures now keep only structural header lines.

All real-data steps (`make real-*`) were run by the participant locally. Data paths and the sample identifier live in an
untracked `config/local.yaml`.

## 10. Reproducibility

- **Repository:** URL and commit above.
- **Environment:** `environment.yml` (conda).
- **Configuration:** `config/config.yaml`, with Exomiser preset and EPCR override in `config/`.
- **One-time setup:** `scripts/05_vep_plugins.sh`, `scripts/06_spliceai_panel.sh`.
- **Steps:** `make real-qc → real-normalize → real-annotate → real-exomiser → real-prioritize →
  real-submission EPCR=config/epcr_overrides.csv` (`real-phase` is not applicable without alignments).
- **Traceability:** each number in this report comes from a run note (`docs/wiki/corridas/`) and the commit above.

## Acknowledgment

"This work was made possible through the Hackathon, organized by Sage Bionetworks in partnership with the MVA
Society, Hugging Face, and BEACON (The Benchmarking, Evaluation, and Assessment Consortium for Science), with prize
sponsorship from AWS and Anthropic. We are deeply grateful to the child and their family who generously contributed
their data and their story to advance research into this rare disease. We acknowledge their trust in making this
Hackathon possible."

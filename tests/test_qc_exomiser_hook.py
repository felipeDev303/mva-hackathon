import importlib.util

import pandas as pd

from mva import REPO_ROOT
from mva.exomiser import build_analysis, summarize_genes
from mva.qc import parse_bcftools_stats, parse_header

STATS = """# SN	[2]id	[3]key	[4]value
SN	0	number of samples:	1
SN	0	number of records:	5012345
SN	0	number of SNPs:	4200000
SN	0	number of indels:	800000
SN	0	number of multiallelic sites:	12000
TSTV	0	2800000	1400000	2.00	2700000	1350000	2.00
PSC	0	SYNTH01	0	1900000	3100000	4200000	800000	30.5	0	0	0
"""


def test_parse_bcftools_stats():
    s = parse_bcftools_stats(STATS)
    assert s["n_snps"] == 4_200_000 and s["ts_tv"] == 2.0
    assert s["het_hom_ratio"] == round(3_100_000 / 1_900_000, 3)


def test_parse_header_detects_grch38():
    h = parse_header("##reference=file:///GRCh38.fa\n##contig=<ID=chr1,length=248956422>\n")
    assert h["build_from_chr1_length"] == "GRCh38" and h["chr_prefix"] is True


def test_exomiser_build_analysis_injects_fields():
    preset = {"analysis": {"genomeAssembly": "hg19", "vcf": None, "hpoIds": [], "steps": [{"x": 1}]},
              "outputOptions": {"outputFormats": ["HTML"]}}
    a = build_analysis(preset, "work/n.vcf.gz", "GRCh38", ["HP:0000252"])
    assert a["analysis"]["genomeAssembly"] == "hg38"
    assert a["analysis"]["hpoIds"] == ["HP:0000252"] and a["analysis"]["steps"] == [{"x": 1}]


def test_exomiser_summary_drops_variant_columns():
    df = pd.DataFrame({"#RANK": [2, 1], "GENE_SYMBOL": ["A", "B"], "EXOMISER_GENE_COMBINED_SCORE": [0.1, 0.9],
                       "EXOMISER_GENE_PHENO_SCORE": [0.2, 0.8], "CONTRIBUTING_VARIANTS": ["x", "y"]})
    s = summarize_genes(df, 50)
    assert list(s["GENE_SYMBOL"]) == ["B", "A"] and "CONTRIBUTING_VARIANTS" not in s.columns


def _hook():
    spec = importlib.util.spec_from_file_location("hook", REPO_ROOT / ".claude" / "hooks" / "data_boundary.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.blocked_reason


def test_hook_blocks_red_zone():
    br = _hook()
    assert br("Bash", {"command": "head -n 5 work/annotated.tsv"})
    assert br("Bash", {"command": "zcat data/WGS_x.vcf.gz | less"})
    assert br("Bash", {"command": "make real-annotate"})
    assert br("Read", {"file_path": "/home/f/mva-hackathon/data/x.vcf.gz"})
    assert br("Grep", {"pattern": "BUB1B", "path": "work/"})


def test_hook_allows_green_zone():
    br = _hook()
    assert br("Bash", {"command": "make test"}) is None
    assert br("Read", {"file_path": "outputs/top_pairs.tsv"}) is None
    assert br("Read", {"file_path": "fixtures/synthetic.vcf"}) is None
    assert br("Bash", {"command": "pytest -q tests/test_guard.py"}) is None

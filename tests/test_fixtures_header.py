from mva.fixtures import main

REAL_LIKE = """##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##GATKCommandLine=<ID=HaplotypeCaller,CommandLine="HaplotypeCaller --input /data/REALID99.bam --sample-name REALID99">
##source=HaplotypeCaller
##reference=file:///refs/GRCh38.fa
##contig=<ID=chr7,length=159345973>
"""


def test_fixtures_keep_only_structural_header_lines(tmp_path):
    h = tmp_path / "header_nosamples.txt"
    h.write_text(REAL_LIKE, encoding="utf-8")
    main(["--header", str(h), "--out", str(tmp_path / "fx"), "--n-noise", "10"])
    vcf = (tmp_path / "fx" / "synthetic.vcf").read_text(encoding="utf-8")
    assert "REALID99" not in vcf and "GATKCommandLine" not in vcf and "/data/" not in vcf
    assert "##contig=<ID=chr7" in vcf

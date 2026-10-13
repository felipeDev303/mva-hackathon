#!/usr/bin/env python3
"""Hook PreToolUse de Claude Code: frontera de datos del paciente.

Bloquea (exit 2, el mensaje vuelve al modelo) cualquier llamada que:
  * lea, busque o edite dentro de data/ o work/,
  * mencione archivos genómicos (.vcf/.vcf.gz/.bam/.cram/.fastq) fuera de fixtures/,
  * ejecute objetivos de make que corren sobre datos reales.

Las reglas `deny` de settings.json cubren Read/Edit; este hook cubre Bash, Grep
y Glob, que esas reglas no alcanzan. No es infalible: el humano sigue siendo
quien corre los pasos sobre datos reales.
"""

import json
import re
import sys

RED_DIRS = re.compile(r"(^|[\s'\"=/(:])(\.?/)?(data|work)(/|\s|$|['\"])")
GENOMIC = re.compile(r"[\w./-]*\.(vcf(\.gz)?|bcf|bam|cram|fastq(\.gz)?|fq\.gz)\b", re.I)
REAL_TARGETS = re.compile(r"\bmake\s+(.*\s)?(qc|normalize|annotate|exomiser|prioritize|phase|submission|real|all)\b")
HF_DOWNLOAD = re.compile(r"\b(hf|huggingface-cli)\s+download\b|snapshot_download|hf_hub_download")


def blocked_reason(tool: str, inp: dict) -> str | None:
    texts = []
    if tool == "Bash":
        cmd = inp.get("command", "")
        if REAL_TARGETS.search(cmd):
            return "objetivo de make sobre datos reales: lo corre el humano (make real-*)."
        if HF_DOWNLOAD.search(cmd):
            return "descarga del dataset gated: la hace el humano."
        texts.append(cmd)
    else:
        for k in ("file_path", "path", "pattern", "notebook_path", "glob"):
            if inp.get(k):
                texts.append(str(inp[k]))
    for t in texts:
        if RED_DIRS.search(t):
            return "toca data/ o work/ (zona roja)."
        for m in GENOMIC.finditer(t):
            if "fixtures/" not in m.group(0):
                return f"menciona un archivo genómico fuera de fixtures/: {m.group(0)}"
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    reason = blocked_reason(payload.get("tool_name", ""), payload.get("tool_input", {}) or {})
    if reason:
        print(f"BLOQUEADO por la política de datos del hackathon: {reason} "
              "Trabaja con fixtures/ y lee solo outputs/ después de `make guard`.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

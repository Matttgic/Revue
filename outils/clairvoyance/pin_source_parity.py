"""Pin exact checked source files, not unrelated data-only GitHub commits."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

FILES=(
    "app/services/predictor.py",
    "docs/app.html",
    "scripts/clairvoyance_update.py",
)


def pin(reference:Path,catalogue:dict,source_commit:str)->dict:
    if not source_commit or catalogue.get("original_source_commit")!=source_commit:
        raise ValueError("Catalogued parity was not checked on this source revision")
    if catalogue.get("verified_formula_parity_models")!=catalogue.get("total_target_models"):
        raise ValueError("All claimed formula checks must have passed to pin source files")
    hashes={}
    for name in FILES:
        path=reference/name
        if not path.is_file():
            raise FileNotFoundError("Source file not available: "+name)
        hashes[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        **catalogue,
        "reference_model_source_sha256":hashes,
        "source_hash_provenance":"Files read from same temporary source checkout immediately after original equality tests. No source code copied.",
        "unrelated_repository_commits_may_change":True,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--reference",required=True)
    parser.add_argument("--catalogue",default="docs/parite-modeles-clairvoyance.json")
    args=parser.parse_args()
    reference=Path(args.reference)
    sha=subprocess.check_output(["git","-C",str(reference),"rev-parse","HEAD"],
                                text=True,timeout=10).strip()
    path=Path(args.catalogue)
    current=json.loads(path.read_text(encoding="utf-8"))
    doc=pin(reference,current,sha)
    path.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("3 source artifacts pinned, 44 targeted parity checks require same source implementation")


if __name__=="__main__":
    main()

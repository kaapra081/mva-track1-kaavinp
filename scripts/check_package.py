#!/usr/bin/env python3
"""Check report/CSV consistency and create a path-independent package manifest."""
import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from validate_submission import validate_file

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / 'submission/kaavinp_exomiser15-context-review.csv'
REPORT = ROOT / 'submission/kaavinp_track1_report.md'
PDF = ROOT / 'submission/kaavinp_track1_report.pdf'
ALLOWED_ROOTS = {'scripts', 'tests', 'config', 'docs', 'submission', 'results'}
ALLOWED_TOP = {'README.md', 'LICENSE.md', 'requirements.txt', '.gitignore', '.gitattributes', 'MANIFEST.sha256'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compare-csv', type=Path, help='Optional local frozen reviewed CSV; path is not published')
    args = parser.parse_args()
    rows, keys = validate_file(CSV)
    text = REPORT.read_text()
    if 'author: "Kaavin Prasanna"' not in text:
        raise ValueError('Report author does not match the requested display name')
    table = [line for line in text.splitlines() if re.match(r'^\| [0-9]+ \|', line)]
    if len(table) != len(rows):
        raise ValueError('Report candidate table size mismatch')
    for row, line in zip(rows, table):
        for suffix in ('1', '2'):
            if row['chrom_' + suffix]:
                allele = f"{row['chrom_'+suffix]}:{row['pos_'+suffix]} {row['ref_'+suffix]}>{row['alt_'+suffix]}"
                if allele not in line:
                    raise ValueError('Report candidate identity mismatch')
        if row['epcr'] not in line:
            raise ValueError('Report EPCR mismatch')
    pdf = PDF.read_bytes()
    if not pdf.startswith(b'%PDF-') or b'%%EOF' not in pdf[-1024:]:
        raise ValueError('PDF structure marker missing')
    comparison = None
    if args.compare_csv:
        comparison = CSV.read_bytes() == args.compare_csv.read_bytes()
        if not comparison:
            raise ValueError('Packaged CSV differs from the reviewed frozen CSV')
    receipt = {'status': 'PASS', 'rows': len(rows), 'unique_alleles': len(set().union(*keys)),
               'report_table_matches_csv': True, 'pdf_structure_markers_present': True,
               'frozen_reviewed_csv_byte_identical': comparison, 'official_score_measured': False,
               'repository_owner': 'kaapra081', 'submitter': 'kaavinp', 'report_author': 'Kaavin Prasanna',
               'method': 'exomiser15-context-review', 'analysis_rerun_for_packaging': False}
    (ROOT / 'results/package_verification.json').write_text(json.dumps(receipt, indent=2)+'\n')
    files = []
    forbidden_suffixes = {'.vcf', '.bcf', '.bam', '.cram', '.jsonl', '.parquet', '.jar', '.log', '.docx'}
    for path in sorted(ROOT.rglob('*')):
        rel = path.relative_to(ROOT)
        if any(part in {'.git', '__pycache__', '.venv', 'work'} for part in rel.parts):
            continue
        if path.is_symlink():
            raise ValueError(f'Symlink excluded from release: {rel}')
        if not path.is_file() or rel.as_posix() == 'MANIFEST.sha256':
            continue
        if not ((len(rel.parts) == 1 and rel.name in ALLOWED_TOP) or rel.parts[0] in ALLOWED_ROOTS):
            raise ValueError(f'Unreviewed package path: {rel}')
        if path.suffix in forbidden_suffixes or path.name.endswith(('.vcf.gz', '.fa.gz', '.fna.gz')):
            raise ValueError(f'Private/heavy input excluded from release: {rel}')
        if path.suffix != '.pdf':
            content = path.read_text()
            credential_pattern = r'gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{24,}|BEGIN ' + r'PRIVATE KEY'
            if ('/' + 'Users/') in content or re.search(credential_pattern, content):
                raise ValueError(f'Private path or credential pattern in {rel}')
        files.append((rel.as_posix(), hashlib.sha256(path.read_bytes()).hexdigest()))
    (ROOT / 'MANIFEST.sha256').write_text(''.join(f'{digest}  {name}\n' for name, digest in files))
    print(json.dumps({'status': 'PASS', 'manifest_files': len(files), **receipt}, indent=2))


if __name__ == '__main__':
    main()

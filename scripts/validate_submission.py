#!/usr/bin/env python3
"""Validate schema, optional exact native membership, and local VCF/reference evidence."""
import argparse
import csv
import json
import math
import re
from pathlib import Path
from build_submission import FIELDS, canonical_contig, load_models


def validate_rows(rows):
    if not 1 <= len(rows) <= 10:
        raise ValueError('Expected 1–10 rows')
    keys, scores = [], []
    for row in rows:
        if set(row) != set(FIELDS) or row['proband_id'] != 'PROBAND01':
            raise ValueError('Invalid columns or proband')
        members = []
        for suffix in ('1', '2'):
            fields = [row[f'{name}_{suffix}'] for name in ('chrom', 'pos', 'ref', 'alt')]
            if suffix == '2' and not any(fields):
                continue
            if not all(fields):
                raise ValueError('Incomplete allele fields')
            chrom, pos, ref, alt = fields
            if canonical_contig(chrom) != chrom or not re.fullmatch(r'[1-9][0-9]*', pos):
                raise ValueError('Noncanonical chromosome or position')
            if not re.fullmatch('[ACGTN]+', ref) or not re.fullmatch('[ACGTN]+', alt) or ref == alt:
                raise ValueError('Invalid REF/ALT')
            members.append((chrom, int(pos), ref, alt))
        if len(set(members)) != len(members):
            raise ValueError('Repeated allele within pair')
        key = frozenset(members)
        if key in keys:
            raise ValueError('Duplicate allele-set hypothesis')
        keys.append(key)
        score = float(row['epcr'])
        if not math.isfinite(score) or not 0 < score <= 1:
            raise ValueError('Invalid EPCR')
        scores.append(score)
        if row['finding_type'] not in {'primary', 'secondary'}:
            raise ValueError('Invalid finding type')
    if any(a <= b for a, b in zip(scores, scores[1:])):
        raise ValueError('This export requires strictly descending, untied EPCR')
    return keys


def validate_file(path):
    with Path(path).open(newline='') as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FIELDS:
            raise ValueError('Header does not exactly match the submission schema')
        rows = list(reader)
    return rows, validate_rows(rows)


def native_membership(keys, path):
    native = {frozenset((canonical_contig(c), p, r, a) for c, p, r, a in m['variants'])
              for m in load_models(path)}
    if any(key not in native for key in keys):
        raise ValueError('A row is not an exact native model')


def contig_alias(chrom, available):
    aliases = (chrom, chrom.removeprefix('chr'))
    matches = [c for c in aliases if c in available]
    if len(matches) != 1:
        raise ValueError('Missing or ambiguous reference/VCF contig alias')
    return matches[0]


def reconcile(keys, vcf_path, reference_path):
    import pysam
    results = []
    with pysam.VariantFile(str(vcf_path)) as vcf, pysam.FastaFile(str(reference_path)) as fasta:
        if len(vcf.header.samples) != 1:
            raise ValueError('Expected exactly one VCF sample')
        sample = next(iter(vcf.header.samples))
        for chrom, pos, ref, alt in sorted(set().union(*keys)):
            vc = contig_alias(chrom, vcf.header.contigs)
            fc = contig_alias(chrom, fasta.references)
            records = [r for r in vcf.fetch(vc, pos-1, pos)
                       if r.pos == pos and r.ref == ref and alt in (r.alts or ())]
            if len(records) != 1:
                raise ValueError('Expected one exact indexed VCF match')
            record = records[0]
            call = record.samples[sample]
            genotype = call.get('GT') or ()
            alt_index = list(record.alts).index(alt) + 1
            if not genotype or None in genotype or alt_index not in genotype:
                raise ValueError('ALT not supported by a complete called genotype')
            if fasta.fetch(fc, pos-1, pos-1+len(ref)).upper() != ref or 'PASS' not in record.filter:
                raise ValueError('Reference mismatch or non-PASS source record')
            if any(call.get(k) is None for k in ('DP', 'GQ', 'AD')):
                raise ValueError('Required genotype QC field missing')
            results.append({'identity': [chrom, pos, ref, alt], 'exact_match': True,
                            'carried_alt': True, 'reference_match': True, 'explicit_pass': True,
                            'qc_fields_present': True})
    return results


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('csv', type=Path)
    p.add_argument('--native', type=Path)
    p.add_argument('--vcf', type=Path)
    p.add_argument('--reference', type=Path)
    p.add_argument('--report', type=Path)
    args = p.parse_args()
    if bool(args.vcf) != bool(args.reference):
        p.error('--vcf and --reference must be used together')
    rows, keys = validate_file(args.csv)
    if args.native:
        native_membership(keys, args.native)
    checks = reconcile(keys, args.vcf, args.reference) if args.vcf else None
    report = {'status': 'PASS', 'rows': len(rows), 'native_membership_checked': bool(args.native),
              'unique_alleles': len(set().union(*keys)), 'allele_checks': checks,
              'official_score_measured': False,
              'limits': 'Allele presence/QC is not confirmation of causality, phase or disease mechanism.'}
    text = json.dumps(report, indent=2) + '\n'
    if args.report:
        if args.report.exists():
            p.error('Refusing to overwrite report')
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text)
    print(text)


if __name__ == '__main__':
    main()

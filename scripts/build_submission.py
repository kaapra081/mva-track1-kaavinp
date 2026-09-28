#!/usr/bin/env python3
"""Reproduce my explicit case review from native Exomiser JSONL."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ['proband_id', 'chrom_1', 'pos_1', 'ref_1', 'alt_1',
          'chrom_2', 'pos_2', 'ref_2', 'alt_2', 'epcr', 'finding_type', 'notes']


def canonical_contig(value):
    value = str(value)
    bare = value[3:] if value.startswith('chr') else value
    if bare not in {str(i) for i in range(1, 23)} | {'X', 'Y', 'M', 'MT'}:
        raise ValueError(f'Unsupported contig: {value}')
    return 'chr' + bare


def finite(value, optional=False):
    if value is None and optional:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('A contributing model score is missing or non-finite')
    return float(value)


def load_models(path):
    models = []
    with Path(path).open() as handle:
        for line in handle:
            if not line.strip():
                continue
            gene = json.loads(line)
            for score in gene.get('geneScores', []):
                variants = score.get('contributingVariants') or []
                if not variants:
                    continue
                alleles = sorted((canonical_contig(v['contigName'])[3:], int(v['start']),
                                  v['ref'].upper(), v['alt'].upper()) for v in variants)
                diseases = []
                for match in score.get('compatibleDiseaseMatches') or []:
                    raw = match.get('model') or {}
                    disease = raw.get('disease') or raw
                    if disease.get('diseaseId'):
                        diseases.append({'id': disease['diseaseId'], 'name': disease.get('diseaseName'),
                                         'score': finite(match.get('score'))})
                diseases.sort(key=lambda d: (-d['score'], d['id'], str(d['name'])))
                models.append({'gene': gene['geneSymbol'], 'mode': score['modeOfInheritance'],
                               'variants': alleles, 'diseases': diseases,
                               'combined': finite(score.get('combinedScore')),
                               'phenotype': finite(score.get('phenotypeScore'), optional=True),
                               'variant': finite(score.get('variantScore'))})
    return models


def identity(model):
    alleles = ';'.join(f'{c}:{p}:{r}>{a}' for c, p, r, a in model['variants'])
    return f"{model['gene']}|{model['mode']}|{alleles}"


def score_key(model):
    # Preserve null in the audit; use the original ordering fallback only for sorting.
    return (-model['combined'], -(model['phenotype'] or 0), -model['variant'],
            model['gene'], model['mode'], identity(model))


def adjudicate(model, policy):
    ids = {d['id'] for d in model['diseases']}
    if (model['gene'] == policy['primary_gene'] and model['mode'] == policy['primary_mode']
            and len(model['variants']) == 2 and ids.intersection(policy['primary_disease_ids'])):
        return 0, 'PRIMARY_CONTEXT_SUPPORTED'
    if (model['gene'] == policy['excluded_gene'] and model['mode'] == policy['excluded_mode']
            and policy['excluded_disease_id'] in ids):
        return 99, 'EXCLUDED_CONTEXT_MISMATCH'
    return (1, 'ALTERNATIVE_CONTEXT_SUPPORTED') if ids else (98, 'NO_COMPATIBLE_DISEASE_CONTEXT')


def rank_models(models, policy):
    models = [dict(m) for m in models]
    for rank, model in enumerate(sorted(models, key=score_key), 1):
        model['native_rank'] = rank
        model['priority'], model['context'] = adjudicate(model, policy)
    selected, seen = [], set()
    for model in sorted(models, key=lambda m: (m['priority'], *score_key(m))):
        if model['priority'] > 1:
            continue
        key = tuple(sorted(model['variants']))
        if len(key) not in (1, 2) or len(set(key)) != len(key):
            raise ValueError('Unsupported or repeated contributing alleles')
        if key in seen:
            continue
        seen.add(key)
        selected.append(model)
        if len(selected) == policy['maximum_rows']:
            break
    if not selected:
        raise ValueError('No admissible models')
    return selected, models


def make_rows(models, policy):
    rows = []
    for rank, m in enumerate(models, 1):
        disease = '; '.join(f"{d['id']} {d['name']} score={d['score']:.6f}" for d in m['diseases'][:2])
        phase = 'SINGLE_ALLELE' if len(m['variants']) == 1 else 'UNPHASED_OR_INCOMPLETE'
        notes = '; '.join([f'repair_rank={rank}', f"gene={m['gene']}", f"mode={m['mode']}",
                          'model_membership=EXOMISER_NATIVE', f"context_status={m['context']}",
                          f"native_model_score_rank={m['native_rank']}",
                          f"native_combined_score={m['combined']:.12g}",
                          f"native_phenotype_score={m['phenotype']:.12g}" if m['phenotype'] is not None else 'native_phenotype_score=unavailable',
                          f"native_variant_score={m['variant']:.12g}", f'disease_context={disease}',
                          f'phase={phase}', 'epcr_policy=ordinal_context_rank_not_calibrated_probability',
                          'hypothesis_only=true', 'no_de_novo_inference=true'])
        row = dict.fromkeys(FIELDS, '')
        row.update(proband_id='PROBAND01', epcr=f"{1-(rank-1)/policy['epcr_denominator']:.6f}",
                   finding_type='primary' if rank == 1 else 'secondary', notes=notes)
        for i, (chrom, pos, ref, alt) in enumerate(m['variants'], 1):
            row.update({f'chrom_{i}': canonical_contig(chrom), f'pos_{i}': str(pos),
                        f'ref_{i}': ref, f'alt_{i}': alt})
        rows.append(row)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--policy', type=Path, default=ROOT / 'config/adjudication.json')
    parser.add_argument('--audit', type=Path, help='Optional LOCAL complete model audit; do not publish it')
    args = parser.parse_args()
    if args.output.exists() or (args.audit and args.audit.exists()):
        parser.error('Refusing to overwrite an existing artifact')
    policy = json.loads(args.policy.read_text())
    selected, inventory = rank_models(load_models(args.native), policy)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(make_rows(selected, policy))
    if args.audit:
        args.audit.parent.mkdir(parents=True, exist_ok=True)
        args.audit.write_text(json.dumps(inventory, indent=2) + '\n')
    print(json.dumps({'models': len(inventory), 'rows': len(selected),
                      'csv_sha256': hashlib.sha256(args.output.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()

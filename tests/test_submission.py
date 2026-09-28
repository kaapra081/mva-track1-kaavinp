"""Synthetic software checks; no patient fixtures or clinical accuracy claims."""
import copy
import json
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_submission import FIELDS, ROOT, canonical_contig, make_rows, rank_models
from validate_submission import validate_rows
from run_exomiser import hpo_terms


def model(gene='TEST', mode='AUTOSOMAL_DOMINANT', variants=None, score=0.5, ids=('OMIM:1',)):
    return {'gene': gene, 'mode': mode, 'variants': sorted(variants or [('1', 100, 'A', 'G')]),
            'combined': score, 'phenotype': 0.5, 'variant': 0.5,
            'diseases': [{'id': x, 'name': 'Synthetic', 'score': 0.5} for x in ids]}


class SubmissionTests(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads((ROOT / 'config/adjudication.json').read_text())
        self.models = [model(), model('OTHER', variants=[('2', 200, 'C', 'T')], score=0.4)]
        self.rows = make_rows(rank_models(self.models, self.policy)[0], self.policy)

    def test_valid_control(self):
        self.assertEqual(len(validate_rows(self.rows)), 2)

    def test_private_hpo_input_comments_and_invalid_values(self):
        self.assertEqual(hpo_terms('# source note\nHP:0000001\n\nHP:0000001\n'), ['HP:0000001'])
        for text in ('# comment only', 'HP:123', 'OMIM:123456', 'HP:0000001 extra'):
            with self.assertRaises(ValueError):
                hpo_terms(text)

    def test_contig_mapping_and_idempotence(self):
        for c in ['1', '22', 'X', 'Y', 'M', 'MT']:
            self.assertEqual(canonical_contig(canonical_contig(c)), 'chr' + c)
        for c in ['0', '23', 'chrchr1', 'unplaced', '01']:
            with self.assertRaises(ValueError):
                canonical_contig(c)

    def test_invalid_rows_rejected(self):
        for field, value in [('chrom_1', '1'), ('chrom_1', 'garbage'), ('pos_1', '0'),
                             ('pos_1', '1.5'), ('alt_1', 'INVALID'), ('alt_1', 'A'),
                             ('epcr', 'NaN'), ('epcr', 'inf'), ('epcr', '0'),
                             ('finding_type', 'invalid')]:
            with self.subTest(field=field, value=value):
                rows = copy.deepcopy(self.rows)
                rows[0][field] = value
                with self.assertRaises(ValueError):
                    validate_rows(rows)

    def test_partial_and_repeated_pair_rejected(self):
        rows = copy.deepcopy(self.rows)
        rows[0]['chrom_2'] = 'chr1'
        with self.assertRaises(ValueError):
            validate_rows(rows)
        for name in ('chrom', 'pos', 'ref', 'alt'):
            rows[0][name + '_2'] = rows[0][name + '_1']
        with self.assertRaises(ValueError):
            validate_rows(rows)

    def test_duplicate_pair_reversal_rejected(self):
        first = dict(self.rows[0], chrom_2='chr1', pos_2='200', ref_2='C', alt_2='T')
        second = dict(first, epcr='0.5', finding_type='secondary')
        for name in ('chrom', 'pos', 'ref', 'alt'):
            second[name+'_1'], second[name+'_2'] = first[name+'_2'], first[name+'_1']
        with self.assertRaises(ValueError):
            validate_rows([first, second])

    def test_rank_invariant_to_model_order(self):
        rng = random.Random(7)
        expected = make_rows(rank_models(self.models, self.policy)[0], self.policy)
        for _ in range(30):
            shuffled = list(self.models)
            rng.shuffle(shuffled)
            self.assertEqual(make_rows(rank_models(shuffled, self.policy)[0], self.policy), expected)

    def test_case_policy_is_explicit(self):
        somatic = model('BUB1B', ids=('OMIM:114500',), score=0.99)
        constitutional = model('BUB1B', 'AUTOSOMAL_RECESSIVE',
                               [('15', 100, 'A', 'G'), ('15', 200, 'C', 'T')], ids=('OMIM:257300',))
        selected, audit = rank_models([somatic, constitutional, *self.models], self.policy)
        self.assertEqual(selected[0]['mode'], 'AUTOSOMAL_RECESSIVE')
        self.assertNotIn(somatic['mode'], [m['mode'] for m in selected if m['gene'] == 'BUB1B'])
        self.assertEqual(len(audit), 4)

    def test_contextless_retained_in_audit_not_export(self):
        selected, audit = rank_models([model('UNKNOWN', ids=()), *self.models], self.policy)
        self.assertEqual(len(audit), 3)
        self.assertEqual(len(selected), 2)

    def test_missing_native_phenotype_preserved(self):
        missing = model('UNKNOWN', ids=())
        missing['phenotype'] = None
        selected, audit = rank_models([missing, *self.models], self.policy)
        self.assertEqual(len(selected), 2)
        self.assertIsNone(next(m for m in audit if m['gene'] == 'UNKNOWN')['phenotype'])

    def test_ties_and_excess_rows_rejected(self):
        rows = copy.deepcopy(self.rows)
        rows[1]['epcr'] = rows[0]['epcr']
        with self.assertRaises(ValueError):
            validate_rows(rows)
        with self.assertRaises(ValueError):
            validate_rows(self.rows * 6)


if __name__ == '__main__':
    unittest.main()

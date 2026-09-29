"""Behavioral checks for consequential tensor-shape mistakes in diagrams."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('diagram_shapes', ROOT / 'scripts/check_shapes.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def one(op, a, b, out, **attrs):
    return {'schema_version': 1, 'tensors': {'a': a, 'b': b, 'out': out},
            'operations': [dict(id='op', op=op, inputs=['a', 'b'], output='out', **attrs)]}


class Shapes(unittest.TestCase):
    def test_example(self):
        data = json.loads((ROOT / 'assets/shape-example.json').read_text(encoding='utf-8'))
        self.assertEqual(checker.check_spec(data), ([], []))

    def test_matrix_contraction_error(self):
        errors, _ = checker.check_spec(one('matmul', ['B', 8], [7, 32], ['B', 32]))
        self.assertTrue(errors)

    def test_gate_broadcast_requires_declaration(self):
        data = one('hadamard', ['B', 2], ['B', 1], ['B', 2])
        self.assertTrue(checker.check_spec(data)[0])
        data['operations'][0]['broadcast'] = True
        self.assertEqual(checker.check_spec(data), ([], []))

    def test_hadamard_is_not_matrix_multiplication(self):
        data = one('matmul', ['B', 2], ['B', 1], ['B', 2])
        self.assertTrue(checker.check_spec(data)[0])

    def test_wrong_concat_axis(self):
        data = one('concat', ['B', 12, 64], ['B', 4, 64], ['B', 16, 64], axis=2)
        self.assertTrue(checker.check_spec(data)[0])

    def test_distinct_batch_symbols_are_not_assumed_equal(self):
        errors, reviews = checker.check_spec(one('add', ['B', 2], ['N', 2], ['B', 2]))
        self.assertFalse(errors)
        self.assertTrue(reviews)

    def test_unsupported_einsum_needs_review(self):
        errors, reviews = checker.check_spec(one('einsum', ['B', 12, 8], [12, 8, 64], ['B', 12, 64]))
        self.assertFalse(errors)
        self.assertTrue(reviews)

    def test_reshape_cannot_drop_elements(self):
        data = {'schema_version': 1, 'tensors': {'a': ['B', 4, 32], 'b': ['B', 64]},
                'operations': [{'id': 'flat', 'op': 'reshape', 'inputs': ['a'], 'output': 'b'}]}
        self.assertTrue(checker.check_spec(data)[0])

    def test_transpose_preserves_axes(self):
        data = {'schema_version': 1, 'tensors': {'a': ['B', 4, 32], 'b': [4, 'B', 32]},
                'operations': [{'id': 'permute', 'op': 'transpose', 'inputs': ['a'], 'output': 'b', 'axes': [1, 0, 2]}]}
        self.assertEqual(checker.check_spec(data), ([], []))

    def test_known_incompatible_batch_broadcast(self):
        self.assertTrue(checker.check_spec(one('matmul', [3, 4, 8], [5, 8, 2], [3, 4, 2]))[0])

    def test_scale_requires_scalar(self):
        self.assertTrue(checker.check_spec(one('scale', ['B', 2], ['B', 1], ['B', 2]))[0])

    def test_missing_and_duplicate_ids(self):
        data = one('add', [2], [2], [2])
        data['operations'].append(data['operations'][0].copy())
        self.assertTrue(checker.check_spec(data)[0])
        data = one('add', [2], [2], [2])
        data['operations'][0]['inputs'] = ['missing', 'b']
        self.assertTrue(checker.check_spec(data)[0])


if __name__ == '__main__':
    unittest.main()

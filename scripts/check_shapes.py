#!/usr/bin/env python3
"""Check declared diagram tensor operations. Python 3.10+, standard library only.

This is neither a model tracer nor a theorem prover. Symbolic ambiguity and
unsupported operations are reported as REVIEW, never silently certified.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from math import prod
from pathlib import Path
import sys


class ShapeError(ValueError):
    pass


def valid_shape(value):
    return isinstance(value, list) and all(
        (type(d) is int and d > 0) or (isinstance(d, str) and bool(d.strip()))
        for d in value
    )


def equal_dim(a, b, review):
    if a == b:
        return
    if type(a) is int and type(b) is int:
        raise ShapeError(f'incompatible dimensions: {a} vs {b}')
    review.append(f'symbolic equality not established: {a} = {b}')


def equal_shape(a, b, review):
    if len(a) != len(b):
        raise ShapeError(f'rank mismatch: {a} vs {b}')
    for da, db in zip(a, b):
        equal_dim(da, db, review)


def broadcast(a, b, review):
    n = max(len(a), len(b))
    aa, bb = [1] * (n-len(a)) + a, [1] * (n-len(b)) + b
    out = []
    for da, db in zip(aa, bb):
        if da == 1:
            out.append(db)
        elif db == 1 or da == db:
            out.append(da)
        elif type(da) is int and type(db) is int:
            raise ShapeError(f'cannot broadcast {a} with {b}')
        else:
            review.append(f'unknown broadcast compatibility: {da}, {db}')
            return None
    return out


def axis_index(axis, rank):
    if type(axis) is not int or not -rank <= axis < rank:
        raise ShapeError(f'invalid axis {axis!r} for rank {rank}')
    return axis % rank


def factors(shape):
    return (prod(d for d in shape if type(d) is int),
            Counter(d for d in shape if isinstance(d, str)))


def infer(op, shapes, target, review):
    name = op.get('op')
    if not isinstance(name, str):
        raise ShapeError('op must be a string')
    counts = {'add': 2, 'hadamard': 2, 'matmul': 2, 'scale': 2,
              'reshape': 1, 'reduce': 1, 'transpose': 1}
    if name in counts and len(shapes) != counts[name]:
        raise ShapeError(f'{name} expects {counts[name]} inputs')
    if name in ('add', 'hadamard'):
        a, b = shapes
        if 'broadcast' in op and type(op['broadcast']) is not bool:
            raise ShapeError('broadcast must be a boolean')
        if op.get('broadcast', False):
            return broadcast(a, b, review)
        equal_shape(a, b, review)
        return a
    if name == 'matmul':
        a, b = shapes
        if min(len(a), len(b)) < 2:
            raise ShapeError('matmul supports rank >= 2; label vector dot separately')
        equal_dim(a[-1], b[-2], review)
        batch = broadcast(a[:-2], b[:-2], review)
        return None if batch is None else batch + [a[-2], b[-1]]
    if name == 'scale':
        if shapes[1] != []:
            raise ShapeError('scale expects [tensor, scalar]; scalar shape is []')
        return shapes[0]
    if name == 'concat':
        if len(shapes) < 2:
            raise ShapeError('concat expects at least two inputs')
        rank = len(shapes[0])
        axis = axis_index(op.get('axis'), rank)
        if any(len(s) != rank for s in shapes):
            raise ShapeError('concat ranks must agree')
        for shape in shapes[1:]:
            for i, d in enumerate(shape):
                if i != axis:
                    equal_dim(shapes[0][i], d, review)
        dims = [s[axis] for s in shapes]
        total = sum(dims) if all(type(d) is int for d in dims) else '+'.join(map(str, dims))
        out = shapes[0].copy()
        out[axis] = total
        return out
    if name == 'reduce':
        source = shapes[0]
        axes = op.get('axis')
        axes = axes if isinstance(axes, list) else [axes]
        if not axes:
            raise ShapeError('reduce requires one or more axes')
        axes = [axis_index(a, len(source)) for a in axes]
        if len(set(axes)) != len(axes):
            raise ShapeError('duplicate reduction axes')
        keep = op.get('keepdims', False)
        if type(keep) is not bool:
            raise ShapeError('keepdims must be a boolean')
        return [1 if i in axes else d for i, d in enumerate(source)] if keep else [
            d for i, d in enumerate(source) if i not in axes]
    if name == 'transpose':
        order = op.get('axes')
        rank = len(shapes[0])
        if (not isinstance(order, list) or any(type(a) is not int for a in order)
                or sorted(order) != list(range(rank))):
            raise ShapeError('transpose axes must be a permutation of the source axes')
        return [shapes[0][i] for i in order]
    if name == 'reshape':
        src, dst = factors(shapes[0]), factors(target)
        if src != dst:
            if src[1] == dst[1]:
                raise ShapeError(f'reshape changes element count: {shapes[0]} -> {target}')
            review.append(f'reshape symbolic element count unresolved: {shapes[0]} -> {target}')
        return target
    review.append(f'unsupported operation {name!r}; verify its formula manually')
    return None


def check_spec(spec):
    errors, reviews = [], []
    if not isinstance(spec, dict):
        return ['spec must be an object'], []
    if spec.get('schema_version') != 1:
        errors.append('schema_version must be 1')
    tensors = spec.get('tensors')
    operations = spec.get('operations')
    if not isinstance(tensors, dict) or not tensors:
        errors.append('tensors must be a nonempty object')
    elif any(not isinstance(k, str) or not k or not valid_shape(v)
             for k, v in tensors.items()):
        errors.append('each tensor needs an ID and a shape of positive integers or symbols')
    if not isinstance(operations, list) or not operations:
        errors.append('operations must be a nonempty list')
    if errors:
        return errors, reviews
    seen = set()
    for i, op in enumerate(operations):
        label = f'operation[{i}]'
        try:
            if not isinstance(op, dict):
                raise ShapeError('operation must be an object')
            oid = op.get('id')
            if not isinstance(oid, str) or not oid:
                raise ShapeError('operation requires a nonempty string id')
            label = oid
            if oid in seen:
                raise ShapeError('duplicate operation id')
            seen.add(oid)
            inputs, output = op.get('inputs'), op.get('output')
            if not isinstance(inputs, list) or not inputs or any(not isinstance(x, str) for x in inputs):
                raise ShapeError('inputs must be a nonempty list of tensor IDs')
            if not isinstance(output, str):
                raise ShapeError('output must be a tensor ID')
            missing = [x for x in inputs + [output] if x not in tensors]
            if missing:
                raise ShapeError(f'undefined tensors: {missing}')
            local = []
            inferred = infer(op, [tensors[x] for x in inputs], tensors[output], local)
            if inferred is not None:
                equal_shape(inferred, tensors[output], local)
            reviews.extend(f'{label}: {s}' for s in dict.fromkeys(local))
        except ShapeError as exc:
            errors.append(f'{label}: {exc}')
    return errors, reviews


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('spec', type=Path)
    parser.add_argument('--strict', action='store_true', help='return code 2 if manual reviews remain')
    args = parser.parse_args()
    try:
        spec = json.loads(args.spec.read_text(encoding='utf-8-sig'))
    except (OSError, ValueError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1
    errors, reviews = check_spec(spec)
    for item in errors:
        print(f'ERROR: {item}')
    for item in reviews:
        print(f'REVIEW: {item}')
    print(f'Declared shape check: {len(errors)} error(s), {len(reviews)} manual review(s).')
    print('Scope: tensor declarations only; model semantics and rendered figures are not verified.')
    return 1 if errors else (2 if args.strict and reviews else 0)


if __name__ == '__main__':
    sys.exit(main())

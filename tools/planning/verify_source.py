#!/usr/bin/env python3
"""Verify frozen-source citations and fixtures against local Git objects, without checkout or network."""
import argparse
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='local clone containing the locked iOS commit')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    lock = json.loads((args.root / 'planning/source-lock.json').read_text(encoding='utf-8'))
    sha = lock['source']['commit_sha']
    raw = subprocess.check_output(['git', '-C', str(args.source), 'ls-tree', '-r', '-l', '-z', sha])
    blobs = {}
    trees = set()
    for row in raw.decode('utf-8').split('\0'):
        if row:
            meta, path = row.split('\t', 1)
            _, kind, oid, size = meta.split()
            if kind == 'blob':
                blobs[path] = (oid, int(size))
                trees.update(path[:m.start()] for m in re.finditer('/', path))
    errors = []
    fixtures = {f['path']: (f['git_blob_sha'], f['size_bytes']) for f in lock['fixtures']}
    actual = {p: info for p, info in blobs.items() if p.startswith('Tests/ContractFixtures/')}
    if actual != fixtures or len(fixtures) != len(lock['fixtures']):
        errors.append('locked fixture paths, sizes or Git blob IDs differ from source tree')
    # Only functional-baseline URLs, not changing PRs, other historical commits or external APIs.
    url = re.escape(lock['source']['url']) + r'/(blob|tree)/' + re.escape(sha) + r'/([^\s)\]#<>`]+)'
    refs = set()
    for md in [args.root / 'README.md', args.root / 'AGENTS.md', *sorted((args.root / 'docs/windows-port').glob('*.md'))]:
        for kind, p in re.findall(url, md.read_text(encoding='utf-8')):
            path = unquote(p).rstrip('/')
            refs.add((kind, path))
            if path not in (blobs if kind == 'blob' else trees):
                errors.append(f'{md.name}: missing locked {kind}: {path}')
    if not refs:
        errors.append('no locked GitHub source citations found')
    for issue in sorted(set(errors)):
        print(issue)
    print(f'{"FAIL" if errors else "PASS"}: {len(blobs)} source blobs, {len(refs)} distinct locked path citations, {len(fixtures)} fixture locks. No application tests executed.')
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())

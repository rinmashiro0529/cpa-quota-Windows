#!/usr/bin/env python3
"""Validate planning documents and metadata; never run application tests or network IO."""

from __future__ import annotations

import argparse
from collections import Counter, deque
from datetime import date
from functools import lru_cache
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


SHA_RE = re.compile(r"[0-9a-f]{40}\Z")
FEATURE_RE = re.compile(r"F-[A-Z][A-Z0-9]*-\d{3}\Z")
ACCEPTANCE_RE = re.compile(r"(?<![A-Za-z0-9-])AT-[A-Z][A-Z0-9]*-\d{3}(?![A-Za-z0-9-])")
TASK_RE = re.compile(r"WP-\d{3}\Z")
TASK_STATUSES = {"planned", "ready", "in_progress", "blocked", "in_review", "done"}
EXPECTED_FEATURE_COUNT = 97
EXPECTED_TASK_IDS = {f"WP-{number:03d}" for number in range(33)}


class Report:
    def __init__(self) -> None:
        self.check_count = 0
        self.failures: list[str] = []

    def check(self, name: str, errors: list[str]) -> None:
        self.check_count += 1
        self.failures.extend(f"{name}: {error}" for error in errors)

    def finish(self, features: int = 0, acceptances: int = 0, tasks: int = 0,
               documents: int = 0) -> int:
        counts = (f"{self.check_count} checks; {features} features, {acceptances} acceptance IDs, "
                  f"{tasks} tasks, {documents} Markdown documents")
        if self.failures:
            print(f"FAIL: planning consistency; {counts}; {len(self.failures)} issue(s).", file=sys.stderr)
            for failure in self.failures[:40]:
                print(f"  - {failure}", file=sys.stderr)
            if len(self.failures) > 40:
                print(f"  - ... {len(self.failures) - 40} additional issue(s).", file=sys.stderr)
        else:
            print(f"PASS: planning consistency; {counts}.")
        print("This gate validates planning consistency only. Application tests were not run.")
        return 1 if self.failures else 0


def nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def string_list(value: object) -> bool:
    return isinstance(value, list) and all(nonempty_string(item) for item in value)


def schema_one(value: object) -> bool:
    return type(value) is int and value == 1


def no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def read_json(path: Path) -> dict:
    result = json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=no_duplicate_keys)
    if not isinstance(result, dict):
        raise ValueError("top-level JSON value must be an object")
    return result


def within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def strip_fences(text: str) -> str:
    """Keep line numbers while excluding fenced examples and future source-path listings."""
    output: list[str] = []
    fence_char: str | None = None
    fence_length = 0
    for line in text.splitlines():
        opening = re.match(r"^\s{0,3}(`{3,}|~{3,})(.*)$", line)
        if fence_char is not None:
            if opening and opening.group(1)[0] == fence_char and len(opening.group(1)) >= fence_length and not opening.group(2).strip():
                fence_char = None
            output.append("")
        elif opening:
            fence_char = opening.group(1)[0]
            fence_length = len(opening.group(1))
            output.append("")
        else:
            output.append(line)
    return "\n".join(output)


def table_cells(line: str) -> list[str]:
    value = line.strip()
    if value.startswith("|"):
        value = value[1:]
    if value.endswith("|"):
        value = value[:-1]
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", value)]


def plain_cell(cell: str) -> str:
    return re.sub(r"[`*_\s]", "", cell)


def feature_rows(text: str) -> tuple[list[tuple[str, list[str], int]], list[str]]:
    """Parse only tables whose headers explicitly identify feature and acceptance columns."""
    lines = strip_fences(text).splitlines()
    rows: list[tuple[str, list[str], int]] = []
    errors: list[str] = []
    index = 0
    while index + 1 < len(lines):
        if not lines[index].lstrip().startswith("|"):
            index += 1
            continue
        headers = [plain_cell(cell) for cell in table_cells(lines[index])]
        feature_column = next((i for i, cell in enumerate(headers) if cell == "功能ID"), None)
        acceptance_column = next((i for i, cell in enumerate(headers) if "验收ID" in cell), None)
        separator = table_cells(lines[index + 1])
        if feature_column is None or acceptance_column is None or not separator or not all(re.fullmatch(r":?-{3,}:?", cell) for cell in separator):
            index += 1
            continue
        index += 2
        while index < len(lines) and lines[index].lstrip().startswith("|"):
            cells = table_cells(lines[index])
            if len(cells) != len(headers):
                errors.append(f"FEATURE_PARITY.md:{index + 1}: expected {len(headers)} table cells, found {len(cells)}")
            else:
                feature = plain_cell(cells[feature_column])
                if not FEATURE_RE.fullmatch(feature):
                    errors.append(f"FEATURE_PARITY.md:{index + 1}: invalid feature ID {feature!r}")
                else:
                    rows.append((feature, ACCEPTANCE_RE.findall(cells[acceptance_column]), index + 1))
            index += 1
    return rows, errors


def normalize_label(label: str) -> str:
    return " ".join(label.split()).casefold()


def link_destination(raw: str) -> str:
    value = raw.strip()
    if value.startswith("<"):
        end = value.find(">")
        return value[1:end] if end >= 0 else ""
    match = re.match(r"\S+", value)
    return match.group(0) if match else ""


@lru_cache(maxsize=128)
def markdown_anchors(path: Path) -> set[str]:
    """ATX headings and explicit anchors used in this planning corpus."""
    body = strip_fences(path.read_text(encoding="utf-8-sig"))
    result = set(re.findall(r'<a\s+(?:id|name)="([^"]+)"', body))
    for heading in re.findall(r'^#{1,6}\s+(.+?)\s*$', body, re.M):
        base = re.sub(r'[^\w\- ]', '', heading.lower()).replace(' ', '-')
        slug, index = base, 0
        while slug in result:
            index += 1
            slug = f'{base}-{index}'
        result.add(slug)
    return result


def check_local_destination(raw: str, origin: Path, root: Path) -> str | None:
    destination = link_destination(raw)
    if not destination:
        return None
    destination = re.sub(r"\\([()\\ ])", r"\1", destination)
    try:
        parsed = urlsplit(destination)
    except ValueError:
        return f"invalid Markdown link destination: {destination!r}"
    if parsed.scheme or parsed.netloc:
        return None  # External URLs are not fetched; this gate makes no availability claim.
    path_text = unquote(parsed.path)
    target = origin if not path_text else ((root / path_text.lstrip("/")) if path_text.startswith("/") else (origin.parent / path_text))
    if not within(target, root):
        return f"relative link escapes repository: {destination}"
    if not target.exists():
        return f"missing Markdown link target: {destination}"
    if parsed.fragment and target.suffix.lower() == '.md' and unquote(parsed.fragment) not in markdown_anchors(target.resolve()):
        return f"missing Markdown anchor: {destination}"
    return None


def check_markdown(path: Path, root: Path) -> list[str]:
    errors: list[str] = []
    text = strip_fences(path.read_text(encoding="utf-8-sig"))
    definitions: dict[str, tuple[str, int]] = {}
    prose: list[tuple[int, str]] = []
    for number, line in enumerate(text.splitlines(), 1):
        definition = re.match(r"^\s{0,3}\[([^\]]+)\]:\s*(.*)$", line)
        if definition and not definition.group(1).startswith("^"):
            label = normalize_label(definition.group(1))
            if label in definitions:
                errors.append(f"{path.relative_to(root)}:{number}: duplicate link reference {definition.group(1)!r}")
            definitions[label] = (definition.group(2), number)
        else:
            prose.append((number, re.sub(r"(`+).*?\1", "", line)))
    for label, (destination, number) in definitions.items():
        if not destination.strip():
            errors.append(f"{path.relative_to(root)}:{number}: empty destination for [{label}]")
        problem = check_local_destination(destination, path, root)
        if problem:
            errors.append(f"{path.relative_to(root)}:{number}: {problem}")
    for number, line in prose:
        for match in re.finditer(r"!?\[[^\]\n]*\]\(([^\n]*?)\)", line):
            problem = check_local_destination(match.group(1), path, root)
            if problem:
                errors.append(f"{path.relative_to(root)}:{number}: {problem}")
        for match in re.finditer(r"!?\[([^\]\n]+)\]\[([^\]\n]*)\]", line):
            label = normalize_label(match.group(2) or match.group(1))
            if label not in definitions:
                errors.append(f"{path.relative_to(root)}:{number}: undefined link reference [{label}]")
        # These documents also use source citations as shortcut reference links.
        for match in re.finditer(r"(?<!!)\[((?:S|W)-[A-Z][A-Z0-9-]*|W\d{2,})\](?![(:])", line):
            if normalize_label(match.group(1)) not in definitions:
                errors.append(f"{path.relative_to(root)}:{number}: undefined source reference [{match.group(1)}]")
    return errors


def artifact_reference(value: object, root: Path) -> bool:
    if isinstance(value, dict):
        value = value.get("url") or value.get("path")
    if not nonempty_string(value):
        return False
    assert isinstance(value, str)
    try:
        url = urlsplit(value)
    except ValueError:
        return False
    if url.scheme in {"https", "http"}:
        return bool(url.netloc)
    if url.scheme or url.netloc:
        return False
    target = root / unquote(url.path)
    return within(target, root) and target.is_file()


def check_done_evidence(task: dict, root: Path, source_sha: str, known_features: set[str]) -> list[str]:
    errors: list[str] = []
    task_id = task.get("id", "<unknown>")
    records = task.get("evidence")
    if not isinstance(records, list) or not records:
        return [f"{task_id}: done requires nonempty passed evidence, not a completion assertion"]
    evidenced_features: set[str] = set()
    evidenced_acceptances: set[str] = set()
    assigned_acceptances = set(task['acceptance_ids']) if string_list(task.get('acceptance_ids')) else set()
    candidate_shas: set[str] = set()
    for number, item in enumerate(records, 1):
        label = f"{task_id}.evidence[{number - 1}]"
        if isinstance(item, str):
            evidence_path = root / item
            if not within(evidence_path, root) or not evidence_path.is_file() or evidence_path.suffix.lower() != ".json":
                errors.append(f"{label}: expected an existing repository-relative JSON evidence file")
                continue
            try:
                evidence = read_json(evidence_path)
            except (OSError, UnicodeError, ValueError) as error:
                errors.append(f"{label}: invalid JSON evidence: {error}")
                continue
        elif isinstance(item, dict):
            evidence = item
        else:
            errors.append(f"{label}: expected a full evidence object or repository-relative JSON path")
            continue
        if not schema_one(evidence.get("schema_version")):
            errors.append(f"{label}: schema_version must be 1")
        if evidence.get("kind") == "template":
            errors.append(f"{label}: an unexecuted template cannot establish done; replace kind with the actual evidence type")
        if evidence.get("status") != "passed":
            errors.append(f"{label}: done evidence status must be passed")
        if evidence.get("task_id") != task_id:
            errors.append(f"{label}: task_id must match {task_id}")
        target_sha = evidence.get("target_sha")
        if not isinstance(target_sha, str) or not SHA_RE.fullmatch(target_sha):
            errors.append(f"{label}: target_sha must identify the tested 40-hex commit")
        else:
            candidate_shas.add(target_sha)
        at_ids = evidence.get('acceptance_ids')
        if not string_list(at_ids) or set(at_ids) - assigned_acceptances:
            errors.append(f'{label}: acceptance_ids must reference this task')
        else:
            evidenced_acceptances.update(at_ids)
        if evidence.get("source_sha") != source_sha:
            errors.append(f"{label}: source_sha differs from the planning source lock")
        features = evidence.get("feature_ids")
        if not string_list(features):
            errors.append(f"{label}: feature_ids must be a string array")
        else:
            unknown = set(features) - known_features
            if unknown:
                errors.append(f"{label}: unknown feature_ids: {', '.join(sorted(unknown))}")
            evidenced_features.update(features)
        checks = evidence.get("checks")
        if not isinstance(checks, list) or not checks:
            errors.append(f"{label}: requires at least one completed check")
            checks = []
        artifacts: list[object] = []
        raw_artifacts = evidence.get("raw_artifacts", [])
        if isinstance(raw_artifacts, list):
            artifacts.extend(raw_artifacts)
        else:
            errors.append(f"{label}: raw_artifacts must be an array")
        for check_number, check in enumerate(checks):
            check_label = f"{label}.checks[{check_number}]"
            if not isinstance(check, dict):
                errors.append(f"{check_label}: must be an object")
                continue
            if not nonempty_string(check.get("id")) or check.get("status") != "passed":
                errors.append(f"{check_label}: requires a check id and passed status; failed/not_run/blocked/unknown cannot establish done")
            if any(check.get(field) is None or
                   (isinstance(check.get(field), str) and not check[field].strip())
                   for field in ("expected", "actual")):
                errors.append(f"{check_label}: expected and actual results are required")
            urls = check.get("artifact_urls", [])
            if isinstance(urls, list):
                artifacts.extend(urls)
            else:
                errors.append(f"{check_label}: artifact_urls must be an array")
        if not artifacts:
            errors.append(f"{label}: requires raw_artifacts or checks[].artifact_urls")
        elif not all(artifact_reference(artifact, root) for artifact in artifacts):
            errors.append(f"{label}: artifact references must be HTTP(S) URLs or existing repository files")
    assigned = set(task.get("feature_ids", [])) if string_list(task.get("feature_ids")) else set()
    if len(candidate_shas) > 1:
        errors.append(f'{task_id}: cannot combine different target_sha values to establish done')
    if assigned_acceptances - evidenced_acceptances:
        errors.append(f'{task_id}: missing task acceptance evidence: {sorted(assigned_acceptances - evidenced_acceptances)}')
    if assigned - evidenced_features:
        errors.append(f"{task_id}: done evidence does not cover assigned feature IDs: {', '.join(sorted(assigned - evidenced_features))}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2],
                        help="Repository root (default: inferred from tools/planning/validate_plan.py)")
    args = parser.parse_args()
    root = args.root.resolve()
    report = Report()
    relative_inputs = {
        "tasks": "planning/tasks.json",
        "lock": "planning/source-lock.json",
        "template": "planning/evidence-template.json",
        "baseline": "docs/windows-port/SOURCE_BASELINE.md",
        "matrix": "docs/windows-port/FEATURE_PARITY.md",
        "architecture": "docs/windows-port/ARCHITECTURE.md",
        "acceptance": "docs/windows-port/ACCEPTANCE.md",
    }
    inputs = {key: root / value for key, value in relative_inputs.items()}
    missing = [f"missing input: {relative_inputs[key]}" for key, path in inputs.items() if not path.is_file()]
    report.check("required inputs", missing)
    if missing:
        return report.finish()
    data: dict[str, dict] = {}
    errors: list[str] = []
    for name in ("tasks", "lock", "template"):
        try:
            data[name] = read_json(inputs[name])
        except (OSError, UnicodeError, ValueError) as error:
            errors.append(f"{relative_inputs[name]}: {error}")
    report.check("JSON syntax and duplicate keys", errors)
    if errors:
        return report.finish()
    try:
        baseline = inputs["baseline"].read_text(encoding="utf-8-sig")
        matrix = inputs["matrix"].read_text(encoding="utf-8-sig")
        architecture = inputs['architecture'].read_text(encoding='utf-8-sig')
        acceptance = inputs['acceptance'].read_text(encoding='utf-8-sig')
    except (OSError, UnicodeError) as error:
        report.check("read planning documents", [str(error)])
        return report.finish()

    errors = []
    for name in ("tasks", "lock", "template"):
        if not schema_one(data[name].get("schema_version")):
            errors.append(f"{relative_inputs[name]}: schema_version must be integer 1")
    source = data["lock"].get("source")
    if not isinstance(source, dict):
        errors.append("source-lock.json: source must be an object")
        source = {}
    if not nonempty_string(source.get("repository")):
        errors.append("source-lock.json: source.repository is required")
    try:
        date.fromisoformat(source.get("verified_on", ""))
    except (TypeError, ValueError):
        errors.append("source-lock.json: source.verified_on must be an ISO YYYY-MM-DD date")
    report.check("metadata schema versions and source identity", errors)

    lock_sha = source.get("commit_sha")
    task_sha = data["tasks"].get("source_baseline_sha")
    baseline_row = re.search(r"^\|\s*基线提交\s*\|([^\n]+)$", baseline, re.M)
    document_shas = set(re.findall(r"(?<![0-9a-f])[0-9a-f]{40}(?![0-9a-f])", baseline_row.group(1))) if baseline_row else set()
    document_sha = next(iter(document_shas)) if len(document_shas) == 1 else None
    errors = []
    for label, value in (("source-lock.json source.commit_sha", lock_sha),
                         ("tasks.json source_baseline_sha", task_sha),
                         ("SOURCE_BASELINE.md 基线提交 row", document_sha)):
        if not isinstance(value, str) or not SHA_RE.fullmatch(value):
            errors.append(f"{label}: requires one unambiguous lowercase 40-hex SHA")
    if not errors and len({lock_sha, task_sha, document_sha}) != 1:
        errors.append("source SHA differs between source-lock.json, tasks.json and SOURCE_BASELINE.md")
    report.check("three-way source SHA lock", errors)

    rows, errors = feature_rows(matrix)
    ids = [feature for feature, _, _ in rows]
    duplicate_ids = [value for value, count in Counter(ids).items() if count > 1]
    if len(ids) != EXPECTED_FEATURE_COUNT:
        errors.append(f"expected {EXPECTED_FEATURE_COUNT} feature table rows, found {len(ids)}")
    if duplicate_ids:
        errors.append("duplicate feature rows: " + ", ".join(sorted(duplicate_ids)))
    report.check("feature matrix IDs", errors)
    known_features = set(ids)
    acceptances: list[str] = []
    errors = []
    for feature, matches, number in rows:
        expected = "AT-" + feature[2:]
        if matches != [expected]:
            errors.append(f"FEATURE_PARITY.md:{number}: {feature} requires exactly {expected} in its acceptance cell; found {matches}")
        acceptances.extend(matches)
    if len(acceptances) != EXPECTED_FEATURE_COUNT or len(set(acceptances)) != EXPECTED_FEATURE_COUNT:
        errors.append(f"expected {EXPECTED_FEATURE_COUNT} unique mirrored AT IDs in feature rows; found {len(acceptances)} total/{len(set(acceptances))} unique")
    report.check("mirrored acceptance IDs", errors)

    tasks = data["tasks"].get("tasks")
    errors = []
    if not isinstance(tasks, list):
        errors.append("tasks.json: tasks must be an array")
        tasks = []
    task_objects = [task for task in tasks if isinstance(task, dict)]
    if len(task_objects) != len(tasks):
        errors.append("every task must be an object")
    task_ids: list[str] = []
    for number, task in enumerate(task_objects):
        task_id = task.get("id")
        label = task_id if isinstance(task_id, str) else f"tasks[{number}]"
        if not isinstance(task_id, str) or not TASK_RE.fullmatch(task_id):
            errors.append(f"{label}: invalid WP task ID")
        else:
            task_ids.append(task_id)
        for field in ("title", "milestone", "owner_role", "repository"):
            if not nonempty_string(task.get(field)):
                errors.append(f"{label}: {field} must be a nonempty string")
        if not isinstance(task.get("status"), str) or task.get("status") not in TASK_STATUSES:
            errors.append(f"{label}: invalid task status {task.get('status')!r}")
        for field in ("depends_on", "feature_ids", "artifacts", "acceptance", "evidence_types"):
            if not string_list(task.get(field)):
                errors.append(f"{label}: {field} must be a string array")
        if not isinstance(task.get("evidence"), list):
            errors.append(f"{label}: evidence must be an array")
        for field in ("assignee", "branch", "pr"):
            if field not in task:
                errors.append(f"{label}: missing nullable field {field}")
    duplicates = [value for value, count in Counter(task_ids).items() if count > 1]
    if duplicates:
        errors.append("duplicate task IDs: " + ", ".join(sorted(duplicates)))
    if set(task_ids) != EXPECTED_TASK_IDS:
        errors.append(f"expected WP-000 through WP-032; missing={sorted(EXPECTED_TASK_IDS - set(task_ids))}, unexpected={sorted(set(task_ids) - EXPECTED_TASK_IDS)}")
    report.check("task schema and IDs", errors)

    tasks_by_id = {task["id"]: task for task in task_objects if isinstance(task.get("id"), str)}
    errors = []
    indegree = {task_id: 0 for task_id in tasks_by_id}
    dependents: dict[str, list[str]] = {task_id: [] for task_id in tasks_by_id}
    for task_id, task in tasks_by_id.items():
        dependencies = task.get("depends_on")
        if not string_list(dependencies):
            continue
        if len(dependencies) != len(set(dependencies)):
            errors.append(f"{task_id}: duplicate dependencies")
        for dependency in set(dependencies):
            if dependency not in tasks_by_id:
                errors.append(f"{task_id}: dependency {dependency} does not exist")
            else:
                indegree[task_id] += 1
                dependents[dependency].append(task_id)
    queue = deque(task_id for task_id, count in indegree.items() if count == 0)
    visited = 0
    while queue:
        current = queue.popleft()
        visited += 1
        for dependent in dependents[current]:
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                queue.append(dependent)
    if visited != len(tasks_by_id):
        errors.append("dependency cycle, or dependency on a cycle: " + ", ".join(sorted(key for key, value in indegree.items() if value)))
    report.check("dependency references and DAG", errors)

    errors = []
    covered: set[str] = set()
    for task_id, task in tasks_by_id.items():
        features = task.get("feature_ids")
        if not string_list(features):
            continue
        if len(features) != len(set(features)):
            errors.append(f"{task_id}: duplicate feature_ids")
        if set(features) - known_features:
            errors.append(f"{task_id}: unknown feature_ids: {', '.join(sorted(set(features) - known_features))}")
        covered.update(features)
    if known_features - covered:
        errors.append("features without a task: " + ", ".join(sorted(known_features - covered)))
    report.check("complete feature-to-task coverage", errors)

    errors = []
    cross = {f'AT-CROSS-{i:03}' for i in range(1, 7)}
    if Counter(re.findall(r'^\|\s*(AT-CROSS-\d+)\s*\|', acceptance, re.M)) != Counter(cross):
        errors.append('ACCEPTANCE.md: missing or duplicate cross-domain scenario definition')
    invariants = re.findall(r'^\|\s*(INV-\d+)\s*\|', architecture, re.M)
    if len(invariants) != len(set(invariants)) or not invariants:
        errors.append('ARCHITECTURE.md: missing or duplicate invariant definitions')
    for tid, task in tasks_by_id.items():
        fids = task.get('feature_ids')
        required = {'AT-' + fid[2:] for fid in fids} if string_list(fids) else set()
        if tid in {'WP-031', 'WP-032'}:
            required |= cross
        at = task.get('acceptance_ids')
        if not string_list(at) or Counter(at) != Counter(required):
            errors.append(f'{tid}: acceptance mapping must match assigned features and release scenarios')
        inv = task.get('invariant_ids')
        if not string_list(inv) or not inv or set(inv) - set(invariants) or len(inv) != len(set(inv)):
            errors.append(f'{tid}: invalid invariant mapping')
    report.check('task acceptance and invariant references', errors)

    visited_ids: set[str] = set()
    pending = ['WP-032']
    while pending:
        tid = pending.pop()
        if tid in visited_ids or tid not in tasks_by_id:
            continue
        visited_ids.add(tid)
        deps = tasks_by_id[tid].get('depends_on')
        if string_list(deps):
            pending.extend(deps)
    missing_ids = set(tasks_by_id) - visited_ids
    report.check('release dependency closure', [f'WP-032 does not require: {sorted(missing_ids)}'] if missing_ids else [])

    errors = []
    for task_id, task in tasks_by_id.items():
        if not isinstance(task.get("priority"), str) or task.get("priority") not in {"P0", "P1"}:
            errors.append(f"{task_id}: priority must be P0 or P1")
        if task.get("required_for_full_release") is not True:
            errors.append(f"{task_id}: every P0/P1 task must have required_for_full_release=true")
    report.check("full-release scope", errors)

    errors = []
    for task in task_objects:
        if task.get("status") == "done":
            if string_list(task.get("depends_on")):
                incomplete_dependencies = [dependency for dependency in task["depends_on"]
                                           if tasks_by_id.get(dependency, {}).get("status") != "done"]
                if incomplete_dependencies:
                    errors.append(f"{task.get('id')}: done requires completed dependencies: "
                                  + ", ".join(incomplete_dependencies))
            errors.extend(check_done_evidence(task, root, lock_sha if isinstance(lock_sha, str) else "", known_features))
    report.check("done evidence integrity", errors)

    template = data["template"]
    errors = []
    if template.get("status") != "not_run":
        errors.append("evidence-template.json: status must remain not_run")
    for field in ("target_sha", "task_id"):
        if field not in template or template[field] is not None:
            errors.append(f"evidence-template.json: {field} must be present and null")
    if template.get("feature_ids") != []:
        errors.append("evidence-template.json: feature_ids must be an empty array")
    if not isinstance(template.get("environment"), dict):
        errors.append("evidence-template.json: environment must be an object")
    checks = template.get("checks")
    if not isinstance(checks, list) or not checks:
        errors.append("evidence-template.json: checks must contain an unexecuted check template")
        checks = []
    for number, check in enumerate(checks):
        if not isinstance(check, dict):
            errors.append(f"evidence-template.json checks[{number}]: must be an object")
            continue
        for field in ("id", "status", "command", "expected", "actual", "artifact_urls"):
            if field not in check:
                errors.append(f"evidence-template.json checks[{number}]: missing {field}")
        if check.get("status") != "not_run" or check.get("command") is not None or check.get("actual") is not None or check.get("artifact_urls") != []:
            errors.append(f"evidence-template.json checks[{number}]: must not claim execution or contain produced artifacts")
    if template.get("source_sha") is not None and template.get("source_sha") != lock_sha:
        errors.append("evidence-template.json: source_sha may be null or equal the locked input source SHA")
    for field in ("service_sha", "exporter_sha", "artifact_sha256", "run_id", "attempt", "reviewer"):
        if field in template and template[field] not in (None, "", [], {}):
            errors.append(f"evidence-template.json: {field} must remain empty in the unexecuted template")
    for field in ("acceptance_ids", "commands", "raw_artifacts"):
        if field in template and template[field] != []:
            errors.append(f"evidence-template.json: {field} must remain an empty array")
    report.check("unexecuted evidence template", errors)

    documents = [root / name for name in ("README.md", "AGENTS.md", ".github/pull_request_template.md")
                 if (root / name).is_file()]
    documents.extend(sorted(path for path in (root / "docs/windows-port").rglob("*.md")
                            if "_research" not in path.relative_to(root).parts))
    if (root / "planning").is_dir():
        documents.extend(sorted(path for path in (root / "planning").rglob("*.md")
                                if "_research" not in path.relative_to(root).parts))
    errors = []
    for document in documents:
        try:
            errors.extend(check_markdown(document, root))
        except (OSError, UnicodeError) as error:
            errors.append(f"{document.relative_to(root)}: {error}")
    report.check("Markdown relative links and reference definitions", errors)

    scan_paths = set(documents)
    if (root / "planning").is_dir():
        scan_paths.update(path for path in (root / "planning").rglob("*")
                          if path.is_file() and "_research" not in path.relative_to(root).parts
                          and path.suffix.lower() in {".json", ".md", ".txt", ".yml", ".yaml"})
    errors = []
    wrong_platform = re.compile(r"Android|Kotlin", re.I)
    for path in sorted(scan_paths):
        try:
            for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
                match = wrong_platform.search(line)
                if match:
                    errors.append(f"{path.relative_to(root)}:{number}: wrong-platform residue {match.group(0)!r}")
        except (OSError, UnicodeError) as error:
            errors.append(f"{path.relative_to(root)}: {error}")
    report.check("final Windows planning scope", errors)
    return report.finish(len(ids), len(set(acceptances)), len(task_objects), len(documents))


if __name__ == "__main__":
    raise SystemExit(main())

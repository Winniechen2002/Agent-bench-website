"""Public-data policy shared by importers, validation, and the release builder.

Source locations are replaced by opaque artifact identifiers before writing data.
The location-to-ID map and exact commands belong in a separate private archive.
"""
import copy
import hashlib
import json
from pathlib import Path
import re

# Match classes of private locations; never embed real account or host names here.
PRIVATE_PATTERNS = (
    re.compile(r'(?<![\w])/(?:Users|home|mnt|private|root|tmp|var|run|Volumes|scratch|lustre|gpfs|cluster|data/users)/', re.I),
    re.compile(r'(?<![\w])(?:[A-Za-z]:[\\/]|\\\\[^\\\s]+\\)'),
    re.compile(r'(?<![\w:/])[\w.-]+(?:@[\w.-]+)?:/(?!/)'),
    re.compile(r'\b(?:ssh|scp|rsync)\s+\S+'),
    re.compile(r'(?:^|\n)\s*(?:python(?:\d+(?:\.\d+)*)?|bash|sh|ffmpeg)\s+(?:-\w+\s+)*(?:[^\s]+\.py\b|-[A-Za-z])', re.I),
    re.compile(r'\bsharpa_\d{4}(?:_\w+)?\b', re.I),
    re.compile(r'(?:~[/\\]|\$(?:HOME|USER)\b|\$\{(?:HOME|USER)\})'),
    re.compile(r'(?:^|[/\\])\.(?:git|codex-local|ssh|aws)(?:[/\\]|$)'),
    re.compile(r'-----BEGIN (?:\w+ )?PRIVATE KEY-----'),
    re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b'),
)
PRIVATE_FIELDS = {
    'source_checkout', 'source_host', 'hostname', 'username', 'user_account',
    'private_path', 'absolute_path', 'local_path', 'remote_path', 'ssh_host',
    'command', 'commands', 'export_command', 'encoding_command', 'command_note',
    'access_token', 'api_key', 'password', 'secret', 'credentials',
}


def artifact_id(location):
    """Opaque locator; deliberately not a content hash or a downloadable URL."""
    return 'source-' + hashlib.sha256(location.encode('utf-8')).hexdigest()[:24]


def strict_json(content):
    """Do not allow a later duplicate key to conceal an earlier private value."""
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON field in public document')
            result[key] = value
        return result
    return json.loads(content, object_pairs_hook=unique)


def public_media_entry(entry):
    """Project one native media record without changing presentation fields."""
    result = copy.deepcopy(entry)
    if 'source_path' in result:
        result['source_artifact_id'] = artifact_id(result.pop('source_path'))
    for resource in result.get('files', []):
        if 'source_path' in resource:
            resource['source_artifact_id'] = artifact_id(resource.pop('source_path'))
    validate_document(result, 'media entry')
    return result


def public_media_catalog(catalog):
    result = copy.deepcopy(catalog)
    result['entries'] = [public_media_entry(entry) for entry in catalog['entries']]
    validate_document(result, 'media provenance')
    return result


def private_text(value):
    return any(pattern.search(value) for pattern in PRIVATE_PATTERNS)


def document_findings(value, pointer=''):
    """Return field locations only. Diagnostics must never echo private values."""
    issues = []
    if isinstance(value, dict):
        for key, item in value.items():
            location = pointer + '/' + key
            if key.lower() in PRIVATE_FIELDS or private_text(key):
                issues.append(location + ': private field')
            issues.extend(document_findings(item, location))
            if isinstance(item, str) and (key == 'path' or key.endswith('_path')):
                if item.startswith(('/', '\\')) or '..' in Path(item).parts:
                    issues.append(location + ': non-portable path')
    elif isinstance(value, list):
        for index, item in enumerate(value):
            issues.extend(document_findings(item, pointer + '/' + str(index)))
    elif isinstance(value, str) and private_text(value):
        issues.append(pointer + ': private location or command')
    return issues


def validate_document(value, filename='document'):
    issues = document_findings(value)
    if issues:
        raise ValueError(f'{filename}: {len(issues)} private-data finding(s); first field: {issues[0]}')


def validate_public(root):
    """Scan runtime documents, including unexpected JSON in public data folders."""
    root = Path(root)
    files = [root / name for name in (
        'index.html', 'environment.html', 'site.js', 'site.css', 'environment.js', 'environment.css')]
    for directory in ('data', 'evidence'):
        files.extend(sorted((root / directory).rglob('*.json')))
    files.extend(sorted((root / 'assets').rglob('*.svg')))
    for file in files:
        if file.is_symlink():
            raise ValueError('Public inputs must not be symlinks')
        content = file.read_text(encoding='utf-8')
        if file.suffix == '.json':
            validate_document(strict_json(content), str(file.relative_to(root)))
        elif private_text(content):
            raise ValueError(f'{file.relative_to(root)}: private-data pattern in public text')
    return len(files)


def public_demo_manifest(manifest):
    """Export provenance without locations or host-specific command strings.

Media paths remain relative. Source artifacts retain hashes, sizes, roles,
conditions, and replay limitations, but identifiers are not download links.
"""
    def project(value):
        if isinstance(value, list):
            return [project(item) for item in value]
        if not isinstance(value, dict):
            return value
        result = {}
        for key, item in value.items():
            if key in PRIVATE_FIELDS:
                continue
            if key.endswith('_paths') and isinstance(item, list):
                result[key[:-6] + '_artifacts'] = [{'artifact_id': artifact_id(path)} for path in item]
            elif key == 'path' and isinstance(item, str) and not item.startswith('assets/'):
                result['artifact_id'] = artifact_id(item)
            elif key in ('source_path', 'source', 'selected_image') and isinstance(item, str):
                result['selected_artifact_id' if key == 'selected_image' else 'source_artifact_id'] = artifact_id(item)
            else:
                result[key] = project(item)
        return result

    result = project(manifest)
    result['version'] = 3
    result['storage_policy'] = 'Only web derivatives, posters, and public provenance are distributed. Raw recordings, trajectories, full source locations, and exact run commands are retained separately by the maintainers.'
    result['rerender_policy'] = 'Use the artifact ID to locate the maintainer-held source record. Preserve the original run, replay conditions, and stated limitations; update derivative hashes after re-encoding. Public artifact IDs are not download URLs and do not by themselves establish exact replay.'
    validate_document(result, 'demo provenance')
    return result

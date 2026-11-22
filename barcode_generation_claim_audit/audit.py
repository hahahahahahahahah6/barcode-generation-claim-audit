"""Compare documentation phrases with static Python evidence."""
import ast
import os
import re
from pathlib import Path
from .phrases import BARCODEGENERATION, NOBARCODEGENERATION, GENERIC_NAMES

CLASSES = frozenset('Code39 Code128 Gs1_128 PZN PZN7 PZN8 EAN13 EAN13_GUARD EAN8 EAN8_GUARD EAN14 JAN UPCA ISBN13 ISBN10 ISSN ITF CODABAR'.split())
ENCODERS = frozenset('Code128Encoder Code39Encoder EAN13Encoder ITFEncoder ITF14Encoder'.split())
ENCODER_PATHS = frozenset('pystrich.code128.Code128Encoder pystrich.code39.Code39Encoder pystrich.ean13.EAN13Encoder pystrich.itf.ITFEncoder pystrich.itf.ITF14Encoder'.split())
CLASS_OUTPUT = frozenset('save write render build'.split())
ENCODER_OUTPUT = frozenset('get_imagedata get_pilimage save get_svg save_svg get_eps save_eps png_dataurl svg_dataurl'.split())


def normalize(text):
    return ' '.join(text.lower().replace('’', "'").replace("n't", ' not').replace('-', ' ').split())


def pattern(phrases):
    return re.compile(r'\b(?:' + '|'.join(re.escape(p) for p in sorted(phrases, key=lambda p: (-len(p), p))) + r')\b')


def paragraphs(text):
    lines, fence = [], None
    for line in text.splitlines():
        mark = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
        if fence:
            if re.match(r'^ {0,3}' + re.escape(fence[0]) + '{' + str(len(fence)) + r',}\s*$', line):
                fence = None
            lines.append('')
        elif mark:
            fence = mark.group(1)
            lines.append('')
        else:
            lines.append(line)
    return [normalize(p) for p in re.split(r'\n\s*\n', '\n'.join(lines)) if p.strip()]


def evidence(source):
    try:
        nodes = list(ast.walk(ast.parse(source)))
    except (SyntaxError, ValueError):
        return False
    imports, bound, definitions = {}, set(), set()
    def targets(node):
        if isinstance(node, ast.Name):
            return {node.id}
        if isinstance(node, (ast.Tuple, ast.List)):
            return set().union(*(targets(item) for item in node.elts))
        if isinstance(node, ast.Starred):
            return targets(node.value)
        return set()
    for node in nodes:
        if isinstance(node, ast.Import):
            for item in node.names:
                imports[item.asname or item.name.split('.')[0]] = item.name if item.asname else item.name.split('.')[0]
        elif isinstance(node, ast.ImportFrom) and not node.level:
            for item in node.names:
                imports[item.asname or item.name] = (node.module or '') + '.' + item.name
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            definitions.add(node.name)
            bound.add(node.name)
        assignments = []
        if isinstance(node, ast.Assign):
            assignments = node.targets
        elif isinstance(node, ast.AnnAssign):
            assignments = [node.target]
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            assignments = [item.optional_vars for item in node.items if item.optional_vars]
        for assignment in assignments:
            bound.update(targets(assignment))
    class_leg = class_output = encoder_leg = encoder_output = False
    for node in nodes:
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        attr = isinstance(func, ast.Attribute)
        if isinstance(func, ast.Name):
            if func.id in bound:
                continue
            resolved = imports.get(func.id, '')
            name = resolved.rsplit('.', 1)[-1]
        elif attr:
            name = func.attr
            base = func.value
            while isinstance(base, ast.Attribute):
                base = base.value
            if isinstance(base, ast.Name) and base.id in imports and base.id in bound:
                continue
            resolved = imports.get(base.id, '') if isinstance(base, ast.Name) else ''
        else:
            continue
        if name in definitions:
            continue
        def library(lib, member):
            return (attr and name == member and (resolved == lib or resolved.startswith(lib + '.'))) or (not attr and resolved == lib + '.' + member)
        if name in GENERIC_NAMES and (attr or resolved):
            return True
        if any(library('barcode', x) for x in ('get', 'get_barcode')) and (len(node.args) >= 2 or any(k.arg == 'code' for k in node.keywords)):
            return True
        if library('barcode', 'generate') or library('treepoem', 'generate_barcode'):
            return True
        class_leg |= any(library('barcode', x) for x in CLASSES)
        class_output |= attr and name in CLASS_OUTPUT
        encoder_leg |= (attr and name in ENCODERS and (resolved == 'pystrich' or resolved.startswith('pystrich.'))) or (not attr and resolved in ENCODER_PATHS)
        encoder_output |= attr and name in ENCODER_OUTPUT
    return bool((class_leg and class_output) or (encoder_leg and encoder_output))


def audit(root, ignore=(), fail_on='high'):
    root = Path(root)
    if not root.is_dir() or not os.access(str(root), os.R_OK | os.X_OK):
        raise OSError('Not a readable directory: {}'.format(root))
    claims = denials = production = tests = False
    yes_re, no_re = pattern(BARCODEGENERATION), pattern(NOBARCODEGENERATION)
    def ignored(path):
        rel = path.relative_to(root).as_posix()
        return any(rel == prefix.rstrip('/') or rel.startswith(prefix.rstrip('/') + '/') for prefix in ignore)
    def raise_error(error):
        raise error
    for directory, dirs, files in os.walk(str(root), followlinks=False, onerror=raise_error):
        parent = Path(directory)
        dirs[:] = sorted(d for d in dirs if not (parent / d).is_symlink() and not ignored(parent / d))
        for filename in sorted(files):
            path = parent / filename
            if path.is_symlink() or ignored(path):
                continue
            rel = path.relative_to(root)
            if rel.as_posix() == 'README.md' or ('docs' in rel.parts and path.suffix == '.md'):
                for para in paragraphs(path.read_text(encoding='utf-8')):
                    denials |= bool(no_re.search(para))
                    claims |= bool(yes_re.search(no_re.sub(' ', para)))
            if path.suffix == '.py' and not any(x in rel.parts for x in ('fixtures', 'docs', 'examples')):
                is_test = 'tests' in rel.parts or filename.startswith('test_') or filename.endswith('_test.py')
                if evidence(path.read_text(encoding='utf-8')):
                    if is_test:
                        tests = True
                    else:
                        production = True
    findings = []
    if claims and not production:
        severity = 'MEDIUM' if tests else 'HIGH'
        findings.append({'rule': 'documented-barcode-generation-claim-false', 'severity': severity, 'message': 'Documented claim has ' + ('test-only evidence.' if tests else 'no production evidence.')})
    if denials and production:
        findings.append({'rule': 'documented-no-barcode-generation-claim-false', 'severity': 'HIGH', 'message': 'Documented denial conflicts with production evidence.'})
    fail = any(item['severity'] == 'HIGH' or fail_on == 'medium' for item in findings)
    return {'verdict': 'FAIL' if fail else 'PASS', 'findings': findings}

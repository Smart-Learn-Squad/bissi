import ast
import json
import subprocess
import sys
from typing import Dict, Any

# Liste blanche réduite aux modules strictement nécessaires
ALLOWED_MODULES = {
    'pandas', 'numpy', 'matplotlib', 'json', 'csv', 'statistics',
    'math', 'random', 'datetime', 'collections', 'itertools',
    're', 'string', 'hashlib', 'base64', 'io', 'pathlib',
    'typing', 'textwrap', 'copy', 'decimal', 'fractions'
}

# Noms de fonctions et attributs dangereux à bloquer (même indirectement)
FORBIDDEN_NAMES = {
    'eval', 'exec', 'compile', '__import__', 'open', 'input',
    'raw_input', 'breakpoint', 'exit', 'quit', 'reload',
    'globals', 'locals', 'vars', 'dir', '__builtins__',
    '__builtin__', '__getattribute__', '__setattr__',
    '__delattr__', '__reduce__', '__reduce_ex__', '__class__',
    '__bases__', '__mro__', '__subclasses__', '__loader__',
    '__spec__', '__name__'
}

class SecurityError(Exception):
    pass

def _is_code_safe(code: str) -> tuple[bool, str]:
    """Analyse AST pour détecter toute forme d’accès dangereux."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, f"Syntax error: {e}"

    for node in ast.walk(tree):
        # Interdire toute forme d’import non autorisé
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split('.')[0]
                if root not in ALLOWED_MODULES:
                    return False, f"Module interdit: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root = node.module.split('.')[0]
                if root not in ALLOWED_MODULES:
                    return False, f"Import interdit: {node.module}"
        # Interdire les appels à des fonctions dangereuses
        elif isinstance(node, ast.Call):
            func_name = None
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                # Bloque les appels de type getattr(...)()
                if isinstance(node.func.value, ast.Call):
                    return False, "Appel de fonction dynamique interdit"
                func_name = node.func.attr
            if func_name in FORBIDDEN_NAMES:
                return False, f"Appel interdit: {func_name}"
        # Interdire les noms de variables dangereux
        elif isinstance(node, ast.Name):
            if node.id in FORBIDDEN_NAMES:
                return False, f"Variable interdite: {node.id}"
        # Interdire les compréhensions avec eval caché (ex: [eval(x) for x in ...])
        elif isinstance(node, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
            # Le parcours des générateurs couvre déjà les appels, mais on garde un niveau supplémentaire
            pass
        # Interdire l’accès aux attributs spéciaux (__dict__, __class__, etc.)
        elif isinstance(node, ast.Attribute) and node.attr.startswith('__') and node.attr.endswith('__'):
            return False, f"Attribut magique interdit: {node.attr}"

    return True, ""

def run_code(code: str, timeout: int = 30) -> Dict[str, Any]:
    is_safe, reason = _is_code_safe(code)
    if not is_safe:
        return {'success': False, 'error': f"Security violation: {reason}", 'output': ''}

    # Surcharge plus radicale des builtins
    bootstrap = f"""
import builtins
import sys
import io
import json
import traceback
import contextlib

# Create a clean copy of builtins without dangerous functions
safe_builtins = {{}}
allowlist = {{
    'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytearray', 'bytes',
    'callable', 'chr', 'complex', 'dict', 'divmod', 'enumerate', 'filter',
    'float', 'format', 'frozenset', 'hasattr', 'hash', 'hex', 'int',
    'isinstance', 'issubclass', 'iter', 'len', 'list', 'map', 'max',
    'memoryview', 'min', 'next', 'oct', 'ord', 'pow', 'print', 'property',
    'range', 'repr', 'reversed', 'round', 'set', 'slice', 'sorted',
    'staticmethod', 'str', 'sum', 'tuple', 'type', 'zip', 'True', 'False', 'None'
}}
for name in allowlist:
    if hasattr(builtins, name):
        safe_builtins[name] = getattr(builtins, name)

# Custom importer that only allows allowed modules
_allowed_modules = {sorted(ALLOWED_MODULES)!r}

def _safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    root = name.split('.')[0] if name else ''
    if root not in _allowed_modules:
        raise ImportError(f"Forbidden import: {{name}}")
    # Use the original __import__ but only after checking
    return original_import(name, globals, locals, fromlist, level)

# Keep a reference to the real __import__
original_import = builtins.__import__
safe_builtins['__import__'] = _safe_import

# Create a brand new globals dict without __builtins__ exposing original
safe_globals = {{'__builtins__': safe_builtins}}

# Pre-import allowed modules
for mod in _allowed_modules:
    try:
        m = original_import(mod)
        safe_globals[mod] = m
        if mod == 'pandas':
            safe_globals['pd'] = m
        elif mod == 'numpy':
            safe_globals['np'] = m
        elif mod == 'matplotlib':
            try:
                safe_globals['plt'] = original_import('matplotlib.pyplot')
            except:
                pass
    except:
        pass

# Execute user code
code = sys.stdin.read()
stdout_capture = io.StringIO()
try:
    with contextlib.redirect_stdout(stdout_capture):
        exec(code, safe_globals)
    payload = {{'success': True, 'output': stdout_capture.getvalue(), 'error': None}}
except Exception as e:
    payload = {{'success': False, 'output': stdout_capture.getvalue(),
               'error': f'{{type(e).__name__}}: {{e}}', 'traceback': traceback.format_exc()}}

print(json.dumps(payload))
"""
    try:
        completed = subprocess.run(
            [sys.executable, "-I", "-c", bootstrap],
            input=code,
            text=True,
            capture_output=True,
            timeout=timeout,
            env={"MPLBACKEND": "Agg"},
        )
    except subprocess.TimeoutExpired:
        return {'success': False, 'output': '', 'error': f'Timeout after {timeout}s'}

    if completed.returncode != 0:
        return {
            'success': False,
            'output': completed.stdout,
            'error': completed.stderr.strip() or f"Exit code {completed.returncode}",
        }

    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {'success': False, 'output': completed.stdout, 'error': 'Invalid sandbox response'}

def analyze_dataframe(df_code: str) -> Dict[str, Any]:
    """Analyse un DataFrame pandas (version sécurisée)."""
    # Exécution du code initial
    result = run_code(df_code)
    if not result['success']:
        return result
    
    # On ne peut plus facilement récupérer les variables locales entre deux appels subprocess
    # Cette fonction doit être revue pour tout faire en un seul appel si possible,
    # ou on laisse tomber cette fonctionnalité spécifique si elle n'est pas critique.
    # Pour BISSI, on préfère la sécurité.
    return result

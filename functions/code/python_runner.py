"""Restricted Python execution for BISSI.

This module intentionally uses a separate Python subprocess with a real timeout.
It is still not a fully isolated OS-level sandbox, but it is materially safer
and more reliable for demos than in-process ``exec``.
"""
import json
import subprocess
import sys
import importlib
import ast
from typing import Dict, Any


class PythonSandbox:
    """Restricted Python execution environment."""
    
    # Allowed modules for data analysis
    ALLOWED_MODULES = {
        'pandas', 'numpy', 'matplotlib', 'json', 'csv', 'statistics',
        'math', 'random', 'datetime', 'collections', 'itertools',
        're', 'string', 'hashlib', 'base64', 'io', 'pathlib',
        'typing', 'inspect', 'textwrap', 'copy', 'decimal', 'fractions'
    }
    
    # Forbidden keywords
    FORBIDDEN_KEYWORDS = [
        '__import__', 'eval', 'exec', 'compile', 'open', 'input',
        'raw_input', 'breakpoint', 'help', 'license', 'credits',
        'exit', 'quit', 'reload', 'compileall', 'py_compile'
    ]
    
    def __init__(self, timeout: int = 30):
        """Initialize sandbox.
        
        Args:
            timeout: Execution timeout in seconds
        """
        self.timeout = timeout
        self.execution_history = []
    
    def _is_code_safe(self, code: str) -> tuple[bool, str]:
        """Check if code contains forbidden elements.
        
        Args:
            code: Python code to check
            
        Returns:
            (is_safe, reason) tuple
        """
        # Check for forbidden keywords
        for keyword in self.FORBIDDEN_KEYWORDS:
            if keyword in code:
                return False, f"Forbidden keyword: {keyword}"
        
        # Parse AST for deeper analysis
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, f"Syntax error: {e}"
        
        # Check for dangerous imports or calls
        for node in ast.walk(tree):
            # Check imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split('.')[0]
                    if root not in self.ALLOWED_MODULES:
                        return False, f"Forbidden import: {alias.name}"
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root = node.module.split('.')[0]
                    if root not in self.ALLOWED_MODULES:
                        return False, f"Forbidden import from: {node.module}"
            
            # Check for dangerous calls
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.FORBIDDEN_KEYWORDS:
                        return False, f"Forbidden call: {node.func.id}"
        
        return True, ""
    
    def execute(self, code: str) -> Dict[str, Any]:
        """Execute Python code safely.
        
        Args:
            code: Python code to execute
            
        Returns:
            Dictionary with execution results
        """
        # Safety check
        is_safe, reason = self._is_code_safe(code)
        if not is_safe:
            return {
                'success': False,
                'error': f"Security error: {reason}",
                'output': ''
            }
        
        try:
            completed = subprocess.run(
                [sys.executable, "-I", "-c", self._bootstrap_code()],
                input=code,
                text=True,
                capture_output=True,
                timeout=self.timeout,
                env={"MPLBACKEND": "Agg"},
            )
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': '',
                'error': f"Timeout after {self.timeout}s",
            }

        if completed.returncode != 0:
            return {
                'success': False,
                'output': completed.stdout,
                'error': completed.stderr.strip() or f"Subprocess failed with exit code {completed.returncode}",
            }

        try:
            payload = json.loads(completed.stdout)
            self.execution_history.append({
                'code': code[:100] + '...' if len(code) > 100 else code,
                'success': payload.get('success', False)
            })
            return payload
        except json.JSONDecodeError:
            return {
                'success': False,
                'output': completed.stdout,
                'error': 'Invalid sandbox response',
            }
    
    def execute_expression(self, expression: str) -> Any:
        """Evaluate single expression and return result.
        
        Args:
            expression: Python expression
            
        Returns:
            Expression result
        """
        is_safe, reason = self._is_code_safe(expression)
        if not is_safe:
            raise ValueError(f"Security error: {reason}")
        
        result = self.execute(f"print(repr({expression}))")
        if not result.get("success"):
            raise ValueError(f"Evaluation error: {result.get('error')}")
        return result.get("output", "").strip()
    
    def get_variable(self, name: str) -> Any:
        """Get variable from sandbox globals.
        
        Args:
            name: Variable name
            
        Returns:
            Variable value
        """
        raise NotImplementedError("Variables are not persisted across subprocess runs.")
    
    def set_variable(self, name: str, value: Any) -> None:
        """Set variable in sandbox globals.
        
        Args:
            name: Variable name
            value: Value to set
        """
        raise NotImplementedError("Variables are not persisted across subprocess runs.")
    
    def get_available_variables(self) -> Dict[str, str]:
        """Get list of defined variables with their types."""
        return {}

    @classmethod
    def _bootstrap_code(cls) -> str:
        allowed_modules = sorted(cls.ALLOWED_MODULES)
        forbidden_calls = sorted(cls.FORBIDDEN_KEYWORDS)
        return f"""
import builtins
import contextlib
import importlib
import io
import json
import traceback
import sys

ALLOWED_MODULES = {allowed_modules!r}
SAFE_NAMES = [
    'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytearray',
    'bytes', 'callable', 'chr', 'complex', 'dict', 'dir',
    'divmod', 'enumerate', 'filter', 'float', 'format',
    'frozenset', 'hasattr', 'hash', 'hex', 'id', 'int',
    'isinstance', 'issubclass', 'iter', 'len', 'list',
    'locals', 'map', 'max', 'memoryview', 'min', 'next',
    'oct', 'ord', 'pow', 'print', 'property', 'range',
    'repr', 'reversed', 'round', 'set', 'slice', 'sorted',
    'staticmethod', 'str', 'sum', 'tuple', 'type', 'vars',
    'zip', 'True', 'False', 'None'
]
FORBIDDEN_CALLS = {forbidden_calls!r}

def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    root = (name or '').split('.')[0]
    if root not in ALLOWED_MODULES:
        raise ImportError(f'Forbidden import: {{name}}')
    module = importlib.import_module(name)
    return module if fromlist else importlib.import_module(root)

safe_builtins = {{name: getattr(builtins, name) for name in SAFE_NAMES if hasattr(builtins, name)}}
safe_builtins['__import__'] = safe_import
safe_globals = {{'__builtins__': safe_builtins}}

for module_name in ALLOWED_MODULES:
    try:
        module = importlib.import_module(module_name)
        safe_globals[module_name] = module
        if module_name == 'pandas':
            safe_globals['pd'] = module
        elif module_name == 'numpy':
            safe_globals['np'] = module
        elif module_name == 'matplotlib':
            try:
                safe_globals['plt'] = importlib.import_module('matplotlib.pyplot')
            except Exception:
                pass
    except Exception:
        pass

code = sys.stdin.read()
stdout_capture = io.StringIO()

try:
    with contextlib.redirect_stdout(stdout_capture):
        exec(code, safe_globals)
    payload = {{
        'success': True,
        'output': stdout_capture.getvalue(),
        'error': None,
    }}
except Exception as exc:
    payload = {{
        'success': False,
        'output': stdout_capture.getvalue(),
        'error': f'{{type(exc).__name__}}: {{exc}}',
        'traceback': traceback.format_exc(),
    }}

print(json.dumps(payload))
"""


def run_code(code: str, timeout: int = 30) -> Dict[str, Any]:
    """Execute Python code in sandbox (convenience function).
    
    Args:
        code: Python code to execute
        timeout: Execution timeout
        
    Returns:
        Execution results
    """
    sandbox = PythonSandbox(timeout=timeout)
    return sandbox.execute(code)


def analyze_dataframe(df_code: str) -> Dict[str, Any]:
    """Analyze pandas DataFrame with common operations.
    
    Args:
        df_code: Code that creates/provides a DataFrame
        
    Returns:
        Analysis results
    """
    sandbox = PythonSandbox()
    
    # Execute dataframe code
    result = sandbox.execute(df_code)
    
    if not result['success']:
        return result
    
    # Get the last variable (assumed to be the DataFrame)
    variables = sandbox.get_available_variables()
    df_vars = [name for name, type_name in variables.items() if type_name == 'DataFrame']
    
    if not df_vars:
        return {
            'success': False,
            'error': 'No DataFrame found in results'
        }
    
    df_name = df_vars[-1]
    
    # Run analysis
    analysis_code = f"""
print(f"DataFrame: {df_name}")
print(f"Shape: {{{df_name}.shape}}")
print(f"Columns: {list({df_name}.columns)}")
print("\\nFirst 5 rows:")
print({df_name}.head())
print("\\nInfo:")
print({df_name}.info())
print("\\nDescription:")
print({df_name}.describe())
"""
    
    return sandbox.execute(analysis_code)

"""Safe Python code execution for BISSI.

Provides a sandboxed environment for running Python code with data analysis capabilities.
"""
import sys
import io
import contextlib
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
import traceback
import ast


class PythonSandbox:
    """Sandboxed Python execution environment."""
    
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
        self.globals = self._setup_globals()
    
    def _setup_globals(self) -> Dict[str, Any]:
        """Setup safe global namespace."""
        safe_globals = {
            '__builtins__': self._get_safe_builtins()
        }
        
        # Import allowed modules
        for module_name in self.ALLOWED_MODULES:
            try:
                module = __import__(module_name)
                safe_globals[module_name] = module
                # Common aliases
                if module_name == 'pandas':
                    safe_globals['pd'] = module
                elif module_name == 'numpy':
                    safe_globals['np'] = module
                elif module_name == 'matplotlib':
                    safe_globals['plt'] = module.pyplot
            except ImportError:
                pass
        
        return safe_globals
    
    def _get_safe_builtins(self) -> Dict[str, Any]:
        """Get safe builtin functions."""
        safe_builtins = {}
        
        # Whitelist safe builtins
        safe_names = [
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
        
        for name in safe_names:
            if name in __builtins__:
                safe_builtins[name] = __builtins__[name]
        
        return safe_builtins
    
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
                    if alias.name not in self.ALLOWED_MODULES:
                        return False, f"Forbidden import: {alias.name}"
            
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module not in self.ALLOWED_MODULES:
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
        
        # Capture stdout
        stdout_capture = io.StringIO()
        
        try:
            with contextlib.redirect_stdout(stdout_capture):
                # Execute with timeout (simplified - real timeout needs threading)
                exec(code, self.globals)
            
            output = stdout_capture.getvalue()
            
            # Record execution
            self.execution_history.append({
                'code': code[:100] + '...' if len(code) > 100 else code,
                'success': True
            })
            
            return {
                'success': True,
                'output': output,
                'error': None
            }
            
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            tb = traceback.format_exc()
            
            return {
                'success': False,
                'output': stdout_capture.getvalue(),
                'error': error_msg,
                'traceback': tb
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
        
        try:
            return eval(expression, self.globals)
        except Exception as e:
            raise ValueError(f"Evaluation error: {e}")
    
    def get_variable(self, name: str) -> Any:
        """Get variable from sandbox globals.
        
        Args:
            name: Variable name
            
        Returns:
            Variable value
        """
        return self.globals.get(name)
    
    def set_variable(self, name: str, value: Any) -> None:
        """Set variable in sandbox globals.
        
        Args:
            name: Variable name
            value: Value to set
        """
        self.globals[name] = value
    
    def get_available_variables(self) -> Dict[str, str]:
        """Get list of defined variables with their types."""
        variables = {}
        for name, value in self.globals.items():
            if not name.startswith('_'):
                variables[name] = type(value).__name__
        return variables


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

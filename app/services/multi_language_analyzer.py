"""
Multi-language code analyzer for detecting language-specific issues.
Supports: Python, JavaScript/TypeScript, Java, C#, Go, and more.
"""

import logging
import re
from typing import List, Dict, Set
from pathlib import Path

logger = logging.getLogger(__name__)


class LanguageAnalyzer:
    """Base class for language-specific analysis."""
    
    def __init__(self):
        self.language_name = "Unknown"
    
    def detect_errors(self, content: str, file_path: str, lines: List[str]) -> List[Dict]:
        """Detect errors in code. Override in subclasses."""
        return []
    
    def detect_security_issues(self, content: str, file_path: str, lines: List[str]) -> List[Dict]:
        """Detect security issues. Override in subclasses."""
        return []


class PythonAnalyzer(LanguageAnalyzer):
    """Python-specific code analyzer."""
    
    def __init__(self):
        super().__init__()
        self.language_name = "Python"
    
    def detect_errors(self, content: str, file_path: str, lines: List[str]) -> List[Dict]:
        """Detect Python-specific errors."""
        issues = []
        
        # Missing imports
        issues.extend(self._check_imports(lines, file_path))
        
        # Indentation issues
        issues.extend(self._check_indentation(lines, file_path))
        
        # Missing colons after statements
        issues.extend(self._check_missing_colons(lines, file_path))
        
        # Unclosed brackets/parentheses
        issues.extend(self._check_unclosed_brackets(content, lines, file_path))
        
        # HTTP calls without error handling
        issues.extend(self._check_http_errors(lines, file_path))
        
        # Missing timeouts
        issues.extend(self._check_timeouts(lines, file_path))
        
        # Infinite loops
        issues.extend(self._check_infinite_loops(lines, file_path))
        
        # Blocking calls
        issues.extend(self._check_blocking_calls(lines, file_path))
        
        return issues
    
    def detect_security_issues(self, content: str, file_path: str, lines: List[str]) -> List[Dict]:
        """Detect Python security issues."""
        issues = []
        
        # Hardcoded credentials
        issues.extend(self._check_hardcoded_secrets(lines, file_path))
        
        # SQL injection risks
        issues.extend(self._check_sql_injection(lines, file_path))
        
        # Eval/exec usage
        issues.extend(self._check_dangerous_functions(lines, file_path))
        
        # Insecure pickle
        issues.extend(self._check_insecure_pickle(lines, file_path))
        
        return issues
    
    def _check_imports(self, lines: List[str], file_path: str) -> List[Dict]:
        """Check for missing or incorrect imports."""
        issues = []
        
        for i, line in enumerate(lines, 1):
            if "from " in line and " import " in line:
                if line.strip().endswith(("import", "from")):
                    issues.append({
                        "file": file_path,
                        "line": i,
                        "issue": "Incomplete import statement",
                        "suggestion": "Complete the import statement (e.g., from module import name)"
                    })
        
        return issues
    
    def _check_indentation(self, lines: List[str], file_path: str) -> List[Dict]:
        """Check for indentation issues."""
        issues = []
        
        for i, line in enumerate(lines, 1):
            if line and line[0] == ' ' and not line[0].isalnum():
                if not (i == 1 or (i > 1 and (lines[i-2].rstrip().endswith(':') or lines[i-2].strip().startswith('#')))):
                    leading_spaces = len(line) - len(line.lstrip())
                    if leading_spaces % 4 != 0 and leading_spaces % 2 != 0:
                        issues.append({
                            "file": file_path,
                            "line": i,
                            "issue": "Inconsistent indentation (expected multiple of 4)",
                            "suggestion": "Use consistent indentation (4 spaces per level)"
                        })
        
        return issues
    
    def _check_missing_colons(self, lines: List[str], file_path: str) -> List[Dict]:
        """Check for missing colons after control statements."""
        issues = []
        
        patterns = [r"^\s*(if|elif|else|for|while|def|class|try|except|finally|with)\s+",
                   r"^\s*(if|elif|else|for|while|def|class|try|except|finally|with).*[^:]$"]
        
        for i, line in enumerate(lines, 1):
            stripped = line.rstrip()
            if stripped and not stripped.startswith('#'):
                for keyword in ['if ', 'elif ', 'else:', 'for ', 'while ', 'def ', 'class ', 'try:', 'except', 'finally:', 'with ']:
                    if stripped.startswith(keyword):
                        if not stripped.endswith(':'):
                            issues.append({
                                "file": file_path,
                                "line": i,
                                "issue": f"Missing colon after '{keyword.strip()}'",
                                "suggestion": "Add ':' at the end of the statement"
                            })
                        break
        
        return issues
    
    def _check_unclosed_brackets(self, content: str, lines: List[str], file_path: str) -> List[Dict]:
        """Check for unclosed brackets/parentheses."""
        issues = []
        
        open_brackets = {'(': ')', '[': ']', '{': '}'}
        stack = []
        
        for i, char in enumerate(content):
            if char in open_brackets:
                stack.append((char, i))
            elif char in open_brackets.values():
                if stack and open_brackets[stack[-1][0]] == char:
                    stack.pop()
                else:
                    line_num = content[:i].count('\n') + 1
                    issues.append({
                        "file": file_path,
                        "line": line_num,
                        "issue": f"Unmatched closing bracket '{char}'",
                        "suggestion": "Check for matching opening brackets"
                    })
        
        for bracket, pos in stack:
            line_num = content[:pos].count('\n') + 1
            issues.append({
                "file": file_path,
                "line": line_num,
                "issue": f"Unclosed bracket '{bracket}'",
                "suggestion": "Close the bracket with matching closing bracket"
            })
        
        return issues
    
    def _check_http_errors(self, lines: List[str], file_path: str) -> List[Dict]:
        """Check for HTTP calls without error handling."""
        issues = []
        
        for i, line in enumerate(lines, 1):
            if any(lib in line for lib in ['requests.', 'httpx.', 'urllib.request']):
                # Check if in try block
                context_start = max(0, i - 10)
                context = '\n'.join(lines[context_start:i])
                
                if 'try:' not in context:
                    issues.append({
                        "file": file_path,
                        "line": i,
                        "issue": "HTTP request without error handling",
                        "suggestion": "Wrap HTTP calls in try/except to handle timeouts and network errors"
                    })
        
        return issues
    
    def _check_timeouts(self, lines: List[str], file_path: str) -> List[Dict]:
        """Check for missing timeout specifications."""
        issues = []
        
        for i, line in enumerate(lines, 1):
            if any(lib in line for lib in ['requests.', 'httpx.']):
                if 'timeout=' not in line:
                    issues.append({
                        "file": file_path,
                        "line": i,
                        "issue": "HTTP request without explicit timeout",
                        "suggestion": "Add timeout parameter (e.g., timeout=30) to prevent hanging requests"
                    })
        
        return issues
    
    def _check_infinite_loops(self, lines: List[str], file_path: str) -> List[Dict]:
        """Check for infinite loops."""
        issues = []
        
        for i, line in enumerate(lines, 1):
            if re.match(r'\s*while\s+True\s*:', line):
                issues.append({
                    "file": file_path,
                    "line": i,
                    "issue": "Infinite loop detected (while True)",
                    "suggestion": "Add proper loop termination conditions or use break statements"
                })
        
        return issues
    
    def _check_blocking_calls(self, lines: List[str], file_path: str) -> List[Dict]:
        """Check for blocking calls in async code."""
        issues = []
        
        in_async = False
        for i, line in enumerate(lines, 1):
            if re.match(r'\s*async\s+def\s+', line):
                in_async = True
            elif re.match(r'\s*def\s+', line):
                in_async = False
            
            if in_async:
                blocking_patterns = [
                    ('time.sleep', 'blocking sleep'),
                    ('requests.', 'blocking requests library'),
                    ('urllib.request', 'blocking urllib'),
                ]
                
                for pattern, desc in blocking_patterns:
                    if pattern in line:
                        issues.append({
                            "file": file_path,
                            "line": i,
                            "issue": f"Blocking call in async function: {desc}",
                            "suggestion": "Use async alternatives (asyncio.sleep, httpx, etc.)"
                        })
        
        return issues
    
    def _check_hardcoded_secrets(self, lines: List[str], file_path: str) -> List[Dict]:
        """Check for hardcoded secrets."""
        issues = []
        
        secret_patterns = [
            (r'(password|passwd|pwd)\s*=\s*["\']([^"\']+)["\']', 'password'),
            (r'(api_key|apikey|api[-_]?secret)\s*=\s*["\']([^"\']+)["\']', 'API key'),
            (r'(token|oauth[-_]?token)\s*=\s*["\']([^"\']+)["\']', 'token'),
            (r'(database[-_]?url|db[-_]?url)\s*=\s*["\']([^"\']+)["\']', 'database URL'),
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, secret_type in secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append({
                        "file": file_path,
                        "line": i,
                        "issue": f"Hardcoded {secret_type} detected",
                        "suggestion": "Move secrets to environment variables or configuration files"
                    })
        
        return issues
    
    def _check_sql_injection(self, lines: List[str], file_path: str) -> List[Dict]:
        """Check for SQL injection vulnerabilities."""
        issues = []
        
        for i, line in enumerate(lines, 1):
            # String concatenation in SQL
            if re.search(r'["\']SELECT|INSERT|UPDATE|DELETE', line) and '+' in line:
                issues.append({
                    "file": file_path,
                    "line": i,
                    "issue": "Potential SQL injection via string concatenation",
                    "suggestion": "Use parameterized queries or ORM instead of string concatenation"
                })
        
        return issues
    
    def _check_dangerous_functions(self, lines: List[str], file_path: str) -> List[Dict]:
        """Check for dangerous function usage."""
        issues = []
        
        dangerous = [('eval(', 'eval'), ('exec(', 'exec'), ('__import__', '__import__')]
        
        for i, line in enumerate(lines, 1):
            for func, name in dangerous:
                if func in line:
                    issues.append({
                        "file": file_path,
                        "line": i,
                        "issue": f"Dangerous function '{name}' used",
                        "suggestion": "Avoid using eval/exec as they pose security risks. Use safer alternatives"
                    })
        
        return issues
    
    def _check_insecure_pickle(self, lines: List[str], file_path: str) -> List[Dict]:
        """Check for insecure pickle usage."""
        issues = []
        
        for i, line in enumerate(lines, 1):
            if 'pickle.load' in line or 'pickle.loads' in line:
                issues.append({
                    "file": file_path,
                    "line": i,
                    "issue": "Insecure pickle.load() usage",
                    "suggestion": "pickle can execute arbitrary code. Use safer serialization like JSON or consider alternatives"
                })
        
        return issues


class JavaScriptTypeScriptAnalyzer(LanguageAnalyzer):
    """JavaScript/TypeScript analyzer."""
    
    def __init__(self):
        super().__init__()
        self.language_name = "JavaScript/TypeScript"
    
    def detect_errors(self, content: str, file_path: str, lines: List[str]) -> List[Dict]:
        """Detect JavaScript/TypeScript errors."""
        issues = []
        
        issues.extend(self._check_missing_semicolons(lines, file_path))
        issues.extend(self._check_promise_errors(lines, file_path))
        issues.extend(self._check_async_errors(lines, file_path))
        issues.extend(self._check_callback_errors(lines, file_path))
        issues.extend(self._check_unclosed_brackets(content, lines, file_path))
        issues.extend(self._check_unused_vars(lines, file_path))
        issues.extend(self._check_console_logs(lines, file_path))
        
        return issues
    
    def detect_security_issues(self, content: str, file_path: str, lines: List[str]) -> List[Dict]:
        """Detect JavaScript/TypeScript security issues."""
        issues = []
        
        issues.extend(self._check_eval_usage(lines, file_path))
        issues.extend(self._check_hardcoded_secrets_js(lines, file_path))
        issues.extend(self._check_dangerous_methods(lines, file_path))
        
        return issues
    
    def _check_missing_semicolons(self, lines: List[str], file_path: str) -> List[Dict]:
        """Check for missing semicolons in JavaScript."""
        issues = []
        
        for i, line in enumerate(lines, 1):
            stripped = line.rstrip()
            if stripped and not any(stripped.endswith(x) for x in ['{', '}', ':', ';', ',', '/*', '*/', '//', '?', '&&', '||']):
                if any(keyword in stripped for keyword in ['const ', 'let ', 'var ', 'return ', 'throw ']):
                    issues.append({
                        "file": file_path,
                        "line": i,
                        "issue": "Missing semicolon at end of statement",
                        "suggestion": "Add semicolon at the end of the statement (automatic semicolon insertion may cause issues)"
                    })
        
        return issues
    
    def _check_promise_errors(self, lines: List[str], file_path: str) -> List[Dict]:
        """Check for unhandled promises."""
        issues = []
        
        for i, line in enumerate(lines, 1):
            if '.then(' in line or '.catch' in line:
                if '.catch(' not in line and i+1 < len(lines):
                    if '.catch(' not in lines[i]:
                        issues.append({
                            "file": file_path,
                            "line": i,
                            "issue": "Promise without .catch() handler",
                            "suggestion": "Add .catch() to handle promise rejections"
                        })
        
        return issues
    
    def _check_async_errors(self, lines: List[str], file_path: str) -> List[Dict]:
        """Check for async/await errors."""
        issues = []
        
        for i, line in enumerate(lines, 1):
            if 'await' in line and 'async' not in ''.join(lines[max(0, i-10):i]):
                issues.append({
                    "file": file_path,
                    "line": i,
                    "issue": "await used outside async function",
                    "suggestion": "Mark the function as 'async' to use await"
                })
        
        return issues
    
    def _check_callback_errors(self, lines: List[str], file_path: str) -> List[Dict]:
        """Check for callback hell."""
        issues = []
        
        brace_depth = 0
        for i, line in enumerate(lines, 1):
            brace_depth += line.count('{') - line.count('}')
            if brace_depth > 5:
                issues.append({
                    "file": file_path,
                    "line": i,
                    "issue": "Deeply nested callbacks detected (Callback Hell)",
                    "suggestion": "Use promises, async/await, or extract functions to reduce nesting"
                })
        
        return issues
    
    def _check_unclosed_brackets(self, content: str, lines: List[str], file_path: str) -> List[Dict]:
        """Check for unclosed brackets."""
        issues = []
        
        open_brackets = {'(': ')', '[': ']', '{': '}'}
        stack = []
        
        for i, char in enumerate(content):
            if char in open_brackets:
                stack.append((char, i))
            elif char in open_brackets.values():
                if stack and open_brackets[stack[-1][0]] == char:
                    stack.pop()
                else:
                    line_num = content[:i].count('\n') + 1
                    issues.append({
                        "file": file_path,
                        "line": line_num,
                        "issue": f"Unmatched closing bracket '{char}'",
                        "suggestion": "Check for matching opening brackets"
                    })
        
        for bracket, pos in stack:
            line_num = content[:pos].count('\n') + 1
            issues.append({
                "file": file_path,
                "line": line_num,
                "issue": f"Unclosed bracket '{bracket}'",
                "suggestion": "Close the bracket with matching closing bracket"
            })
        
        return issues
    
    def _check_unused_vars(self, lines: List[str], file_path: str) -> List[Dict]:
        """Check for unused variables."""
        issues = []
        
        for i, line in enumerate(lines, 1):
            if re.match(r'\s*(const|let|var)\s+\w+\s*=', line):
                match = re.search(r'\b(const|let|var)\s+(\w+)\s*=', line)
                if match:
                    var_name = match.group(2)
                    rest_of_code = ''.join(lines[i:])
                    if f' {var_name}' not in rest_of_code and f'({var_name}' not in rest_of_code:
                        issues.append({
                            "file": file_path,
                            "line": i,
                            "issue": f"Unused variable '{var_name}'",
                            "suggestion": "Remove unused variable or use it in the code"
                        })
        
        return issues
    
    def _check_console_logs(self, lines: List[str], file_path: str) -> List[Dict]:
        """Check for console.log in production code."""
        issues = []
        
        for i, line in enumerate(lines, 1):
            if 'console.log' in line:
                issues.append({
                    "file": file_path,
                    "line": i,
                    "issue": "console.log found in code",
                    "suggestion": "Remove console.log statements before production or use proper logging library"
                })
        
        return issues
    
    def _check_eval_usage(self, lines: List[str], file_path: str) -> List[Dict]:
        """Check for eval usage."""
        issues = []
        
        for i, line in enumerate(lines, 1):
            if 'eval(' in line:
                issues.append({
                    "file": file_path,
                    "line": i,
                    "issue": "eval() usage detected",
                    "suggestion": "Avoid eval() as it executes arbitrary code and is a security risk"
                })
        
        return issues
    
    def _check_hardcoded_secrets_js(self, lines: List[str], file_path: str) -> List[Dict]:
        """Check for hardcoded secrets in JavaScript."""
        issues = []
        
        for i, line in enumerate(lines, 1):
            if any(secret in line for secret in ['API_KEY', 'apiKey', 'api_key', 'password', 'secret']):
                if '=' in line and any(quote in line for quote in ['"', "'"]):
                    issues.append({
                        "file": file_path,
                        "line": i,
                        "issue": "Potential hardcoded secret detected",
                        "suggestion": "Move secrets to environment variables or configuration files"
                    })
        
        return issues
    
    def _check_dangerous_methods(self, lines: List[str], file_path: str) -> List[Dict]:
        """Check for dangerous methods."""
        issues = []
        
        dangerous = [
            ('innerHTML', 'innerHTML (XSS vulnerability)'),
            ('.eval(', 'eval method'),
            ('Function(', 'Function constructor'),
        ]
        
        for i, line in enumerate(lines, 1):
            for method, desc in dangerous:
                if method in line:
                    issues.append({
                        "file": file_path,
                        "line": i,
                        "issue": f"Potentially dangerous method: {desc}",
                        "suggestion": "Use safer alternatives (e.g., textContent instead of innerHTML, JSON.parse instead of eval)"
                    })
        
        return issues


class JavaAnalyzer(LanguageAnalyzer):
    """Java analyzer."""
    
    def __init__(self):
        super().__init__()
        self.language_name = "Java"
    
    def detect_errors(self, content: str, file_path: str, lines: List[str]) -> List[Dict]:
        """Detect Java errors."""
        issues = []
        
        issues.extend(self._check_missing_semicolons(lines, file_path))
        issues.extend(self._check_unclosed_brackets(content, lines, file_path))
        issues.extend(self._check_null_pointer(lines, file_path))
        issues.extend(self._check_exception_handling(lines, file_path))
        
        return issues
    
    def detect_security_issues(self, content: str, file_path: str, lines: List[str]) -> List[Dict]:
        """Detect Java security issues."""
        issues = []
        
        issues.extend(self._check_sql_injection(lines, file_path))
        issues.extend(self._check_hardcoded_secrets(lines, file_path))
        
        return issues
    
    def _check_missing_semicolons(self, lines: List[str], file_path: str) -> List[Dict]:
        """Check for missing semicolons."""
        issues = []
        
        for i, line in enumerate(lines, 1):
            stripped = line.rstrip()
            if stripped and not any(stripped.endswith(x) for x in ['{', '}', ';', '/*', '*/', '//']):
                if any(keyword in stripped for keyword in ['int ', 'String ', 'boolean ', 'return ', 'throw ']):
                    issues.append({
                        "file": file_path,
                        "line": i,
                        "issue": "Missing semicolon at end of statement",
                        "suggestion": "Add semicolon at the end of the statement"
                    })
        
        return issues
    
    def _check_unclosed_brackets(self, content: str, lines: List[str], file_path: str) -> List[Dict]:
        """Check for unclosed brackets."""
        issues = []
        
        open_brackets = {'(': ')', '[': ']', '{': '}'}
        stack = []
        
        for i, char in enumerate(content):
            if char in open_brackets:
                stack.append((char, i))
            elif char in open_brackets.values():
                if stack and open_brackets[stack[-1][0]] == char:
                    stack.pop()
        
        for bracket, pos in stack:
            line_num = content[:pos].count('\n') + 1
            issues.append({
                "file": file_path,
                "line": line_num,
                "issue": f"Unclosed bracket '{bracket}'",
                "suggestion": "Close the bracket with matching closing bracket"
            })
        
        return issues
    
    def _check_null_pointer(self, lines: List[str], file_path: str) -> List[Dict]:
        """Check for potential null pointer exceptions."""
        issues = []
        
        for i, line in enumerate(lines, 1):
            if '.' in line and 'null' not in line and 'if' not in line:
                issues.append({
                    "file": file_path,
                    "line": i,
                    "issue": "Potential null pointer exception",
                    "suggestion": "Add null checks before accessing object members"
                })
        
        return issues
    
    def _check_exception_handling(self, lines: List[str], file_path: str) -> List[Dict]:
        """Check for improper exception handling."""
        issues = []
        
        for i, line in enumerate(lines, 1):
            if 'try {' in line:
                # Check if there's a catch block nearby
                context = '\n'.join(lines[i:min(i+10, len(lines))])
                if 'catch' not in context:
                    issues.append({
                        "file": file_path,
                        "line": i,
                        "issue": "Try block without catch handler",
                        "suggestion": "Add catch block to handle exceptions"
                    })
        
        return issues
    
    def _check_sql_injection(self, lines: List[str], file_path: str) -> List[Dict]:
        """Check for SQL injection."""
        issues = []
        
        for i, line in enumerate(lines, 1):
            if 'executeQuery' in line or 'execute(' in line:
                if '+' in line or '\"' in line:
                    issues.append({
                        "file": file_path,
                        "line": i,
                        "issue": "Potential SQL injection",
                        "suggestion": "Use PreparedStatement instead of string concatenation"
                    })
        
        return issues
    
    def _check_hardcoded_secrets(self, lines: List[str], file_path: str) -> List[Dict]:
        """Check for hardcoded secrets."""
        issues = []
        
        for i, line in enumerate(lines, 1):
            if any(secret in line for secret in ['password', 'api_key', 'token', 'secret']):
                if '=' in line and '"' in line:
                    issues.append({
                        "file": file_path,
                        "line": i,
                        "issue": "Hardcoded secret detected",
                        "suggestion": "Use secure configuration or environment variables"
                    })
        
        return issues


class CSharpAnalyzer(LanguageAnalyzer):
    """C# analyzer."""
    
    def __init__(self):
        super().__init__()
        self.language_name = "C#"
    
    def detect_errors(self, content: str, file_path: str, lines: List[str]) -> List[Dict]:
        """Detect C# errors."""
        issues = []
        
        issues.extend(self._check_unclosed_brackets(content, lines, file_path))
        issues.extend(self._check_null_reference(lines, file_path))
        issues.extend(self._check_async_errors(lines, file_path))
        
        return issues
    
    def detect_security_issues(self, content: str, file_path: str, lines: List[str]) -> List[Dict]:
        """Detect C# security issues."""
        issues = []
        
        issues.extend(self._check_hardcoded_secrets(lines, file_path))
        
        return issues
    
    def _check_unclosed_brackets(self, content: str, lines: List[str], file_path: str) -> List[Dict]:
        """Check for unclosed brackets."""
        issues = []
        
        open_brackets = {'(': ')', '[': ']', '{': '}'}
        stack = []
        
        for i, char in enumerate(content):
            if char in open_brackets:
                stack.append((char, i))
            elif char in open_brackets.values():
                if stack and open_brackets[stack[-1][0]] == char:
                    stack.pop()
        
        for bracket, pos in stack:
            line_num = content[:pos].count('\n') + 1
            issues.append({
                "file": file_path,
                "line": line_num,
                "issue": f"Unclosed bracket '{bracket}'",
                "suggestion": "Close the bracket"
            })
        
        return issues
    
    def _check_null_reference(self, lines: List[str], file_path: str) -> List[Dict]:
        """Check for potential null references."""
        issues = []
        
        for i, line in enumerate(lines, 1):
            if '?.' not in line and '?[' not in line and '.' in line:
                if any(x in line for x in ['var ', 'new ', 'return ']):
                    issues.append({
                        "file": file_path,
                        "line": i,
                        "issue": "Potential null reference exception",
                        "suggestion": "Use null-conditional operators (?.) or null-coalescing (??) operators"
                    })
        
        return issues
    
    def _check_async_errors(self, lines: List[str], file_path: str) -> List[Dict]:
        """Check for async/await errors."""
        issues = []
        
        for i, line in enumerate(lines, 1):
            if 'await' in line and 'async' not in ''.join(lines[max(0, i-10):i]):
                issues.append({
                    "file": file_path,
                    "line": i,
                    "issue": "await used in non-async method",
                    "suggestion": "Mark the method as 'async' or use .Result (with caution)"
                })
        
        return issues
    
    def _check_hardcoded_secrets(self, lines: List[str], file_path: str) -> List[Dict]:
        """Check for hardcoded secrets."""
        issues = []
        
        for i, line in enumerate(lines, 1):
            if any(secret in line for secret in ['password', 'apiKey', 'api_key', 'token', 'secret']):
                if '=' in line and '"' in line:
                    issues.append({
                        "file": file_path,
                        "line": i,
                        "issue": "Hardcoded secret detected",
                        "suggestion": "Use configuration or User Secrets for sensitive data"
                    })
        
        return issues


class GoAnalyzer(LanguageAnalyzer):
    """Go analyzer."""
    
    def __init__(self):
        super().__init__()
        self.language_name = "Go"
    
    def detect_errors(self, content: str, file_path: str, lines: List[str]) -> List[Dict]:
        """Detect Go errors."""
        issues = []
        
        issues.extend(self._check_unclosed_brackets(content, lines, file_path))
        issues.extend(self._check_error_handling(lines, file_path))
        issues.extend(self._check_goroutine_leaks(lines, file_path))
        
        return issues
    
    def detect_security_issues(self, content: str, file_path: str, lines: List[str]) -> List[Dict]:
        """Detect Go security issues."""
        issues = []
        
        issues.extend(self._check_hardcoded_secrets(lines, file_path))
        
        return issues
    
    def _check_unclosed_brackets(self, content: str, lines: List[str], file_path: str) -> List[Dict]:
        """Check for unclosed brackets."""
        issues = []
        
        open_brackets = {'(': ')', '[': ']', '{': '}'}
        stack = []
        
        for i, char in enumerate(content):
            if char in open_brackets:
                stack.append((char, i))
            elif char in open_brackets.values():
                if stack and open_brackets[stack[-1][0]] == char:
                    stack.pop()
        
        for bracket, pos in stack:
            line_num = content[:pos].count('\n') + 1
            issues.append({
                "file": file_path,
                "line": line_num,
                "issue": f"Unclosed bracket '{bracket}'",
                "suggestion": "Close the bracket"
            })
        
        return issues
    
    def _check_error_handling(self, lines: List[str], file_path: str) -> List[Dict]:
        """Check for unhandled errors."""
        issues = []
        
        for i, line in enumerate(lines, 1):
            if 'err :=' in line or 'err =' in line:
                # Check next line for error check
                if i < len(lines) and 'if err' not in lines[i]:
                    issues.append({
                        "file": file_path,
                        "line": i,
                        "issue": "Unhandled error variable",
                        "suggestion": "Check error with 'if err != nil' block"
                    })
        
        return issues
    
    def _check_goroutine_leaks(self, lines: List[str], file_path: str) -> List[Dict]:
        """Check for goroutine leaks."""
        issues = []
        
        for i, line in enumerate(lines, 1):
            if 'go ' in line:
                # Check if there's synchronization nearby
                context = '\n'.join(lines[max(0, i-5):min(i+5, len(lines))])
                if 'wg.Wait()' not in context and 'channel' not in context:
                    issues.append({
                        "file": file_path,
                        "line": i,
                        "issue": "Goroutine without synchronization mechanism",
                        "suggestion": "Use WaitGroup, channels, or context to avoid goroutine leaks"
                    })
        
        return issues
    
    def _check_hardcoded_secrets(self, lines: List[str], file_path: str) -> List[Dict]:
        """Check for hardcoded secrets."""
        issues = []
        
        for i, line in enumerate(lines, 1):
            if any(secret in line for secret in ['password', 'api_key', 'token', 'secret']):
                if '=' in line and '"' in line:
                    issues.append({
                        "file": file_path,
                        "line": i,
                        "issue": "Hardcoded secret detected",
                        "suggestion": "Use environment variables or configuration files"
                    })
        
        return issues


class MultiLanguageCodeAnalyzer:
    """Multi-language code analyzer supporting multiple programming languages."""
    
    # Mapping of file extensions to analyzers
    analyzers_map = {
        '.py': PythonAnalyzer,
        '.js': JavaScriptTypeScriptAnalyzer,
        '.ts': JavaScriptTypeScriptAnalyzer,
        '.jsx': JavaScriptTypeScriptAnalyzer,
        '.tsx': JavaScriptTypeScriptAnalyzer,
        '.java': JavaAnalyzer,
        '.cs': CSharpAnalyzer,
        '.go': GoAnalyzer,
    }
    
    def __init__(self):
        self.analyzers = {ext: analyzer_class() for ext, analyzer_class in self.analyzers_map.items()}
    
    def get_analyzer(self, file_path: str):
        """Get appropriate analyzer for file."""
        ext = Path(file_path).suffix.lower()
        return self.analyzers.get(ext)
    
    def analyze(self, content: str, file_path: str) -> List[Dict]:
        """Analyze code file and return issues."""
        from pathlib import Path
        
        analyzer = self.get_analyzer(file_path)
        if not analyzer:
            logger.warning(f"No analyzer found for {file_path}")
            return []
        
        lines = content.split('\n')
        issues = []
        
        # Detect language-specific errors
        issues.extend(analyzer.detect_errors(content, file_path, lines))
        
        # Detect security issues
        issues.extend(analyzer.detect_security_issues(content, file_path, lines))
        
        return issues

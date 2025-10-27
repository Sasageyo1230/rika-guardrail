# phase3/l2-autonomy/agents/craft.py
# Craft Agent v0 - Code Creation and Modification

import asyncio
import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import structlog

logger = structlog.get_logger()

class CraftAgent:
    """Craft agent for code creation and modification"""
    
    def __init__(self, workspace_root: str = None):
        self.workspace_root = workspace_root or os.getcwd()
        self.agent_id = "craft-v0"
        self.capabilities = [
            "code_modification",
            "file_creation",
            "refactoring",
            "bug_fixing",
            "formatting",
            "documentation"
        ]
        self.changes_made = []
        self.backup_dir = None
    
    async def execute_task(self, task_description: str, scope: str, bounds: Dict) -> Dict[str, Any]:
        """Execute crafting task"""
        logger.info(f"Craft agent executing: {task_description}")
        
        start_time = datetime.utcnow()
        result = {
            "agent_id": self.agent_id,
            "task_description": task_description,
            "scope": scope,
            "start_time": start_time.isoformat(),
            "success": False,
            "files_changed": [],
            "changes_made": [],
            "backup_location": None,
            "error": None
        }
        
        try:
            # Create backup before making changes
            self.backup_dir = await self._create_backup()
            result["backup_location"] = self.backup_dir
            
            # Parse task and determine actions
            actions = self._parse_task(task_description, scope)
            
            # Execute actions within bounds
            for action in actions:
                if not self._check_bounds(action, bounds):
                    logger.warning(f"Action {action['type']} skipped - exceeds bounds")
                    continue
                
                action_result = await self._execute_action(action, bounds)
                if action_result.get("success"):
                    result["changes_made"].append(action_result)
                    result["files_changed"].extend(action_result.get("files_modified", []))
            
            # Verify changes don't break basic syntax
            if await self._verify_changes(result["files_changed"]):
                result["success"] = True
            else:
                # Rollback on verification failure
                await self._rollback_changes()
                result["error"] = "Changes failed verification - rolled back"
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Craft agent failed: {e}")
            
            # Attempt rollback
            try:
                await self._rollback_changes()
            except:
                logger.error("Rollback also failed")
        
        result["end_time"] = datetime.utcnow().isoformat()
        # Remove duplicates from files_changed
        result["files_changed"] = list(set(result["files_changed"]))
        
        return result
    
    def _parse_task(self, description: str, scope: str) -> List[Dict]:
        """Parse task description into actionable items"""
        actions = []
        description_lower = description.lower()
        
        # Code modification actions
        if any(keyword in description_lower for keyword in ["refactor", "improve", "optimize"]):
            actions.append({
                "type": "refactor_code",
                "target_pattern": self._extract_target_files(description),
                "focus": self._extract_refactor_focus(description)
            })
        
        # Bug fixing
        if any(keyword in description_lower for keyword in ["fix", "bug", "error", "issue"]):
            actions.append({
                "type": "fix_bugs",
                "target_pattern": self._extract_target_files(description),
                "issue_keywords": self._extract_bug_keywords(description)
            })
        
        # Formatting
        if any(keyword in description_lower for keyword in ["format", "style", "clean"]):
            actions.append({
                "type": "format_code",
                "target_pattern": self._extract_target_files(description),
                "formatter": self._detect_formatter(description)
            })
        
        # Documentation
        if any(keyword in description_lower for keyword in ["document", "comment", "docstring"]):
            actions.append({
                "type": "add_documentation",
                "target_pattern": self._extract_target_files(description),
                "doc_type": "docstrings" if "docstring" in description_lower else "comments"
            })
        
        # File creation
        if any(keyword in description_lower for keyword in ["create", "new file", "add file"]):
            actions.append({
                "type": "create_file",
                "filename": self._extract_filename(description),
                "template": self._extract_template(description)
            })
        
        # Default action if no specific keywords
        if not actions:
            actions.append({
                "type": "general_improvement",
                "target_pattern": "*.py",  # Default to Python files
                "improvements": ["formatting", "simple_refactor"]
            })
        
        return actions
    
    def _extract_target_files(self, description: str) -> str:
        """Extract file pattern from description"""
        # Look for file extensions or patterns
        patterns = {
            "python": "*.py",
            "javascript": "*.js", 
            "typescript": "*.ts",
            "css": "*.css",
            "html": "*.html",
            "json": "*.json"
        }
        
        description_lower = description.lower()
        for lang, pattern in patterns.items():
            if lang in description_lower:
                return pattern
        
        # Look for specific file mentions
        words = description.split()
        for word in words:
            if '.' in word and any(ext in word for ext in ['.py', '.js', '.ts', '.css', '.html']):
                return word
        
        return "*.py"  # Default
    
    def _extract_refactor_focus(self, description: str) -> str:
        """Extract what aspect to focus on during refactoring"""
        description_lower = description.lower()
        
        if "performance" in description_lower:
            return "performance"
        elif "readability" in description_lower:
            return "readability"
        elif "structure" in description_lower:
            return "structure"
        elif "duplicate" in description_lower:
            return "deduplication"
        else:
            return "general"
    
    def _extract_bug_keywords(self, description: str) -> List[str]:
        """Extract keywords related to bugs"""
        keywords = []
        bug_indicators = ["error", "exception", "crash", "fail", "broken", "issue"]
        
        words = description.lower().split()
        for word in words:
            if word in bug_indicators:
                keywords.append(word)
        
        return keywords or ["general_bugs"]
    
    def _detect_formatter(self, description: str) -> str:
        """Detect which formatter to use"""
        description_lower = description.lower()
        
        if "black" in description_lower:
            return "black"
        elif "prettier" in description_lower:
            return "prettier"
        elif "autopep8" in description_lower:
            return "autopep8"
        else:
            return "basic"  # Basic formatting
    
    def _extract_filename(self, description: str) -> str:
        """Extract filename from creation request"""
        words = description.split()
        for word in words:
            if '.' in word and any(ext in word for ext in ['.py', '.js', '.ts', '.css', '.html', '.json', '.md']):
                return word
        
        # Default filename based on context
        return "new_file.py"
    
    def _extract_template(self, description: str) -> str:
        """Extract template type from description"""
        description_lower = description.lower()
        
        if "class" in description_lower:
            return "class"
        elif "function" in description_lower:
            return "function"
        elif "test" in description_lower:
            return "test"
        elif "config" in description_lower:
            return "config"
        else:
            return "basic"
    
    def _check_bounds(self, action: Dict, bounds: Dict) -> bool:
        """Check if action is within allowed bounds"""
        max_files = bounds.get("max_files", 5)
        max_lines = bounds.get("max_lines_per_file", 100)
        
        # Estimate impact
        if action["type"] == "create_file":
            # Creating files is within bounds if under file limit
            return len(self.changes_made) < max_files
        
        # For modifications, assume they're within bounds for safe operations
        if action.get("target_pattern", "").startswith("*"):
            # Wildcard patterns - limit to max_files
            return True
        
        return True
    
    async def _execute_action(self, action: Dict, bounds: Dict) -> Dict[str, Any]:
        """Execute a specific action"""
        action_type = action["type"]
        
        if action_type == "refactor_code":
            return await self._refactor_code(action, bounds)
        elif action_type == "fix_bugs":
            return await self._fix_bugs(action, bounds)
        elif action_type == "format_code":
            return await self._format_code(action, bounds)
        elif action_type == "add_documentation":
            return await self._add_documentation(action, bounds)
        elif action_type == "create_file":
            return await self._create_file(action, bounds)
        else:
            return await self._general_improvement(action, bounds)
    
    async def _refactor_code(self, action: Dict, bounds: Dict) -> Dict[str, Any]:
        """Refactor code based on focus area"""
        result = {
            "action": "refactor_code",
            "success": False,
            "files_modified": [],
            "changes": []
        }
        
        try:
            pattern = action["target_pattern"]
            focus = action.get("focus", "general")
            max_files = bounds.get("max_files", 5)
            
            # Find target files
            target_files = list(Path(self.workspace_root).rglob(pattern))[:max_files]
            
            for file_path in target_files:
                try:
                    changes = await self._refactor_single_file(file_path, focus, bounds)
                    if changes:
                        result["files_modified"].append(str(file_path.relative_to(Path(self.workspace_root))))
                        result["changes"].extend(changes)
                except Exception as e:
                    logger.warning(f"Failed to refactor {file_path}: {e}")
                    continue
            
            result["success"] = len(result["files_modified"]) > 0
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    async def _refactor_single_file(self, file_path: Path, focus: str, bounds: Dict) -> List[str]:
        """Refactor a single file"""
        changes = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            lines = original_content.split('\n')
            new_lines = lines.copy()
            
            max_lines = bounds.get("max_lines_per_file", 100)
            if len(lines) > max_lines:
                # Skip files that are too large
                return []
            
            if focus == "performance":
                # Simple performance improvements
                changes.extend(self._apply_performance_fixes(new_lines))
            elif focus == "readability":
                # Readability improvements
                changes.extend(self._apply_readability_fixes(new_lines))
            elif focus == "structure":
                # Structural improvements
                changes.extend(self._apply_structure_fixes(new_lines))
            else:
                # General improvements
                changes.extend(self._apply_general_fixes(new_lines))
            
            # Write back if changes were made
            if changes:
                new_content = '\n'.join(new_lines)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
        
        except Exception as e:
            logger.error(f"Failed to refactor file {file_path}: {e}")
        
        return changes
    
    def _apply_performance_fixes(self, lines: List[str]) -> List[str]:
        """Apply simple performance improvements"""
        changes = []
        
        for i, line in enumerate(lines):
            # Example: Replace inefficient list operations
            if 'list(range(' in line and 'for' in line:
                # This is a simple example - real implementation would be more sophisticated
                changes.append(f"Line {i+1}: Potential range optimization opportunity")
        
        return changes
    
    def _apply_readability_fixes(self, lines: List[str]) -> List[str]:
        """Apply readability improvements"""
        changes = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Add spacing around operators
            if '=' in stripped and not any(op in stripped for op in ['==', '!=', '<=', '>=']):
                if not ' = ' in stripped:
                    lines[i] = line.replace('=', ' = ', 1)
                    changes.append(f"Line {i+1}: Added spacing around assignment operator")
            
            # Remove trailing whitespace
            if line != line.rstrip():
                lines[i] = line.rstrip()
                changes.append(f"Line {i+1}: Removed trailing whitespace")
        
        return changes
    
    def _apply_structure_fixes(self, lines: List[str]) -> List[str]:
        """Apply structural improvements"""
        changes = []
        
        # Simple structural improvements like consistent indentation
        for i, line in enumerate(lines):
            if line.startswith('\t'):
                # Convert tabs to spaces
                lines[i] = line.replace('\t', '    ')
                changes.append(f"Line {i+1}: Converted tabs to spaces")
        
        return changes
    
    def _apply_general_fixes(self, lines: List[str]) -> List[str]:
        """Apply general code improvements"""
        changes = []
        
        # Combine all improvement types
        changes.extend(self._apply_readability_fixes(lines))
        changes.extend(self._apply_structure_fixes(lines))
        
        return changes
    
    async def _fix_bugs(self, action: Dict, bounds: Dict) -> Dict[str, Any]:
        """Fix common bugs in code"""
        result = {
            "action": "fix_bugs",
            "success": False,
            "files_modified": [],
            "bugs_fixed": []
        }
        
        try:
            pattern = action["target_pattern"]
            max_files = bounds.get("max_files", 5)
            
            target_files = list(Path(self.workspace_root).rglob(pattern))[:max_files]
            
            for file_path in target_files:
                try:
                    bugs_fixed = await self._fix_bugs_in_file(file_path, bounds)
                    if bugs_fixed:
                        result["files_modified"].append(str(file_path.relative_to(Path(self.workspace_root))))
                        result["bugs_fixed"].extend(bugs_fixed)
                except Exception as e:
                    logger.warning(f"Failed to fix bugs in {file_path}: {e}")
            
            result["success"] = len(result["bugs_fixed"]) > 0
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    async def _fix_bugs_in_file(self, file_path: Path, bounds: Dict) -> List[str]:
        """Fix bugs in a single file"""
        bugs_fixed = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Common bug patterns and fixes
            bug_fixes = [
                (r'except:', 'except Exception:'),  # Bare except
                (r'== None', 'is None'),  # Equality with None
                (r'!= None', 'is not None'),  # Inequality with None
            ]
            
            for pattern, replacement in bug_fixes:
                if pattern in content:
                    content = content.replace(pattern, replacement)
                    bugs_fixed.append(f"Fixed: {pattern} -> {replacement}")
            
            # Write back if changes were made
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
        
        except Exception as e:
            logger.error(f"Failed to fix bugs in {file_path}: {e}")
        
        return bugs_fixed
    
    async def _format_code(self, action: Dict, bounds: Dict) -> Dict[str, Any]:
        """Format code using specified formatter"""
        result = {
            "action": "format_code",
            "success": False,
            "files_modified": [],
            "formatter_used": action.get("formatter", "basic")
        }
        
        try:
            pattern = action["target_pattern"]
            formatter = action.get("formatter", "basic")
            max_files = bounds.get("max_files", 5)
            
            target_files = list(Path(self.workspace_root).rglob(pattern))[:max_files]
            
            for file_path in target_files:
                try:
                    if await self._format_single_file(file_path, formatter):
                        result["files_modified"].append(str(file_path.relative_to(Path(self.workspace_root))))
                except Exception as e:
                    logger.warning(f"Failed to format {file_path}: {e}")
            
            result["success"] = len(result["files_modified"]) > 0
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    async def _format_single_file(self, file_path: Path, formatter: str) -> bool:
        """Format a single file"""
        try:
            if formatter == "black" and file_path.suffix == ".py":
                # Try to use black if available
                proc = await asyncio.create_subprocess_exec(
                    "black", "--check", "--diff", str(file_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.communicate()
                
                if proc.returncode != 0:  # File needs formatting
                    proc = await asyncio.create_subprocess_exec(
                        "black", str(file_path),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await proc.communicate()
                    return proc.returncode == 0
                
            else:
                # Basic formatting
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Basic formatting improvements
                lines = content.split('\n')
                formatted_lines = []
                
                for line in lines:
                    # Remove trailing whitespace
                    formatted_line = line.rstrip()
                    formatted_lines.append(formatted_line)
                
                formatted_content = '\n'.join(formatted_lines)
                
                if formatted_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(formatted_content)
                    return True
        
        except Exception as e:
            logger.error(f"Failed to format {file_path}: {e}")
        
        return False
    
    async def _add_documentation(self, action: Dict, bounds: Dict) -> Dict[str, Any]:
        """Add documentation to code"""
        result = {
            "action": "add_documentation",
            "success": False,
            "files_modified": [],
            "docs_added": []
        }
        
        try:
            pattern = action["target_pattern"]
            doc_type = action.get("doc_type", "comments")
            max_files = bounds.get("max_files", 5)
            
            target_files = list(Path(self.workspace_root).rglob(pattern))[:max_files]
            
            for file_path in target_files:
                try:
                    docs_added = await self._add_docs_to_file(file_path, doc_type, bounds)
                    if docs_added:
                        result["files_modified"].append(str(file_path.relative_to(Path(self.workspace_root))))
                        result["docs_added"].extend(docs_added)
                except Exception as e:
                    logger.warning(f"Failed to add docs to {file_path}: {e}")
            
            result["success"] = len(result["docs_added"]) > 0
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    async def _add_docs_to_file(self, file_path: Path, doc_type: str, bounds: Dict) -> List[str]:
        """Add documentation to a single file"""
        docs_added = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            new_lines = []
            
            for i, line in enumerate(lines):
                stripped = line.strip()
                
                # Add docstrings to Python functions
                if stripped.startswith('def ') and doc_type == "docstrings":
                    new_lines.append(line)
                    # Check if next line is already a docstring
                    if i + 1 < len(lines) and '"""' not in lines[i + 1]:
                        indent = len(line) - len(line.lstrip())
                        docstring = ' ' * (indent + 4) + '"""Add description here."""\n'
                        new_lines.append(docstring)
                        docs_added.append(f"Added docstring to function on line {i+1}")
                    else:
                        new_lines.append(line)
                
                # Add comments for complex expressions
                elif doc_type == "comments" and any(keyword in stripped for keyword in ['for', 'while', 'if']) and not stripped.startswith('#'):
                    # Add comment before complex control structures
                    indent = len(line) - len(line.lstrip())
                    comment = ' ' * indent + '# TODO: Add description\n'
                    new_lines.append(comment)
                    new_lines.append(line)
                    docs_added.append(f"Added comment before line {i+1}")
                else:
                    new_lines.append(line)
            
            if docs_added:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
        
        except Exception as e:
            logger.error(f"Failed to add docs to {file_path}: {e}")
        
        return docs_added
    
    async def _create_file(self, action: Dict, bounds: Dict) -> Dict[str, Any]:
        """Create a new file"""
        result = {
            "action": "create_file",
            "success": False,
            "files_modified": [],
            "template_used": action.get("template", "basic")
        }
        
        try:
            filename = action["filename"]
            template = action.get("template", "basic")
            
            file_path = Path(self.workspace_root) / filename
            
            if file_path.exists():
                result["error"] = f"File {filename} already exists"
                return result
            
            content = self._generate_file_content(filename, template)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            result["files_modified"] = [filename]
            result["success"] = True
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def _generate_file_content(self, filename: str, template: str) -> str:
        """Generate content for new file based on template"""
        name_without_ext = Path(filename).stem
        
        if template == "class" and filename.endswith('.py'):
            return f'''# {filename}
# Generated by Craft Agent

class {name_without_ext.title()}:
    """Add class description here."""
    
    def __init__(self):
        """Initialize the {name_without_ext}."""
        pass
    
    def example_method(self):
        """Add method description here."""
        pass
'''
        elif template == "function" and filename.endswith('.py'):
            return f'''# {filename}
# Generated by Craft Agent

def {name_without_ext}():
    """Add function description here."""
    pass
'''
        elif template == "test" and filename.endswith('.py'):
            return f'''# {filename}
# Generated by Craft Agent

import unittest

class Test{name_without_ext.title()}(unittest.TestCase):
    """Test cases for {name_without_ext}."""
    
    def setUp(self):
        """Set up test fixtures."""
        pass
    
    def test_{name_without_ext}(self):
        """Test {name_without_ext} functionality."""
        pass

if __name__ == '__main__':
    unittest.main()
'''
        else:
            return f'''# {filename}
# Generated by Craft Agent

# Add your code here
'''
    
    async def _general_improvement(self, action: Dict, bounds: Dict) -> Dict[str, Any]:
        """Apply general improvements"""
        result = {
            "action": "general_improvement",
            "success": False,
            "files_modified": [],
            "improvements": []
        }
        
        try:
            # Combine multiple improvement types
            format_result = await self._format_code({"target_pattern": "*.py", "formatter": "basic"}, bounds)
            if format_result["success"]:
                result["files_modified"].extend(format_result["files_modified"])
                result["improvements"].append("formatting")
            
            result["success"] = len(result["files_modified"]) > 0
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    async def _create_backup(self) -> str:
        """Create backup of workspace before making changes"""
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_dir = f"{self.workspace_root}_backup_{timestamp}"
            
            # Only backup specific file types to avoid large backups
            important_files = []
            for pattern in ["*.py", "*.js", "*.ts", "*.css", "*.html", "*.json"]:
                important_files.extend(Path(self.workspace_root).rglob(pattern))
            
            if important_files:
                os.makedirs(backup_dir, exist_ok=True)
                
                for file_path in important_files[:50]:  # Limit backup size
                    rel_path = file_path.relative_to(Path(self.workspace_root))
                    backup_file_path = Path(backup_dir) / rel_path
                    backup_file_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_path, backup_file_path)
            
            logger.info(f"Created backup at: {backup_dir}")
            return backup_dir
            
        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")
            return None
    
    async def _verify_changes(self, files_changed: List[str]) -> bool:
        """Verify that changes don't break basic syntax"""
        try:
            for file_path in files_changed:
                full_path = Path(self.workspace_root) / file_path
                
                if full_path.suffix == ".py":
                    # Basic Python syntax check
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            compile(f.read(), str(full_path), 'exec')
                    except SyntaxError as e:
                        logger.error(f"Syntax error in {file_path}: {e}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return False
    
    async def _rollback_changes(self):
        """Rollback changes using backup"""
        if not self.backup_dir or not os.path.exists(self.backup_dir):
            logger.error("No backup available for rollback")
            return
        
        try:
            # Restore files from backup
            for root, dirs, files in os.walk(self.backup_dir):
                for file in files:
                    backup_file = Path(root) / file
                    rel_path = backup_file.relative_to(Path(self.backup_dir))
                    original_file = Path(self.workspace_root) / rel_path
                    
                    original_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup_file, original_file)
            
            logger.info("Successfully rolled back changes")
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            raise

# CLI interface for standalone usage
if __name__ == "__main__":
    import sys
    
    async def main():
        if len(sys.argv) < 2:
            print("Usage: python craft.py '<task_description>' [scope] [workspace_root]")
            return
        
        task_description = sys.argv[1]
        scope = sys.argv[2] if len(sys.argv) > 2 else "safe_refactor"
        workspace_root = sys.argv[3] if len(sys.argv) > 3 else None
        
        agent = CraftAgent(workspace_root)
        bounds = {"max_files": 5, "max_lines_per_file": 100}
        
        result = await agent.execute_task(task_description, scope, bounds)
        print(json.dumps(result, indent=2))
    
    asyncio.run(main())
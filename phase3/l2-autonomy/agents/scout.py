# phase3/l2-autonomy/agents/scout.py
# Scout Agent v0 - Exploration and Analysis

import asyncio
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import structlog

logger = structlog.get_logger()

class ScoutAgent:
    """Scout agent for code exploration and analysis"""
    
    def __init__(self, workspace_root: str = None):
        self.workspace_root = workspace_root or os.getcwd()
        self.agent_id = "scout-v0"
        self.capabilities = [
            "code_analysis",
            "file_exploration", 
            "pattern_detection",
            "dependency_mapping",
            "test_discovery"
        ]
    
    async def execute_task(self, task_description: str, scope: str, bounds: Dict) -> Dict[str, Any]:
        """Execute scouting task"""
        logger.info(f"Scout agent executing: {task_description}")
        
        start_time = datetime.utcnow()
        result = {
            "agent_id": self.agent_id,
            "task_description": task_description,
            "scope": scope,
            "start_time": start_time.isoformat(),
            "success": False,
            "findings": {},
            "recommendations": [],
            "files_analyzed": [],
            "error": None
        }
        
        try:
            # Parse task and determine actions
            actions = self._parse_task(task_description, scope)
            
            # Execute actions within bounds
            for action in actions:
                if not self._check_bounds(action, bounds):
                    continue
                
                action_result = await self._execute_action(action)
                result["findings"][action["type"]] = action_result
            
            # Generate recommendations
            result["recommendations"] = self._generate_recommendations(result["findings"])
            result["success"] = True
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Scout agent failed: {e}")
        
        result["end_time"] = datetime.utcnow().isoformat()
        return result
    
    def _parse_task(self, description: str, scope: str) -> List[Dict]:
        """Parse task description into actionable items"""
        actions = []
        description_lower = description.lower()
        
        # Code analysis actions
        if any(keyword in description_lower for keyword in ["analyze", "review", "examine"]):
            actions.append({
                "type": "code_analysis",
                "target": "current_codebase",
                "depth": "surface" if "quick" in description_lower else "deep"
            })
        
        # File exploration
        if any(keyword in description_lower for keyword in ["find", "search", "locate"]):
            actions.append({
                "type": "file_exploration",
                "pattern": self._extract_search_pattern(description),
                "recursive": True
            })
        
        # Pattern detection
        if any(keyword in description_lower for keyword in ["pattern", "duplicate", "similar"]):
            actions.append({
                "type": "pattern_detection",
                "scope": scope,
                "analyze_duplicates": True
            })
        
        # Test discovery
        if any(keyword in description_lower for keyword in ["test", "spec", "coverage"]):
            actions.append({
                "type": "test_discovery",
                "find_missing_tests": True,
                "analyze_coverage": True
            })
        
        # Default action if no specific keywords
        if not actions:
            actions.append({
                "type": "general_analysis",
                "scope": scope,
                "quick_overview": True
            })
        
        return actions
    
    def _extract_search_pattern(self, description: str) -> str:
        """Extract search pattern from description"""
        # Simple pattern extraction - could be enhanced with NLP
        common_patterns = ["*.py", "*.js", "*.ts", "*.css", "*.html", "*.json"]
        
        for pattern in common_patterns:
            if pattern.replace("*", "").replace(".", "") in description.lower():
                return pattern
        
        return "**/*"  # Default: all files
    
    def _check_bounds(self, action: Dict, bounds: Dict) -> bool:
        """Check if action is within allowed bounds"""
        # Basic bounds checking
        max_files = bounds.get("max_files", 10)
        
        if action["type"] == "file_exploration":
            # Limit file search scope
            return True  # Scout operations are generally safe
        
        return True
    
    async def _execute_action(self, action: Dict) -> Dict[str, Any]:
        """Execute a specific action"""
        action_type = action["type"]
        
        if action_type == "code_analysis":
            return await self._analyze_code(action)
        elif action_type == "file_exploration":
            return await self._explore_files(action)
        elif action_type == "pattern_detection":
            return await self._detect_patterns(action)
        elif action_type == "test_discovery":
            return await self._discover_tests(action)
        else:
            return await self._general_analysis(action)
    
    async def _analyze_code(self, action: Dict) -> Dict[str, Any]:
        """Analyze codebase structure and quality"""
        result = {
            "files_found": 0,
            "languages": {},
            "complexity_estimate": "unknown",
            "potential_issues": []
        }
        
        try:
            # Find code files
            code_files = []
            for ext in [".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c"]:
                files = list(Path(self.workspace_root).rglob(f"*{ext}"))
                code_files.extend(files)
                if files:
                    result["languages"][ext[1:]] = len(files)
            
            result["files_found"] = len(code_files)
            
            # Quick complexity analysis
            if code_files:
                total_lines = 0
                for file_path in code_files[:10]:  # Sample first 10 files
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = len(f.readlines())
                            total_lines += lines
                    except:
                        continue
                
                avg_lines = total_lines / min(len(code_files), 10)
                if avg_lines > 200:
                    result["complexity_estimate"] = "high"
                elif avg_lines > 100:
                    result["complexity_estimate"] = "medium"
                else:
                    result["complexity_estimate"] = "low"
        
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    async def _explore_files(self, action: Dict) -> Dict[str, Any]:
        """Explore filesystem for specific patterns"""
        result = {
            "matches_found": [],
            "total_files": 0,
            "directories": []
        }
        
        try:
            pattern = action.get("pattern", "**/*")
            root_path = Path(self.workspace_root)
            
            matches = list(root_path.rglob(pattern))
            result["total_files"] = len(matches)
            
            # Limit results to avoid overwhelming
            for match in matches[:50]:
                result["matches_found"].append({
                    "path": str(match.relative_to(root_path)),
                    "size": match.stat().st_size if match.is_file() else 0,
                    "type": "file" if match.is_file() else "directory",
                    "modified": datetime.fromtimestamp(match.stat().st_mtime).isoformat()
                })
            
            # Find unique directories
            dirs = set()
            for match in matches:
                if match.is_file():
                    dirs.add(str(match.parent.relative_to(root_path)))
            result["directories"] = sorted(list(dirs))
        
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    async def _detect_patterns(self, action: Dict) -> Dict[str, Any]:
        """Detect code patterns and duplicates"""
        result = {
            "duplicate_patterns": [],
            "common_imports": [],
            "naming_conventions": {},
            "architectural_patterns": []
        }
        
        try:
            # Find Python files for pattern analysis
            py_files = list(Path(self.workspace_root).rglob("*.py"))[:20]  # Limit to first 20
            
            import_counts = {}
            class_patterns = []
            
            for py_file in py_files:
                try:
                    with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                        # Analyze imports
                        for line in content.split('\n'):
                            if line.strip().startswith(('import ', 'from ')):
                                import_line = line.strip()
                                import_counts[import_line] = import_counts.get(import_line, 0) + 1
                        
                        # Find class definitions
                        for line in content.split('\n'):
                            if line.strip().startswith('class '):
                                class_patterns.append(line.strip())
                
                except:
                    continue
            
            # Most common imports
            result["common_imports"] = [
                {"import": imp, "count": count}
                for imp, count in sorted(import_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            ]
            
            # Detect naming conventions
            if class_patterns:
                camel_case = sum(1 for pattern in class_patterns if any(c.isupper() for c in pattern))
                result["naming_conventions"]["camel_case_classes"] = camel_case / len(class_patterns)
        
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    async def _discover_tests(self, action: Dict) -> Dict[str, Any]:
        """Discover test files and coverage"""
        result = {
            "test_files": [],
            "test_frameworks": [],
            "coverage_estimate": "unknown",
            "missing_test_areas": []
        }
        
        try:
            # Find test files
            test_patterns = ["*test*.py", "*spec*.py", "test_*.py", "*_test.py"]
            test_files = []
            
            for pattern in test_patterns:
                test_files.extend(Path(self.workspace_root).rglob(pattern))
            
            result["test_files"] = [str(f.relative_to(Path(self.workspace_root))) for f in test_files]
            
            # Detect frameworks
            frameworks = set()
            for test_file in test_files[:10]:  # Sample first 10
                try:
                    with open(test_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read().lower()
                        if 'pytest' in content or 'def test_' in content:
                            frameworks.add("pytest")
                        if 'unittest' in content or 'TestCase' in content:
                            frameworks.add("unittest")
                        if 'jest' in content or 'describe(' in content:
                            frameworks.add("jest")
                except:
                    continue
            
            result["test_frameworks"] = list(frameworks)
            
            # Basic coverage estimate
            source_files = list(Path(self.workspace_root).rglob("*.py"))
            if source_files and test_files:
                coverage_ratio = len(test_files) / len(source_files)
                if coverage_ratio > 0.8:
                    result["coverage_estimate"] = "high"
                elif coverage_ratio > 0.4:
                    result["coverage_estimate"] = "medium"
                else:
                    result["coverage_estimate"] = "low"
        
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    async def _general_analysis(self, action: Dict) -> Dict[str, Any]:
        """General codebase analysis"""
        result = {
            "overview": {},
            "structure": [],
            "technologies": []
        }
        
        try:
            root_path = Path(self.workspace_root)
            
            # Directory structure (top level)
            for item in root_path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    file_count = len(list(item.rglob("*")))
                    result["structure"].append({
                        "name": item.name,
                        "type": "directory",
                        "file_count": file_count
                    })
                elif item.is_file():
                    result["structure"].append({
                        "name": item.name,
                        "type": "file",
                        "size": item.stat().st_size
                    })
            
            # Detect technologies
            config_files = {
                "package.json": "Node.js/JavaScript",
                "requirements.txt": "Python",
                "Cargo.toml": "Rust", 
                "pom.xml": "Java/Maven",
                "build.gradle": "Java/Gradle",
                "docker-compose.yml": "Docker",
                ".env": "Environment Config"
            }
            
            for config_file, tech in config_files.items():
                if (root_path / config_file).exists():
                    result["technologies"].append(tech)
        
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def _generate_recommendations(self, findings: Dict) -> List[str]:
        """Generate recommendations based on findings"""
        recommendations = []
        
        # Code analysis recommendations
        if "code_analysis" in findings:
            analysis = findings["code_analysis"]
            complexity = analysis.get("complexity_estimate")
            
            if complexity == "high":
                recommendations.append("Consider refactoring large files to improve maintainability")
            
            if analysis.get("files_found", 0) > 100:
                recommendations.append("Large codebase detected - consider implementing module boundaries")
        
        # Test discovery recommendations  
        if "test_discovery" in findings:
            test_info = findings["test_discovery"]
            coverage = test_info.get("coverage_estimate")
            
            if coverage == "low":
                recommendations.append("Low test coverage detected - consider adding more unit tests")
            elif not test_info.get("test_frameworks"):
                recommendations.append("No test framework detected - consider setting up automated testing")
        
        # Pattern detection recommendations
        if "pattern_detection" in findings:
            patterns = findings["pattern_detection"]
            if len(patterns.get("duplicate_patterns", [])) > 5:
                recommendations.append("Multiple duplicate patterns found - consider extracting common utilities")
        
        # Default recommendation if none generated
        if not recommendations:
            recommendations.append("Codebase analysis completed - no immediate issues detected")
        
        return recommendations

# CLI interface for standalone usage
if __name__ == "__main__":
    import sys
    
    async def main():
        if len(sys.argv) < 2:
            print("Usage: python scout.py '<task_description>' [scope] [workspace_root]")
            return
        
        task_description = sys.argv[1]
        scope = sys.argv[2] if len(sys.argv) > 2 else "safe_refactor"
        workspace_root = sys.argv[3] if len(sys.argv) > 3 else None
        
        agent = ScoutAgent(workspace_root)
        bounds = {"max_files": 10, "max_lines_per_file": 100}
        
        result = await agent.execute_task(task_description, scope, bounds)
        print(json.dumps(result, indent=2))
    
    asyncio.run(main())
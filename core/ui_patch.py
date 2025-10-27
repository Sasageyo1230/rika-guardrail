"""
Rika Phase 3.4 UI Patch System
AI-driven UI modifications for Design Mode
"""
import os
import re
import json
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .config import config
from .llm_client import LLMMessage, get_llm_client

# Request/Response Models
class UIPatchRequest(BaseModel):
    request: str
    target_files: Optional[List[str]] = None
    preview_only: bool = True

class UIPatchResponse(BaseModel):
    patch_id: str
    description: str
    files_changed: List[str]
    patches: List[Dict[str, Any]]
    preview_diff: str
    safe: bool
    warnings: List[str] = []

class ApplyPatchRequest(BaseModel):
    patch_id: str

# Router for UI patch endpoints
ui_patch_router = APIRouter(prefix="/ui", tags=["ui_patch"])

# System prompt for UI modification
UI_PATCH_SYSTEM_PROMPT = """You are an expert React/TypeScript/Tailwind CSS developer. You help modify UI components based on natural language requests.

RULES:
1. Only modify files under ui/src/ directory
2. Never touch configuration files, package.json, or files outside ui/src/
3. Never include API keys, secrets, or sensitive data
4. Provide precise, minimal diffs that accomplish the requested change
5. Use Tailwind CSS classes whenever possible
6. Maintain existing component structure and props
7. Ensure TypeScript type safety
8. Keep accessibility in mind (aria labels, keyboard navigation)

When given a UI modification request:
1. Analyze what files need to be changed
2. Generate the minimal diff for each file
3. Explain what the changes do
4. Flag any potential issues or warnings

Respond with JSON in this format:
{
  "description": "Brief description of what changes will be made",
  "files": [
    {
      "path": "ui/src/components/Example.tsx",
      "changes": [
        {
          "type": "replace",
          "line_start": 10,
          "line_end": 12,
          "old_content": "old code here",
          "new_content": "new code here"
        }
      ]
    }
  ],
  "warnings": ["Any warnings about the changes"],
  "safe": true
}"""

class UIPatchService:
    """Service for handling UI patch operations"""
    
    def __init__(self):
        self.llm_client = get_llm_client(config)
        self.patches_dir = Path("ui/.ai-patches")
        self.patches_dir.mkdir(parents=True, exist_ok=True)
        self.ui_src_dir = Path("ui/src")
    
    async def create_patch(self, request: UIPatchRequest) -> UIPatchResponse:
        """Create a UI patch based on natural language request"""
        
        # Validate that ui/src directory exists
        if not self.ui_src_dir.exists():
            raise HTTPException(status_code=400, detail="UI source directory not found")
        
        # Get current UI file structure for context
        ui_context = self._get_ui_context(request.target_files)
        
        # Create LLM prompt
        messages = [
            LLMMessage("system", UI_PATCH_SYSTEM_PROMPT),
            LLMMessage("user", f"""
UI Modification Request: {request.request}

Current UI Structure:
{ui_context}

Please generate the precise changes needed to fulfill this request. Focus on minimal, safe modifications.
""")
        ]
        
        # Get LLM response
        llm_response = await self.llm_client.chat(messages)
        
        if llm_response.error:
            raise HTTPException(status_code=500, detail=f"LLM Error: {llm_response.error}")
        
        # Parse LLM response as JSON
        try:
            patch_data = json.loads(llm_response.content)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"Invalid JSON response from LLM: {e}")
        
        # Validate and sanitize patch
        patch_id = str(uuid.uuid4())
        validated_patch = self._validate_and_sanitize_patch(patch_data, patch_id)
        
        # Save patch to file
        patch_file = self.patches_dir / f"{patch_id}.json"
        with open(patch_file, 'w', encoding='utf-8') as f:
            json.dump(validated_patch, f, indent=2)
        
        # Generate preview diff
        preview_diff = self._generate_preview_diff(validated_patch)
        
        return UIPatchResponse(
            patch_id=patch_id,
            description=validated_patch["description"],
            files_changed=[f["path"] for f in validated_patch["files"]],
            patches=validated_patch["files"],
            preview_diff=preview_diff,
            safe=validated_patch["safe"],
            warnings=validated_patch["warnings"]
        )
    
    async def apply_patch(self, patch_id: str) -> Dict[str, Any]:
        """Apply a previously created patch"""
        
        patch_file = self.patches_dir / f"{patch_id}.json"
        if not patch_file.exists():
            raise HTTPException(status_code=404, detail="Patch not found")
        
        # Load patch
        with open(patch_file, 'r', encoding='utf-8') as f:
            patch_data = json.load(f)
        
        if not patch_data.get("safe", False):
            raise HTTPException(status_code=400, detail="Unsafe patch cannot be applied")
        
        applied_files = []
        errors = []
        
        # Apply changes to each file
        for file_patch in patch_data["files"]:
            file_path = Path(file_patch["path"])
            
            try:
                if not file_path.exists():
                    errors.append(f"File not found: {file_path}")
                    continue
                
                # Read current file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Apply changes
                modified_content = self._apply_changes_to_content(content, file_patch["changes"])
                
                # Write modified content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                
                applied_files.append(str(file_path))
                
            except Exception as e:
                errors.append(f"Error applying patch to {file_path}: {str(e)}")
        
        # Mark patch as applied
        patch_data["applied_at"] = datetime.now(timezone.utc).isoformat()
        patch_data["applied_files"] = applied_files
        patch_data["apply_errors"] = errors
        
        with open(patch_file, 'w', encoding='utf-8') as f:
            json.dump(patch_data, f, indent=2)
        
        return {
            "patch_id": patch_id,
            "applied_files": applied_files,
            "errors": errors,
            "success": len(errors) == 0
        }
    
    def _get_ui_context(self, target_files: Optional[List[str]] = None) -> str:
        """Get UI file structure and content for context"""
        context_lines = []
        
        if target_files:
            # Focus on specific files
            for file_path in target_files:
                full_path = Path(file_path)
                if full_path.exists() and full_path.is_relative_to(self.ui_src_dir):
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        context_lines.append(f"\n--- {file_path} ---")
                        context_lines.append(content[:2000])  # First 2000 chars
                        if len(content) > 2000:
                            context_lines.append("... (truncated)")
                    except Exception:
                        context_lines.append(f"\n--- {file_path} --- (could not read)")
        else:
            # Get general structure
            context_lines.append("UI File Structure:")
            for file_path in self.ui_src_dir.rglob("*.tsx"):
                rel_path = file_path.relative_to(Path("."))
                context_lines.append(f"  {rel_path}")
            
            context_lines.append("\nKey Component Files:")
            key_files = [
                "ui/src/App.tsx",
                "ui/src/components/ChatPanel.tsx", 
                "ui/src/components/HUD.tsx"
            ]
            
            for file_path in key_files:
                full_path = Path(file_path)
                if full_path.exists():
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        context_lines.append(f"\n--- {file_path} ---")
                        context_lines.append(content[:1000])  # First 1000 chars
                        if len(content) > 1000:
                            context_lines.append("... (truncated)")
                    except Exception:
                        context_lines.append(f"\n--- {file_path} --- (could not read)")
        
        return "\n".join(context_lines)
    
    def _validate_and_sanitize_patch(self, patch_data: Dict, patch_id: str) -> Dict[str, Any]:
        """Validate and sanitize patch data for security"""
        
        validated = {
            "patch_id": patch_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "description": patch_data.get("description", "UI modification"),
            "files": [],
            "warnings": list(patch_data.get("warnings", [])),
            "safe": True
        }
        
        for file_patch in patch_data.get("files", []):
            file_path = file_patch.get("path", "")
            
            # Security checks
            if not file_path.startswith("ui/src/"):
                validated["warnings"].append(f"File outside ui/src/ ignored: {file_path}")
                validated["safe"] = False
                continue
            
            # Check for suspicious patterns
            suspicious_patterns = [
                r"process\.env",
                r"localStorage\.setItem.*token",
                r"document\.cookie",
                r"eval\s*\(",
                r"innerHTML\s*=",
                r"dangerouslySetInnerHTML"
            ]
            
            for change in file_patch.get("changes", []):
                new_content = change.get("new_content", "")
                for pattern in suspicious_patterns:
                    if re.search(pattern, new_content, re.IGNORECASE):
                        validated["warnings"].append(f"Suspicious pattern detected in {file_path}: {pattern}")
                        validated["safe"] = False
            
            # Add validated file patch
            validated["files"].append({
                "path": file_path,
                "changes": file_patch.get("changes", [])
            })
        
        return validated
    
    def _generate_preview_diff(self, patch_data: Dict) -> str:
        """Generate a human-readable diff preview"""
        diff_lines = []
        
        for file_patch in patch_data["files"]:
            diff_lines.append(f"\n--- {file_patch['path']} ---")
            
            for change in file_patch["changes"]:
                if change["type"] == "replace":
                    diff_lines.append(f"@@ Lines {change['line_start']}-{change['line_end']} @@")
                    diff_lines.append(f"- {change['old_content']}")
                    diff_lines.append(f"+ {change['new_content']}")
                elif change["type"] == "insert":
                    diff_lines.append(f"@@ Insert at line {change['line_start']} @@")
                    diff_lines.append(f"+ {change['new_content']}")
                elif change["type"] == "delete":
                    diff_lines.append(f"@@ Delete lines {change['line_start']}-{change['line_end']} @@")
                    diff_lines.append(f"- {change['old_content']}")
        
        return "\n".join(diff_lines)
    
    def _apply_changes_to_content(self, content: str, changes: List[Dict]) -> str:
        """Apply changes to file content"""
        lines = content.split('\n')
        
        # Sort changes by line number in reverse order to avoid index shifting
        sorted_changes = sorted(changes, key=lambda c: c.get("line_start", 0), reverse=True)
        
        for change in sorted_changes:
            change_type = change.get("type", "replace")
            line_start = change.get("line_start", 1) - 1  # Convert to 0-based indexing
            line_end = change.get("line_end", line_start + 1) - 1
            
            if change_type == "replace":
                new_content = change.get("new_content", "")
                lines[line_start:line_end + 1] = [new_content]
            
            elif change_type == "insert":
                new_content = change.get("new_content", "")
                lines.insert(line_start, new_content)
            
            elif change_type == "delete":
                del lines[line_start:line_end + 1]
        
        return '\n'.join(lines)

# Global service instance
_ui_patch_service: Optional[UIPatchService] = None

def get_ui_patch_service() -> UIPatchService:
    """Get or create the global UI patch service"""
    global _ui_patch_service
    if _ui_patch_service is None:
        _ui_patch_service = UIPatchService()
    return _ui_patch_service

# FastAPI route handlers
@ui_patch_router.post("/patch", response_model=UIPatchResponse)
async def create_ui_patch(request: UIPatchRequest):
    """Create a UI patch based on natural language description"""
    service = get_ui_patch_service()
    return await service.create_patch(request)

@ui_patch_router.post("/patch/{patch_id}/apply")
async def apply_ui_patch(patch_id: str):
    """Apply a previously created UI patch"""
    service = get_ui_patch_service()
    return await service.apply_patch(patch_id)

@ui_patch_router.get("/patches")
async def list_patches():
    """List available patches"""
    service = get_ui_patch_service()
    patches_dir = service.patches_dir
    
    patches = []
    for patch_file in patches_dir.glob("*.json"):
        try:
            with open(patch_file, 'r') as f:
                patch_data = json.load(f)
            
            patches.append({
                "patch_id": patch_data.get("patch_id", patch_file.stem),
                "description": patch_data.get("description", "Unknown"),
                "created_at": patch_data.get("created_at"),
                "applied_at": patch_data.get("applied_at"),
                "safe": patch_data.get("safe", False),
                "files_count": len(patch_data.get("files", []))
            })
        except Exception:
            continue
    
    # Sort by creation time
    patches.sort(key=lambda p: p.get("created_at", ""), reverse=True)
    
    return {"patches": patches}
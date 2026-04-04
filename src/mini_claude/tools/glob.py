"""Glob tool for file pattern matching."""

import glob as pyglob
from pathlib import Path
from typing import Any, List, Optional

from mini_claude.tools.base import Tool, ToolResult


class GlobTool(Tool):
    """Tool for file pattern matching."""

    name = "Glob"
    description = "Find files matching a glob pattern"

    async def execute(
        self,
        pattern: str,
        path: Optional[str] = None,
        include_hidden: bool = False,
        **kwargs: Any,
    ) -> ToolResult:
        """
        Find files matching a glob pattern.

        Args:
            pattern: Glob pattern to match (e.g., "**/*.py")
            path: Base directory to search in (defaults to current directory)
            include_hidden: Whether to include hidden files/directories
            **kwargs: Additional arguments (unused)

        Returns:
            ToolResult with matching file paths
        """
        try:
            base_path = Path(path) if path else Path.cwd()
            base_path = base_path.resolve()

            if not base_path.exists():
                return ToolResult.err(f"Base path not found: {base_path}")
            if not base_path.is_dir():
                return ToolResult.err(f"Base path is not a directory: {base_path}")

            # Combine base path with pattern
            search_pattern = str(base_path / pattern)

            # Use glob to find matches
            matches = pyglob.glob(
                search_pattern,
                recursive="**" in pattern,
                include_hidden=include_hidden,
            )

            # Convert to Path objects and sort
            paths = [Path(m) for m in matches]
            paths.sort(key=lambda p: (p.is_file(), str(p)))

            # Convert to relative paths if possible
            relative_paths: List[str] = []
            for p in paths:
                try:
                    relative_paths.append(str(p.relative_to(base_path)))
                except ValueError:
                    relative_paths.append(str(p))

            result_content = "\n".join(relative_paths) if relative_paths else "No matches found"

            return ToolResult.ok(
                content=result_content,
                data={
                    "pattern": pattern,
                    "base_path": str(base_path),
                    "matches": relative_paths,
                    "count": len(relative_paths),
                },
            )
        except Exception as e:
            return ToolResult.err(f"Failed to search files: {e}")

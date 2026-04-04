"""
MiniClaude tools package.

This package contains the built-in tools that MiniClaude provides for
interacting with the filesystem and executing commands. These tools can
be automatically discovered and used by the AI assistant during chat
sessions.

Available Tools:
    - Read: Read file contents with optional offset and limit
    - Write: Write content to a file (creates or overwrites)
    - Edit: Perform precise string replacement in files
    - Glob: Find files matching glob patterns
    - Grep: Search file contents using regular expressions
    - Bash: Execute shell commands and return output

Example:
    ```python
    from mini_claude.tools import ReadTool, WriteTool, BashTool

    # Use a tool directly
    read_tool = ReadTool()
    result = await read_tool.execute(file_path="example.txt")
    if result.success:
        print(result.content)

    # Discover all tools
    from mini_claude.services.tool_schema_generator import discover_tools
    tools = discover_tools()
    ```
"""

from mini_claude.tools.bash import BashTool
from mini_claude.tools.edit import EditTool
from mini_claude.tools.glob import GlobTool
from mini_claude.tools.grep import GrepTool
from mini_claude.tools.read import ReadTool
from mini_claude.tools.write import WriteTool

__all__ = [
    "ReadTool",
    "WriteTool",
    "EditTool",
    "GlobTool",
    "GrepTool",
    "BashTool",
]

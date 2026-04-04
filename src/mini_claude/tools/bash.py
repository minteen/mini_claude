"""Bash tool for executing shell commands."""

import asyncio
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from mini_claude.tools.base import Tool, ToolResult


def _get_shell_info() -> Tuple[str, str]:
    """Get default shell and shell flag for the current platform."""
    if sys.platform == "win32":
        # Prefer PowerShell if available, fallback to cmd
        powershell = shlex.quote(os.environ.get("COMSPEC", ""))
        if "powershell" in powershell.lower() or "pwsh" in powershell.lower():
            return powershell, "-Command"
        # Check for PowerShell in PATH
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", "echo $null"],
                capture_output=True,
                timeout=2,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            return "powershell", "-NoProfile -Command"
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        # Fallback to cmd
        return "cmd", "/c"
    else:
        # Unix-like systems
        shell = os.environ.get("SHELL", "/bin/bash")
        if "bash" in shell:
            return shell, "-c"
        elif "zsh" in shell:
            return shell, "-c"
        elif "fish" in shell:
            return shell, "-c"
        return shell, "-c"


def _normalize_command(command: str, shell: str) -> str:
    """Normalize command for the given shell."""
    if sys.platform == "win32":
        if "powershell" in shell.lower() or "pwsh" in shell.lower():
            # Already PowerShell, no need to convert
            return command
        else:
            # For cmd.exe, basic conversion
            return command
    return command


class BashTool(Tool):
    """Tool for executing shell commands."""

    name = "Bash"
    description = "Execute shell commands and return output"

    async def execute(
        self,
        command: str,
        description: Optional[str] = None,
        timeout: Optional[int] = 120000,  # milliseconds
        working_dir: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> ToolResult:
        """
        Execute a shell command.

        Args:
            command: Shell command to execute
            description: Description of what the command does
            timeout: Timeout in milliseconds (default: 120000 = 2 minutes)
            working_dir: Working directory for the command
            env: Additional environment variables
            **kwargs: Additional arguments (unused)

        Returns:
            ToolResult with command output or error
        """
        try:
            shell_exe, shell_flag = _get_shell_info()

            # Prepare environment
            full_env = dict(os.environ)
            if env:
                full_env.update(env)

            # Prepare working directory
            cwd = Path(working_dir) if working_dir else Path.cwd()
            cwd = cwd.resolve()

            if not cwd.exists():
                return ToolResult.err(f"Working directory not found: {cwd}")
            if not cwd.is_dir():
                return ToolResult.err(f"Working directory is not a directory: {cwd}")

            # Build command list
            if sys.platform == "win32" and ("powershell" in shell_exe.lower() or "pwsh" in shell_exe.lower()):
                # PowerShell needs special handling
                cmd_parts = [shell_exe]
                cmd_parts.extend(shlex.split(shell_flag))
                cmd_parts.append(command)
            else:
                cmd_parts = [shell_exe, shell_flag, command]

            # Execute command asynchronously
            timeout_sec = (timeout or 120000) / 1000.0

            # Use asyncio.create_subprocess_exec
            proc = await asyncio.create_subprocess_exec(
                *cmd_parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(cwd),
                env=full_env,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout_sec,
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return ToolResult.err(f"Command timed out after {timeout_sec} seconds")

            # Decode output
            stdout = stdout_bytes.decode("utf-8", errors="replace").rstrip("\r\n")
            stderr = stderr_bytes.decode("utf-8", errors="replace").rstrip("\r\n")

            combined_output = []
            if stdout:
                combined_output.append(stdout)
            if stderr:
                combined_output.append(stderr)

            result_content = "\n".join(combined_output) if combined_output else ""

            if proc.returncode == 0:
                return ToolResult.ok(
                    content=result_content,
                    data={
                        "command": command,
                        "description": description,
                        "returncode": proc.returncode,
                        "stdout": stdout,
                        "stderr": stderr,
                        "working_dir": str(cwd),
                    },
                )
            else:
                # Command failed, but we still return the output in error
                error_msg = f"Command failed with exit code {proc.returncode}"
                if stderr:
                    error_msg += f"\n{stderr}"
                return ToolResult.err(
                    error=error_msg,
                    data={
                        "command": command,
                        "description": description,
                        "returncode": proc.returncode,
                        "stdout": stdout,
                        "stderr": stderr,
                        "working_dir": str(cwd),
                    },
                )
        except Exception as e:
            return ToolResult.err(f"Failed to execute command: {e}")

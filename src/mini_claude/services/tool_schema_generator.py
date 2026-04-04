"""Generate OpenAI-compatible tool schemas from Tool classes."""

import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Any, Dict, List, Optional, get_args, get_origin

from mini_claude.services.models import (
    FunctionDefinition,
    FunctionParameters,
    ToolDefinition,
)
from mini_claude.tools.base import Tool


def discover_tools() -> Dict[str, type]:
    """
    Discover all Tool subclasses in the tools package.

    Returns:
        Dictionary mapping tool name to Tool class.
    """
    tools = {}

    try:
        import mini_claude.tools
        package = mini_claude.tools
        package_path = str(Path(mini_claude.tools.__file__).parent)
    except (ImportError, AttributeError):
        return tools

    # Discover all modules in the tools package
    for _, module_name, _ in pkgutil.iter_modules([package_path]):
        if module_name.startswith("_"):
            continue

        try:
            module = importlib.import_module(f"{package.__name__}.{module_name}")

            # Find all Tool subclasses in the module
            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, Tool)
                    and obj is not Tool
                    and not inspect.isabstract(obj)
                ):
                    tools[name] = obj
        except Exception:
            # Skip modules that fail to import
            pass

    return tools


def python_type_to_json_schema(python_type: Any) -> Dict[str, Any]:
    """
    Convert Python type to JSON Schema.

    Args:
        python_type: Python type annotation.

    Returns:
        JSON Schema property definition.
    """
    origin = get_origin(python_type)

    if origin is list:
        item_type = get_args(python_type)[0]
        return {
            "type": "array",
            "items": python_type_to_json_schema(item_type),
        }
    elif origin is dict:
        return {
            "type": "object",
            "additionalProperties": True,
        }
    elif origin is Optional:
        # Optional[T] is Union[T, None]
        actual_type = get_args(python_type)[0]
        return python_type_to_json_schema(actual_type)
    elif hasattr(python_type, "__origin__") and python_type.__origin__ is list:
        item_type = python_type.__args__[0] if python_type.__args__ else str
        return {
            "type": "array",
            "items": python_type_to_json_schema(item_type),
        }
    elif python_type is str:
        return {"type": "string"}
    elif python_type is int:
        return {"type": "integer"}
    elif python_type is float:
        return {"type": "number"}
    elif python_type is bool:
        return {"type": "boolean"}
    elif python_type is type(None):
        return {"type": "null"}
    else:
        # Default to string for unknown types
        return {"type": "string"}


def extract_tool_schema(tool_class: type) -> ToolDefinition:
    """
    Extract OpenAI-compatible schema from a Tool class.

    Args:
        tool_class: Tool class to extract schema from.

    Returns:
        ToolDefinition for the tool.
    """
    # Get tool name and description
    tool_name = getattr(tool_class, "name", tool_class.__name__)
    tool_description = getattr(tool_class, "help", "")

    # Try to get description from docstring
    if hasattr(tool_class, "execute"):
        execute_method = tool_class.execute
        if execute_method.__doc__:
            docstring = execute_method.__doc__.strip()
            if not tool_description:
                tool_description = docstring.split("\n")[0]

    # Extract parameters from execute method signature
    if not hasattr(tool_class, "execute"):
        raise ValueError(f"Tool class {tool_class.__name__} must have an execute method")

    sig = inspect.signature(tool_class.execute)
    properties: Dict[str, Any] = {}
    required: List[str] = []

    for param_name, param in sig.parameters.items():
        # Skip 'self' and '**kwargs' parameters
        if param_name == "self" or param_name == "kwargs":
            continue

        # Convert Python type to JSON Schema
        param_type = param.annotation if param.annotation != inspect.Parameter.empty else str
        schema = python_type_to_json_schema(param_type)

        # Add description if available (from docstring or parameter name)
        description = f"Parameter: {param_name}"
        if param_name == "file_path":
            description = "Path to the file"
        elif param_name == "content":
            description = "Content to write or search for"
        elif param_name == "pattern":
            description = "Pattern to match"
        elif param_name == "command":
            description = "Command to execute"
        schema["description"] = description

        properties[param_name] = schema

        # Add to required if no default value
        if param.default == inspect.Parameter.empty:
            required.append(param_name)

    return ToolDefinition(
        type="function",
        function=FunctionDefinition(
            name=tool_name,
            description=tool_description,
            parameters=FunctionParameters(
                type="object",
                properties=properties,
                required=required,
            ),
        ),
    )


def generate_all_tool_schemas() -> List[ToolDefinition]:
    """
    Generate schemas for all discovered tools.

    Returns:
        List of ToolDefinition objects.
    """
    tools = discover_tools()
    schemas = []

    for tool_class in tools.values():
        try:
            schema = extract_tool_schema(tool_class)
            schemas.append(schema)
        except Exception as e:
            # Skip tools that can't be processed
            pass

    return schemas


def get_tool_class_by_name(tool_name: str) -> Optional[type]:
    """
    Get Tool class by name.

    Args:
        tool_name: Name of the tool.

    Returns:
        Tool class if found, None otherwise.
    """
    tools = discover_tools()
    for cls in tools.values():
        if getattr(cls, "name", cls.__name__) == tool_name:
            return cls
    return None

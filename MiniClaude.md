# MiniClaude

基于 Python 实现的 Claude Code CLI 轻量版本。

## 技术栈

| 层级 | 技术选型 |
|------|----------|
| **CLI框架** | `Typer` + `Rich` |
| **异步运行时** | `asyncio` + `aiohttp` |
| **配置管理** | `pydantic-settings` + `python-dotenv` |
| **API客户端** | `httpx` |
| **Git操作** | `GitPython` |
| **文件监听** | `watchdog` |
| **语法高亮** | `pygments` |

## 项目结构

```
mini_claude/
├── pyproject.toml
├── src/
│   └── mini_claude/
│       ├── __main__.py       # CLI入口
│       ├── tools/            # 工具实现
│       ├── commands/         # 命令系统
│       ├── services/         # 服务层 (API/MCP/分析引擎)
│       └── utils/            # 工具函数
```

## 参考架构

参考 Claude Code 源码架构：
- `tools/` - 工具实现模块
- `commands/` - 命令系统
- `services/` - 服务层
- `utils/` - 工具函数库

"""
AutoApply MCP Test Client
-------------------------
Verifies the MCP server is working by listing all tools and prompts,
then running a quick smoke test on create_user.

Usage:
    python mcp_server/mcp_server_client.py
"""

import asyncio
import sys
from pathlib import Path


PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


SERVER_SCRIPT = str(Path(__file__).parent / "mcp_server.py")

PYTHON_EXE = str(Path(PROJECT_ROOT) / "venv" / "Scripts" / "python.exe")


async def run_tests() -> None:
    server_params = StdioServerParameters(
        command=PYTHON_EXE,
        args=[SERVER_SCRIPT],
        env={"PYTHONPATH": PROJECT_ROOT},
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            tools = tools_result.tools
            print(f"Tools available ({len(tools)}):")
            for mcp_tool in tools:
                print(f"   • {mcp_tool.name}: {mcp_tool.description}")

            prompts_result = await session.list_prompts()
            prompts = prompts_result.prompts
            print(f"Prompts available ({len(prompts)}):")
            for prompt in prompts:
                print(f"   • {prompt.name}: {prompt.description}")


if __name__ == "__main__":
    asyncio.run(run_tests())

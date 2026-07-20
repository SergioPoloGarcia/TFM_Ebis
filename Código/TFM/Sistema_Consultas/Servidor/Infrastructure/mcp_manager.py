import os
import sys
from typing import Any

from agent_framework import FunctionTool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPManager:
    """Administrador para gestionar la conexión y uso del servidor MCP."""
    def __init__(self, server_script_path: str):
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"

        self.server_params = StdioServerParameters(
            command=sys.executable,
            args=[server_script_path],
            env=env
        )
        self.session = None
        self._ctx = None

    async def connect(self):
        """Establece la conexión con el servidor MCP y crea una sesión de cliente."""
        self._ctx = stdio_client(self.server_params)
        read_stream, write_stream = await self._ctx.__aenter__()
        self.session = ClientSession(read_stream, write_stream)
        await self.session.__aenter__()
        await self.session.initialize()

    async def get_azure_tools(self) -> list:
        """Obtiene la lista de herramientas disponibles en el servidor MCP y las devuelve como objetos FunctionTool."""
        if not self.session:
            raise RuntimeError("MCP no conectado")

        mcp_tools = await self.session.list_tools()

        tool_objects = []
        for tool in mcp_tools.tools:
            tool_name = tool.name
            tool_schema = getattr(tool, "inputSchema", {}) or {}

            def _make_invoke_tool(name: str):
                async def _invoke_tool(*, arguments: dict[str, Any] | None = None, **kwargs: Any):
                    payload = dict(arguments or {})
                    if kwargs:
                        payload.update(kwargs)
                    return await self.execute_tool(name, payload)

                return _invoke_tool

            tool_objects.append(
                FunctionTool(
                    name=tool_name,
                    description=tool.description or f"Herramienta MCP: {tool_name}",
                    func=_make_invoke_tool(tool_name),
                    input_model=tool_schema,
                )
            )

        return tool_objects

    async def execute_tool(self, name: str, arguments: dict):
        """Ejecuta una herramienta específica en el servidor MCP con los argumentos proporcionados."""
        try:
            print(f"Llamando a tool '{name}': {arguments}")
            return await self.session.call_tool(name, arguments)

        except Exception as e:
            print(f"Error executing tool '{name}': {e}")
            raise

    async def disconnect(self):
        """Cierra la sesión y la conexión con el servidor MCP."""
        if self.session:
            await self.session.__aexit__(None, None, None)

        if self._ctx:
            await self._ctx.__aexit__(None, None, None)
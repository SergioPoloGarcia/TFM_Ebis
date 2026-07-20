import asyncio
from contextlib import AsyncExitStack
import json
import os
from typing import Any
import sys
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.shared.exceptions import McpError
from openai import OpenAI

foundry_url = ""
api_key_foundry = ""


class ClienteMCP:
    """Cliente para interactuar con el servidor MCP."""
    def __init__(self):
        self.session: ClientSession | None = None
        self._transport_context: Any | None = None
        self.exit_stack = AsyncExitStack()
        self.tools: list[str] = []

    async def conectar(self, server_script_path: str):
        """Conecta al servidor MCP"""
        command = sys.executable
        
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        print("Inicializando sesion con el servidor MCP")
        await self.session.initialize()

        # Lista tools disponibles
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConectado a MCP con tools:", [tool.name for tool in tools])
        
        return True
    
    async def cerrar(self) -> None:
        """Cierra la conexion con el servidor MCP"""
        await self.exit_stack.aclose()
        self.session = None


    async def ejecutar_tool(self, name: str, args: dict[str, Any]):
        """Ejecuta una tool del servidor MCP"""
        if not self.session:
            raise RuntimeError("Sesion no iniciada")
        try:
            return await self.session.call_tool(name, args)
        except McpError as exc:
            print(f"No se pudo llamar a la tool '{name}': {exc}")
            raise



def crear_cliente_openai(endpoint: str, api_key: str):
    """Crea cliente compatible con Foundry"""
    endpoint = endpoint.rstrip("/")
    return OpenAI(base_url=endpoint, api_key=api_key)

async def procesar_llamadas(client: ClienteMCP) -> None:
    """Procesa las llamadas y las guarda mediante una tool del servidor MCP."""

    endpoint: str = foundry_url
    deployment_name: str = "gpt-5.4-mini-TFM-Ebis"
    api_key: str = api_key_foundry

    if not api_key:
        raise RuntimeError("Falta configurar api_key_foundry.")

    if not deployment_name:
        raise RuntimeError("Falta configurar deployment_name.")

    # Crear cliente OpenAI con Foundry
    clientOpenAI = crear_cliente_openai(endpoint=endpoint, api_key=api_key)

    # Procesar cada transcripcion
    for filename in os.listdir("transcripciones_llamadas"):
        if filename.endswith(".txt"):
            with open(os.path.join("transcripciones_llamadas", filename), "r", encoding="utf-8") as f:
                transcription = f.read()

            # Leer prompt desde archivo
            with open("prompt.txt", "r", encoding="utf-8") as f:
                prompt = f.read()

            # Llamar al modelo de OpenAI para analizar la transcripcion
            response = clientOpenAI.responses.create(
                model=deployment_name,
                input=prompt.replace("{{TRANSCRIPCION}}", transcription)
            )

            # Convertir la respuesta JSON del modelo a un dict
            analisis = json.loads(response.output_text)

            # Añadir el id de la llamada
            analisis["id"] = os.path.splitext(filename)[0]

            # Enviar el JSON completo al MCP
            try:
                await client.ejecutar_tool(
                    name="guardar_transcripcion_procesada",
                    args={
                        "analisis": analisis
                    }
                )
                print(f"Analisis guardado para {os.path.splitext(filename)[0]}")
            except Exception as exc:
                print(f"Error al guardar la transcripcion {filename}: {exc}")
                continue




async def main() -> None:
    client = ClienteMCP()

    try:
        if await client.conectar(server_script_path=r"../MCP/servidor.py"):
            print("Cliente MCP ejecutandose correctamente.")
            await procesar_llamadas(client)

    except Exception as exc:
        print(f"Error: {exc}")

    finally:
        await client.cerrar()
        print("Conexion con MCP cerrada")

if __name__ == "__main__":
    asyncio.run(main())
   

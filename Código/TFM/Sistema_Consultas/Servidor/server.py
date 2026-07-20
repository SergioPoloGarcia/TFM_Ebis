from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn
from agent_framework_ag_ui import add_agent_framework_fastapi_endpoint
from Agentes.agente_consultas import crear_agente
from Infrastructure.mcp_manager import MCPManager
from Agentes.agente_consultas import crear_agente

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
        Administrador de ciclo de vida para la aplicación, 
        que se encarga de inicializar y conectar el servidor MCP, 
        obtener las tools y crear un agente con ellas.
    """
 
    mcp_gate = MCPManager(server_script_path=r"../../Backend_Proceso_Speech_Analytics/MCP/servidor.py")

    print("Conectando al servidor MCP")
    await mcp_gate.connect()

    # Obtencion de tools del servidor MCP
    discovered_tools = await mcp_gate.get_azure_tools()

    # Instancia del agente con las tools
    agent = crear_agente(tools_list=discovered_tools)
    print(f"Agente inicializado con tools MCP")  

    # Registro del endpoint del agente en FastAPI
    add_agent_framework_fastapi_endpoint(app, agent, "/")

    app.state.mcp_gate = mcp_gate
    yield


app = FastAPI(title="AG-UI Server", lifespan=lifespan)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)
from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential


class MCPToolAdapter:
    """Adaptador para integrar tools MCP en el agente."""
    def __init__(self, tool):
        self.tool = tool

    async def invoke(self, *, arguments=None, skip_parsing=False, **_):
        return await self.tool.invoke(arguments=arguments, skip_parsing=skip_parsing)

def crear_agente(tools_list=None):
    """Crea el agente con las tools proporcionadas."""
    if tools_list is None:
        tools_list = []

    # Configuración del cliente Foundry con credenciales de Azure CLI    
    credential = AzureCliCredential()
    client = FoundryChatClient(
        project_endpoint="https://ai-foundry-spg-dev.services.ai.azure.com/api/projects/default-project",
        model="gpt-5.4-mini-TFM-Ebis",
        credential=credential,
    )

    # Creación del agente
    agent = Agent(
        client=client,
        name="AGUIAssistant",
        instructions="Eres un asistente útil que usa tools MCP para responder las preguntas del usuario, cuando tenga sentido genera y utiliza graficas para ilustrar las respuestas.",
        tools=tools_list 
    )

    print(f"Agente creado con {len(tools_list)} tools MCP.")
    
    return agent
    
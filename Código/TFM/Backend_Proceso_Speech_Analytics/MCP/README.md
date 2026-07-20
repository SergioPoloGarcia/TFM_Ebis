# Servidor MCP
Se encarga de disponibilizar las tools al agente y al proceso de indexación.

## Paquetes
```
pip install mcp
pip install "mcp[cli]"
pip install openai
pip install uv
pip install asyncio
```

## Antes de iniciar
- Crear .venv e instalar paquetes.
- Aadir foundry_url (enviado al email).
- Añadir apy_key de Azure OpenAi (enviada en el email).
- Completar ruta de la carpeta "Datos".

## Comando para ejecutar
```
mcp dev servidor.py 
```




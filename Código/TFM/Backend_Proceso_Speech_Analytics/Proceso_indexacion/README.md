# Proceso de indexación
Se encarga de procesar las transcripciones de las llamadas (ubicadas en "transcripciones_llamadas") con IA para extraer KPIs de interés, utiliza una tool del MCP para guardar el resultado final.

## Paquetes
```
pip install mcp
pip install "mcp[cli]"
pip install openai
```

## Antes de iniciar
- Crear .venv e instalar paquetes.
- Aadir foundry_url (enviado al email).
- Añadir apy_key de Azure OpenAi (enviada en el email).


## Comando para ejecutar
```
pyhton main.py
```
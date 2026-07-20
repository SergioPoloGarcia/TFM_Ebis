# Servidor (agente)
Se encarga de disponibilizar el agente que procesa las solicitudes hechas por el cliente web.

## Paquetes
```
pip install agent-framework
pip install agent-framework-azure-ai --pre
pip install agent-framework-ag-ui --pre
pip install "mcp[cli]"
pip install mcp
```
## Antes de iniciar
- Crear .venv e instalar paquetes.
- Hacer Login en azure
    ```
    az login --tenant e0445127-b21d-48b8-8fa3-e03be5916817
    ```
    Si no te deja hacer login en el tenant y quieres probarlo puedes escribeme a sergio.polo.garcia21@gmail.com y te genero un usuario.

## Comando para ejecutar
```
python server.py
```
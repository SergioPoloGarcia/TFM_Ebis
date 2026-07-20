import json
from typing import Literal, Optional, List
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from models.transcripcion_procesada import AnalisisTranscripcion
from openai import OpenAI
import glob
from typing import Literal, Optional, Annotated, Any


founfry_url = ""
api_key_foundry = ""
ruta_base_ficheros_json = "<ruta_absoluta>\\TFM\\Backend_Proceso_Speech_Analytics\\Datos"


cliente_openAi = OpenAI(
                    base_url=founfry_url, 
                    api_key=api_key_foundry
                )


mcp: FastMCP = FastMCP("Speech analitics MCP")


@mcp.tool()
async def guardar_transcripcion_procesada(
    analisis: AnalisisTranscripcion
) -> str:
    """
    Guarda el análisis procesado de una llamada en formato JSON.
    """

    fichero = f"{ruta_base_ficheros_json}\\analisis_{analisis.id}.json"

    with open(fichero, "w", encoding="utf-8") as f:
        json.dump(
            analisis.model_dump(),
            f,
            ensure_ascii=False,
            indent=4
        )
    
    return f"Análisis guardado correctamente con id {analisis.id}"





class FiltroQuery(BaseModel):
    campo: str = Field(..., description="El campo del JSON a filtrar (ej: 'sentimiento', 'duracion')")
    operador: Literal["eq", "neq", "gt", "lt", "contains"] = Field(..., description="Operador lógico de comparación")
    valor: str = Field(..., description="El valor contra el que comparar")

@mcp.tool()
async def analizar_y_buscar_llamadas(peticion_usuario: str) -> Any:
    """
    Recibe una petición en lenguaje natural (ej: 'cuenta las llamadas de facturacion' o 
    'dame el id y resumen de las llamadas con sentimiento negativo'), genera la query 
    estructurada automáticamente y busca los resultados en los archivos JSON de llamadas.
    """
    
    # TRADUCCIÓN DE LENGUAJE NATURAL A QUERY JSON
    prompt_sistema = """
    Eres un traductor de lenguaje natural a consultas estructuradas de base de datos JSON.
    Tu objetivo es transformar la petición del usuario en un objeto JSON estructurado.
    
    Debes responder ÚNICAMENTE con un objeto JSON que cumpla ESTRICTAMENTE con este esquema:
    {
      "filtros": [
         {"campo": "categoria|sentimiento_cliente|resolucion|educacion_operador|resumen", "operador": "eq|neq|gt|lt|contains", "valor": <valor>}
      ],
      "limite": null o entero,
      "ordenar_por": null o string del campo,
      "direccion_orden": "asc" o "desc",
      "campos": null o lista de strings (ej: ["id", "resumen", "sentimiento_cliente"]),
      "conteo_solo": booleano (true si el usuario quiere saber "cuántos", "contar" o el "total de llamadas", false por defecto)
    }
    
    Reglas de traducción importantes:
    1. Operadores permitidos:
       - "eq": igual a (para strings, booleanos)
       - "neq": diferente a
       - "gt": mayor que (para números)
       - "lt": menor que (para números)
       - "contains": para buscar palabras clave dentro de 'resumen' o 'motivo'
       
    2. Parámetro 'conteo_solo':
       - Si el usuario pregunta cosas como: "¿Cuántas llamadas...?", "Cuenta los casos...", "Dime el total de...", actívalo a true.
       
    3. Parámetro 'campos':
       - Si el usuario pide explícitamente ver solo ciertos datos (ej: "solo quiero los IDs y el resumen"), pon esos campos en la lista. Si pide ver las llamadas completas o no especifica campos, déjalo como null.
    """

    # Llamada al modelo para extraer los parámetros de búsqueda
    response = cliente_openAi.chat.completions.create(
        model="gpt-5.4-mini-TFM-Ebis",
        messages=[
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": peticion_usuario}
        ],
        response_format={"type": "json_object"},
        temperature=0.0
    )
    
    try:
        query_estructurada = json.loads(response.choices[0].message.content)
    except Exception as err:
        return {"error": "No se pudo estructurar la petición del usuario.", "detalle": str(err)}

    # Extracción de los parámetros mapeados desde el JSON generado
    filtros_data = query_estructurada.get("filtros", [])
    
    # Se convierten los filtros a instancias de FiltroQuery
    filtros = [FiltroQuery(**f) for f in filtros_data]
    
    ordenar_por = query_estructurada.get("ordenar_por")
    direccion_orden = query_estructurada.get("direccion_orden", "asc")
    limite = query_estructurada.get("limite")
    campos = query_estructurada.get("campos")
    conteo_solo = query_estructurada.get("conteo_solo", False)

    # Busqueda en ficheros JSON con resultados del análisis de llamadas
    resultados = []
    patron_ficheros = f"{ruta_base_ficheros_json}\\analisis_*.json"
    ficheros = glob.glob(patron_ficheros)
    
    for ruta_fichero in ficheros:
        try:
            with open(ruta_fichero, "r", encoding="utf-8") as f:
                datos = json.load(f)
                
            cumple_filtros = True
            for filtro in filtros:
                campo = filtro.campo
                operador = filtro.operador
                valor_filtro = filtro.valor
                
                valor_real = datos.get(campo)
                
                if valor_real is None:
                    cumple_filtros = False
                    break
                
                try:
                    if isinstance(valor_real, (int, float)):
                        valor_comparar = type(valor_real)(valor_filtro)
                    else:
                        valor_comparar = valor_filtro
                except ValueError:
                    valor_comparar = valor_filtro

                if operador == "eq" and valor_real != valor_comparar:
                    cumple_filtros = False
                elif operador == "neq" and valor_real == valor_comparar:
                    cumple_filtros = False
                elif operador == "gt" and not (valor_real > valor_comparar):
                    cumple_filtros = False
                elif operador == "lt" and not (valor_real < valor_comparar):
                    cumple_filtros = False
                elif operador == "contains" and valor_filtro.lower() not in str(valor_real).lower():
                    cumple_filtros = False
                
                if not cumple_filtros:
                    break
            
            if cumple_filtros:
                resultados.append(datos)
                
        except Exception as err:
            print(f"Error procesando el fichero {ruta_fichero}: {err}")
            continue


    # Proceso de salida según los parámetros de la query estructurada
    if conteo_solo:
        return {
            "peticion": peticion_usuario,
            "total_coincidencias": len(resultados)
        }

    if ordenar_por and resultados:
        reversa = direccion_orden == "desc"
        resultados.sort(key=lambda x: x.get(ordenar_por, ""), reverse=reversa)

    if limite is not None:
        resultados = resultados[:limite]

    if campos:
        campos_set = set(campos)
        resultados_filtrados = []
        for registro in resultados:
            registro_reducido = {k: v for k, v in registro.items() if k in campos_set}
            resultados_filtrados.append(registro_reducido)
        return resultados_filtrados

    return resultados

if __name__ == "__main__":
    mcp.run()
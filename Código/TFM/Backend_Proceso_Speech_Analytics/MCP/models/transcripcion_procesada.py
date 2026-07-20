from pydantic import BaseModel
from typing import List

# Modelo de datos para representar la confianza en cada campo del análisis    
class Confidence(BaseModel):
    motivo: float
    categoria: float
    sentimiento_cliente: float
    educacion_operador: float
    resolucion: float

# Modelo de datos para representar el análisis de la transcripción de una llamada
class AnalisisTranscripcion(BaseModel):
    id: str
    motivo: str | None
    categoria: str | None
    sentimiento_cliente: str | None
    educacion_operador: float | None
    resolucion: bool | None
    dispositivos_mencionados: List[str]
    resumen: str | None
    confidence: Confidence


# Asistente Tienda IA (FastAPI + OpenAI + SQLite)

Este proyecto es un asistente conversacional para análisis de datos de negocio, especializado en consultas sobre ventas, productos y distribuidores, usando FastAPI, OpenAI y SQLite. Permite a usuarios hacer preguntas en lenguaje natural y obtener respuestas interpretadas, incluyendo consultas SQL y visualización de resultados en tablas.

## Características

- Interfaz web amigable para interactuar con el asistente.
- Soporte para contexto conversacional (recuerda las últimas 5 preguntas y respuestas).
- Generación automática de queries SQL y ejecución sobre una base de datos SQLite.
- Respuestas interpretadas y visualizadas en tablas HTML.
- Múltiples agentes (experto SQL, analista de datos, profesor).
- Adaptación automática de queries a sintaxis SQLite.
- Integración con OpenAI GPT-4.

## Estructura de la base de datos

El asistente responde sobre una base de datos con las siguientes tablas:

- **Productos:** CveArticulo, Nombre_Articulo, Categoria, TamanioDeFoto, TamanioFotoConNumero, NumeroPagina, NumeroPaginaCatalogo, Posicion, Rango_PN_Nuevo, Rango_PE_Nuevo, TBasica, Precio_Especial_Unitario, Precio_Normal_Unitario
- **Distribuidores:** ClaveDistribuidor, Clasificacion, Cod_Aso, Municipio, Estado, Zona_Metropolitana
- **Ventas:** id, Catálogo, ClaveDistribuidor, CveArticulo, Descuento, RangoDescuentos, UnidadesVendidas, VentaCatalogo, Fecha

## Instalación

1. **Clona el repositorio:**
   ```bash
   git clone https://github.com/tu_usuario/tec2025sql.git
   cd tec2025sql
   ```

2. **Instala las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configura tu clave de OpenAI:**
   - Crea una variable de entorno `OPENAI_API_KEY` con tu clave de OpenAI.

4. **Ejecuta el servidor:**
   ```bash
   uvicorn main:app --reload
   ```

5. **Abre en tu navegador:**
   ```
   http://localhost:8000
   ```

## Uso

- Escribe preguntas sobre ventas, productos o distribuidores.
- El asistente responde con interpretación, query SQL (si aplica) y resultados en tabla.
- Puedes elegir el tipo de agente para diferentes estilos de respuesta.

## Estructura del proyecto

```
.
├── main.py              # Backend FastAPI
├── create_db.py         # Script para crear la base de datos
├── requirements.txt     # Dependencias Python
├── prompt.txt           # Prompt base para el asistente
├── store.db             # Base de datos SQLite
├── templates/
│   └── index.html       # Interfaz web
└── README.md            # Este archivo
```

## Diagrama de arquitectura

Puedes visualizar el flujo del sistema con este diagrama Mermaid:

```mermaid
flowchart TD
    A[Usuario (Web o API)] -->|Pregunta| B[FastAPI Backend]
    B --> C[Gestor de contexto (últimas 5 preguntas/respuestas)]
    B --> D[Generador de prompt]
    D --> E[OpenAI API (GPT-4)]
    E --> F{¿Respuesta contiene SQL?}
    F -- Sí --> G[Adaptador SQL para SQLite]
    G --> H[SQLite DB]
    H --> I[Resultados de consulta]
    I --> J[Renderizado de tabla HTML + interpretación]
    F -- No --> K[Respuesta directa de OpenAI]
    J --> L[Respuesta al usuario]
    K --> L

    C -.-> D
    C -.-> L
```

## Créditos

Desarrollado por el equipo del Tec de Monterrey.

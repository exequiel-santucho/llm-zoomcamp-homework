# Módulo 1 - Agentic RAG (Homework 1)

Este directorio contiene la solución para el Módulo 1 de LLM Zoomcamp.

## Descripción

Implementación de un sistema RAG (Retrieval-Augmented Generation) con capacidades de agentes autónomos.

## Requisitos

- Python >= 3.13
- Dependencias especificadas en `requirements.txt`

## Instalación

### Opción 1: Con pip (usando requirements.txt)

```bash
pip install -r requirements.txt
```

### Opción 2: Con uv (recomendado)

```bash
uv sync
```

## Dependencias Principales

- **gitsource**: Herramienta para trabajar con repositorios Git
- **groq**: API cliente de Groq
- **minsearch**: Búsqueda mínima eficiente
- **openai**: Cliente de OpenAI API
- **python-dotenv**: Gestión de variables de entorno
- **toyaikit**: Kit de herramientas de IA

## Configuración

### Variables de Entorno

Crear un archivo `.env` en la raíz del proyecto:

```bash
OPENAI_API_KEY=tu_clave_aqui
GROQ_API_KEY=tu_clave_aqui
```

## Estructura

- **main.py**: Script principal de la aplicación
- **pyproject.toml**: Configuración del proyecto
- **.env**: Variables de entorno (no incluir en git)

## Ejecución

```bash
# Con pip
python main.py

# O con uv
uv run python main.py
```

## Notas de Seguridad

- NO incluir en git: `.env` con claves de API
- Usar `.gitignore` para proteger archivos sensibles
- NO exponer: `homework-es.md` con respuestas
- OK exponer: Código, `RESUMEN_CONCEPTOS.md`, `POST_LINKEDIN.md`

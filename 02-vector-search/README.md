# Módulo 2 - Vector Search (Homework 2)

Este directorio contiene la solución para el Módulo 2 de LLM Zoomcamp.

## Descripción

Implementación de búsqueda por vectores usando modelos de embeddings con ONNX Runtime.

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

- **numpy**: Operaciones numéricas
- **onnxruntime**: Runtime para modelos ONNX
- **tokenizers**: Tokenización de texto
- **tqdm**: Barra de progreso
- **minsearch**: Búsqueda mínima eficiente
- **gitsource**: Herramienta para trabajar con repositorios Git
- **python-dotenv**: Gestión de variables de entorno

## Configuración

### Variables de Entorno

Crear un archivo `.env` en la raíz del proyecto:

```bash
# Configuración según sea necesario
```

## Estructura

- **main.py** o scripts de búsqueda: Implementación principal
- **pyproject.toml**: Configuración del proyecto
- **models/**: Modelos ONNX pre-entrenados
- **.env**: Variables de entorno (no incluir en git)

## Ejecución

```bash
# Con pip
python main.py

# O con uv
uv run python main.py
```

## Características Clave

- Búsqueda por similitud vectorial
- Embeddings con modelos ONNX
- Integración con minsearch
- Tokenización eficiente

## Notas de Seguridad

- NO incluir en git: `.env` con información sensible
- Usar `.gitignore` para proteger archivos sensibles
- NO exponer: `homework-es.md` con respuestas
- OK exponer: Código, `RESUMEN_CONCEPTOS.md`, `POST_LINKEDIN.md`

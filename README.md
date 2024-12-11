# Asistente Financiero AI

## Descripción General
Este proyecto implementa un asistente financiero que utiliza tecnologías de inteligencia artificial para proporcionar información en tiempo real sobre precios de acciones. El asistente utiliza la biblioteca [Gradio](https://www.gradio.app/) para crear una interfaz de usuario web, y hace uso de servicios externos como [Groq AI](https://console.groq.com/) y [Pydantic AI](https://console.x.ai/) para obtener y procesar datos financieros. La aplicación permite a los usuarios realizar consultas en lenguaje natural y obtener información detallada sobre acciones, incluyendo precios actuales, cambios porcentuales y análisis comparativos.

## Agentes Involucrados
El proyecto utiliza los siguientes agentes para obtener y procesar información financiera:

1. **Agente de Pydantic AI**: Este agente se encarga de consultar precios de acciones utilizando la herramienta `obtener_precio_accion`. Procesa la información y la devuelve en un formato estructurado, utilizando modelos Pydantic para validar y organizar los datos.

2. **Groq AI**: Este servicio se utiliza para obtener información financiera a través de una API. El proyecto llama a la API de Groq para obtener datos detallados sobre acciones, aprovechando su modelo `llama3-groq-70b-8192-tool-use-preview`.

3. **Grok**: Similar a Groq AI, este servicio también se utiliza para obtener información financiera. El proyecto utiliza Grok para complementar los datos obtenidos de Groq AI, permitiendo consultas a través de su API.

## Características Principales
- **Consulta en Lenguaje Natural**: Permite a los usuarios realizar consultas sobre precios de acciones utilizando un lenguaje coloquial.
- **Información en Tiempo Real**: Proporciona datos actualizados sobre precios de acciones, incluyendo el precio actual, el cambio porcentual y la tendencia.
- **Análisis Comparativo**: Ofrece un análisis comparativo básico, mostrando el máximo y mínimo precio entre las acciones consultadas.
- **Interfaz Intuitiva**: Utiliza Gradio para crear una interfaz de usuario web amigable y fácil de usar.
- **Soporte para Múltiples Servicios**: Permite utilizar tanto Groq AI como Grok para obtener información financiera, ofreciendo flexibilidad y redundancia en la obtención de datos.

## Requerimientos
Para ejecutar este proyecto, necesitarás instalar las siguientes bibliotecas de Python:

- `gradio`
- `pydantic_ai`
- `pydantic`
- `yfinance`
- `asyncio`
- `pandas`
- `openai`

Puedes instalar estas bibliotecas utilizando `pip`:

```bash
pip install gradio pydantic_ai pydantic yfinance pandas openai
```

## Configuración de Variables de Entorno
El proyecto requiere configurar las siguientes variables de entorno para acceder a los servicios externos:

- `GROQ_API_KEY`: Clave de API para Groq AI.
- `GROK_API_KEY`: Clave de API para Grok.

Puedes configurar estas variables de entorno en tu sistema operativo o en un archivo `.env` en la raíz del proyecto. Si usas un archivo `.env`, asegúrate de que esté incluido en tu archivo `.gitignore` para no compartir claves sensibles.

Ejemplo de archivo `.env`:

```bash
GROQ_API_KEY=your_groq_api_key_here
GROK_API_KEY=your_grok_api_key_here
```

## Ejecución del Proyecto
Para ejecutar el proyecto, simplemente ejecuta el siguiente comando en la terminal:

```bash
python app.py
```

Esto iniciará la interfaz de usuario web en tu navegador predeterminado, donde podrás realizar consultas sobre precios de acciones.

## Autor
Desarrollado por **Ricardo Fernández**

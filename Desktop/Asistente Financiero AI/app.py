import os
import gradio as gr
from pydantic_ai import Agent
from pydantic import BaseModel
import yfinance as yf
import asyncio
from datetime import datetime
import pandas as pd
from typing import List
from openai import OpenAI
import json

# Modelo para resultados de precios de acciones individuales
class ResultadoPrecioAccion(BaseModel):
    simbolo: str
    precio: float
    moneda: str = "USD"
    company_name: str
    previous_close: float
    percentage_change: float
    timestamp: str

# Modelo para agrupar los resultados de múltiples acciones
class ResultadosPreciosAcciones(BaseModel):
    resultados: List[ResultadoPrecioAccion]

# Función para ejecutar la herramienta de obtención de precio de acción
async def obtener_precio_accion_async(simbolo: str) -> dict:
    ticker = yf.Ticker(simbolo)
    try:
        info = ticker.fast_info
        precio = info.last_price
        if precio is None:
            raise ValueError(f"No se encontró información para el símbolo '{simbolo}'.")
        company_name = ticker.info.get('shortName', 'N/A')
        previous_close = info.previous_close
        percentage_change = ((precio - previous_close) / previous_close) * 100 if previous_close != 0 else 0
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return {
            "simbolo": simbolo,
            "precio": round(precio, 2),
            "moneda": "USD",
            "company_name": company_name,
            "previous_close": round(previous_close, 2),
            "percentage_change": round(percentage_change, 2),
            "timestamp": timestamp
        }
    except Exception as e:
        raise ValueError(f"Error al obtener datos para '{simbolo}': {str(e)}")

# Función para llamar a la API de Grok (síncrona)
def call_grok_api(api_key, consulta):
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.x.ai/v1",
    )

    functions = [
        {
            "name": "obtener_info_accion",
            "description": "Obtiene información sobre el precio de una o varias acciones.",
            "parameters": {
                "type": "object",
                "properties": {
                    "consulta": {
                        "type": "string",
                        "description": "La consulta del usuario sobre el precio de las acciones.",
                    },
                },
                "required": ["consulta"],
            },
        }
    ]

    tools = [{"type": "function", "function": f} for f in functions]

    messages = [
        {"role": "system", "content": "Eres un asistente financiero útil."},
        {"role": "user", "content": consulta}
    ]

    try:
        # Llama a la API
        response = client.chat.completions.create(
            model="grok-beta",  # Asegúrate de que el modelo es correcto
            messages=messages,
            tools=tools,
        )

        # Verifica si la respuesta tiene contenido esperado
        if hasattr(response, "choices") and len(response.choices) > 0:
            response_message = response.choices[0].message
            if hasattr(response_message, "tool_calls") and response_message.tool_calls:
                tool_call = response_message.tool_calls[0]
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                if function_name == "obtener_info_accion":
                    # Ejecutar la función asíncrona usando asyncio.run
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        resultados = loop.run_until_complete(
                            obtener_info_accion(
                                function_args["consulta"],
                                os.environ.get("GROQ_API_KEY"),
                                api_key, True, False
                            )
                        )
                    finally:
                        loop.close()
                    return resultados

                else:
                    return f"Función desconocida: {function_name}"
            else:
                return response_message.content
        else:
            return "La API no devolvió una respuesta válida."

    except Exception as e:
        return f"Error al llamar a la API de Grok: {e}"

# Función principal para obtener información de acciones (asíncrona)
async def obtener_info_accion(consulta: str, groq_api_key: str, grok_api_key: str, use_groq: bool, use_grok: bool) -> str:
    try:
        if use_groq:
            # Usar Groq AI
            os.environ["GROQ_API_KEY"] = groq_api_key

            # Inicializa el agente de Pydantic AI
            agente_acciones = Agent(
                "groq:llama3-groq-70b-8192-tool-use-preview",
                result_type=ResultadosPreciosAcciones,
                system_prompt="Eres un asistente financiero útil que puede consultar precios de acciones. Usa la herramienta obtener_precio_accion para obtener datos actuales y devuelve la información en el formato especificado. Debes proporcionar información para todas las acciones solicitadas."
            )

            # Herramienta para obtener el precio de una acción
            @agente_acciones.tool_plain
            async def obtener_precio_accion_tool(simbolo: str) -> dict:
                return await obtener_precio_accion_async(simbolo)

            # Ejecutar la consulta
            response = await agente_acciones.run(consulta)

            # Procesar los resultados
            data_frames = []
            errores = []
            for resultado in response.data.resultados:
                try:
                    data_frames.append(pd.DataFrame([{
                        'Símbolo': resultado.simbolo,
                        'Nombre de la Empresa': resultado.company_name,
                        'Precio Actual': f"${resultado.precio:.2f} {resultado.moneda}",
                        'Última Actualización': resultado.timestamp,
                        'Cambio en Precio': f"{resultado.percentage_change:.2f}%",
                        'Tendencia': '📈' if resultado.percentage_change >= 0 else '📉'
                    }]))
                except Exception as e:
                    errores.append(pd.DataFrame([{'Símbolo': resultado.simbolo, 'Error': str(e)}]))

            # Concatena todos los DataFrames
            if data_frames:
                data_df = pd.concat(data_frames, ignore_index=True)
            else:
                data_df = pd.DataFrame()

            if errores:
                error_df = pd.concat(errores, ignore_index=True)
            else:
                error_df = pd.DataFrame()

            respuesta = "📈 Información de las Acciones\n\n"
            if not data_df.empty:
                respuesta += data_df.to_string(index=False) + "\n\n"
            if not error_df.empty:
                respuesta += "### Errores:\n" + error_df.to_string(index=False) + "\n\n"
            if not data_df.empty:
                respuesta += "### Análisis Comparativo:\n"
                respuesta += f"- **Máximo Precio:** {data_df['Precio Actual'].max()}\n"
                respuesta += f"- **Mínimo Precio:** {data_df['Precio Actual'].min()}\n"

            return respuesta

        elif use_grok:
            # Usar Grok API (llamada asíncrona a call_grok_api)
            # return await asyncio.to_thread(call_grok_api, grok_api_key, consulta)
            return await asyncio.get_event_loop().run_in_executor(None, call_grok_api, grok_api_key, consulta)

        else:
            return "⚠️ Por favor, selecciona al menos un modelo para usar."

    except Exception as e:
        return f"⚠️ **Error:** {str(e)}\nPor favor, ingresa una consulta válida."

# Tema personalizado con tonos claros
tema_personalizado = gr.themes.Soft(
    primary_hue=gr.themes.Color(
        c50='#e6f2ff',
        c100='#b3dcff',
        c200='#4dabf7',
        c300='#2196f3',
        c400='#1e88e5',
        c500='#1976d2',
        c600='#1565c0',
        c700='#0b3d91',
        c800='#082963',
        c900='#051839',
        c950='#030c1f'
    ),
    neutral_hue=gr.themes.Color(
        c50='#f5f5f5',
        c100='#e0e0e0',
        c200='#bdbdbd',
        c300='#9e9e9e',
        c400='#757575',
        c500='#616161',
        c600='#424242',
        c700='#212121',
        c800='#121212',
        c900='#010101',
        c950='#000000'
    )
)

# Crear la interfaz de Gradio con el tema personalizado
with gr.Blocks(title="Asistente Financiero AI", theme=tema_personalizado) as demo:
    # Encabezado con markdown
    gr.Markdown(
        """
        # 💹 Asistente de Precios de Acciones AI
        ## Consulta Instantánea de Información Bursátil
        """
    )

    # Sección de instrucciones
    gr.Markdown(
        """
        ### 🎯 Guía Rápida
        - Ingresa una consulta en lenguaje coloquial (ej. "¿Cuál es el precio de Apple y Microsoft?")
        - Obtén información de precio en tiempo real
        - Soporta mercados de valores globales
        """
    )

    # Diseño de entrada y salida
    with gr.Column():
        consulta = gr.Textbox(
            label="Ingrese la consulta",
            placeholder="Ingrese una consulta en lenguaje coloquial",
            lines=1,
            elem_id="input-textbox"
        )
        groq_api_key = gr.Textbox(
            label="Groq AI API Key",
            placeholder="Ingrese su API Key de Groq AI (opcional si no usa Groq)",
            type="password",
            value=os.environ.get("GROQ_API_KEY", "")
        )
        grok_api_key = gr.Textbox(
            label="Grok API Key",
            placeholder="Ingrese su API Key de Grok (opcional si no usa Grok)",
            type="password",
            value=os.environ.get("GROK_API_KEY", "")
        )
        with gr.Row():
            use_groq = gr.Checkbox(label="Usar Groq AI", value=True)
            use_grok = gr.Checkbox(label="Usar Grok", value=False)
        boton = gr.Button("Consultar Precio 🔍", variant="primary", elem_id="consultar-button")

    # Sección de salida
    salida = gr.Textbox(
        label="Resultados",
        placeholder="La información de la acción aparecerá aquí...",
        lines=10,
        interactive=False,
        elem_id="output-textbox"
    )

    # Pie de página con autor
    gr.Markdown(
        """
        ---
        ### 🚀 Potenciado por Tecnología AI
        Desarrollado con ❤️ usando Python, Gradio, Groq  y Grok 
        **Creado por: Ricardo Fernández**
        """
    )

    # Conectar evento de clic del botón
    boton.click(
        obtener_info_accion,
        inputs=[consulta, groq_api_key, grok_api_key, use_groq, use_grok],
        outputs=salida
    )

# Lanzar la aplicación
if __name__ == "__main__":
    demo.launch(share=True)
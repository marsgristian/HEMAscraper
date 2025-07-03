#Utilizar API GEMINI e OPENAI como alternativa

import os
import google.generativeai as genai
import openai

# Configurar OpenAI
openai.api_key = "chave-exemplo"

def traduzir_texto_contextualizado_openai(texto, idioma_origem, idioma_destino, contexto="", api_key=None):
    
    prompt = f"""
    Contexto: {contexto}
    *APENAS RESPONDA O TEXTO TRADUZIDO, NÃO RESPONDA NADA MAIS*
    Traduz o seguinte texto do {idioma_origem} para o {idioma_destino}, 
    mantendo o estilo e o significado original:
    
    {texto}
    """
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Erro na traducao contextualizada OpenAI: {e}")
        return None

def traduzir_texto_hibrido(texto, idioma_origem, idioma_destino, contexto="", openai_api_key=None):

    if openai_api_key:
        resultado = traduzir_texto_contextualizado_openai(texto, idioma_origem, idioma_destino, contexto, openai_api_key)
        if resultado:
            return resultado, "openai"
    
    return None, "failed"
import os
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import logging
import requests

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar Groq
API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    raise ValueError("GROQ_API_KEY não configurada. Configure a variável de ambiente. Obtenha em https://console.groq.com/")

# Carregar CSV
csv_path = "base_faq_one_organizada.csv"
try:
    df = pd.read_csv(csv_path, encoding='utf-8')
    # Criar contexto a partir do CSV
    csv_context = df.to_string()
    logger.info("CSV carregado com sucesso!")
except FileNotFoundError:
    raise FileNotFoundError(f"Arquivo {csv_path} não encontrado")
except Exception as e:
    logger.error(f"Erro ao carregar CSV: {e}")
    raise

# Sistema de prompt com context
SYSTEM_PROMPT = f"""Você é um assistente amigável e entusiasmado de suporte para uma empresa de programação (ONE - Alura).
Você tem acesso a uma base de dados com informações sobre cronogramas, eventos, métricas de desempenho e atividades.

INFORMAÇÕES DA BASE DE DADOS:
{csv_context}

Instruções de Formatação e Estilo:
1. Use emojis relevantes e alegres para tornar a conversa mais amigável 😊
2. Organize a resposta em parágrafos curtos e claros
3. Use quebras de linha entre informações diferentes
4. Destaque informações importantes com emojis (📅 para datas, 📊 para métricas, 🎯 para objetivos, etc)
5. Seja entusiasmado e motivador na comunicação
6. Use listas com bullets quando apropriado

Instruções de Conteúdo:
1. Responda APENAS baseado nas informações fornecidas acima
2. Se não souber a resposta, diga de forma amigável que a informação não está disponível
3. Para datas e eventos, mostre as informações de forma clara e organizada
4. Para métricas, contextualize o significado
5. Sempre cite a categoria quando relevante (ex: "Cronograma de Especialização", "Desempenho")
6. Responda em português do Brasil com tom conversacional

Exemplo de Formatação:
"Oi! 👋 Achei a informação que você pediu!

📅 Data do Evento:
A próxima live será em [data], às [hora].

📊 Mais Detalhes:
[Informação adicional]

Algo mais que eu possa ajudar? 😊"
"""

class Message(BaseModel):
    text: str

@app.post("/api/chat")
async def chat(message: Message):
    """Endpoint para enviar mensagens ao chatbot"""
    try:
        if not message.text or not message.text.strip():
            raise HTTPException(status_code=400, detail="Mensagem não pode estar vazia")
        
        logger.info(f"Pergunta recebida: {message.text}")
        
        try:
            # Usar a API do Groq
            url = "https://api.groq.com/openai/v1/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }
            
            # Lista de modelos atualizados e disponíveis (verificar em https://console.groq.com/docs/models)
            models_to_try = [
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant",
                "gemma2-9b-it",
                "mixtral-8x7b-32768"
            ]
            
            response_text = None
            last_error = None
            
            for model in models_to_try:
                try:
                    payload = {
                        "model": model,
                        "messages": [
                            {
                                "role": "system",
                                "content": SYSTEM_PROMPT
                            },
                            {
                                "role": "user",
                                "content": message.text
                            }
                        ],
                        "temperature": 0.7,
                        "max_tokens": 1024
                    }
                    
                    response = requests.post(url, json=payload, headers=headers, timeout=30)
                    
                    logger.info(f"Tentando modelo {model}: Status {response.status_code}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Extrair o texto da resposta
                        if "choices" in result and len(result["choices"]) > 0:
                            response_text = result["choices"][0]["message"]["content"]
                            
                            if response_text:
                                logger.info(f"Sucesso com modelo {model}")
                                return {
                                    "response": response_text,
                                    "status": "success"
                                }
                    else:
                        error_response = response.json() if response.text else {}
                        error_msg = error_response.get('error', {}).get('message', f'Status {response.status_code}')
                        last_error = f"{model}: {error_msg}"
                        logger.warning(f"Modelo {model} falhou: {error_msg}")
                        continue
                        
                except Exception as model_error:
                    last_error = str(model_error)
                    logger.warning(f"Erro ao tentar {model}: {last_error}")
                    continue
            
            logger.error(f"Nenhum modelo funcionou. Último erro: {last_error}")
            raise Exception(f"Nenhum modelo disponível: {last_error}")
            
        except Exception as groq_error:
            error_str = str(groq_error)
            logger.error(f"Erro ao chamar Groq: {error_str}")
            
            raise HTTPException(
                status_code=502, 
                detail=f"Erro ao conectar com o serviço de IA"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro no servidor")

@app.get("/api/health")
async def health():
    """Verificar saúde da API"""
    return {"status": "ok", "csv_loaded": len(df) > 0, "ai_provider": "Groq (Mixtral)"}

@app.get("/", response_class=HTMLResponse)
async def root():
    """Servir página inicial"""
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Erro: index.html não encontrado</h1>"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

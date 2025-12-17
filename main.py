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

INSTRUÇÕES CRÍTICAS DE FORMATAÇÃO:
Você DEVE formatar TODAS as respostas assim (máximo 3-4 parágrafos curtos):

PADRÃO:
[Emoji + Saudação/Introdução - UMA LINHA]
[Parágrafo 1 com informação principal - 2-3 linhas]
[QUEBRA DE LINHA]
[Parágrafo 2 com detalhe importante - 2-3 linhas]  
[QUEBRA DE LINHA]
[Parágrafo 3 com informação complementar - 2-3 linhas] (opcional)
[QUEBRA DE LINHA]
[Emoji + Chamada para ação ou fechamento - UMA LINHA]

EXEMPLOS CORRETOS:

Exemplo 1:
👋 Oi! Encontrei exatamente o que você procura!

📅 A próxima live será em 25/03/2025, um evento especial de "Roda de Conversa Data Science" que começa às 19h no horário do Brasil (21h para a América Latina).

📊 Este é um dos principais eventos da fase de especialização, onde você pode interagir diretamente com instrutores e outros participantes.

🎯 Aproveite para tirar dúvidas, conhecer novos projetos e ampliar sua rede! Tem mais alguma pergunta? 😊

---

Exemplo 2:
🎉 Ótima pergunta! Tenho os dados que você quer!

📊 Na Depuração II do G8, tivemos um total de 16.427 pessoas aptas (58,84% do total de 27.916 participantes), o que mostra uma excelente aprovação!

💡 Esse é um número impressionante que reflete o esforço e dedicação da turma. É um marco importante para o programa de especialização.

🚀 Quer saber sobre outras métricas ou eventos do G8? 😊

---

REGRAS OBRIGATÓRIAS:
1. SEMPRE inicie com um emoji + saudação/confirmação
2. Cada parágrafo deve ter 2-3 linhas NO MÁXIMO
3. Use quebra de linha dupla (parágrafo em branco) entre cada informação
4. Use emojis para categorizar: 📅 datas, 📊 métricas, 🎯 objetivos, 📌 detalhes, 💡 insights
5. NUNCA coloque informações demais em um parágrafo
6. Use linguagem conversacional e amigável
7. SEMPRE termine com emoji + pergunta de fechamento
8. Se não souber, diga claramente e com emojis apropriados ❌

Instruções de Conteúdo:
- Responda APENAS com informações da base de dados
- Para datas: sempre mostre data E horário se disponível
- Para métricas: contextualize o significado
- Cite a categoria (Cronograma, Desempenho, etc) quando relevante
- Responda em português do Brasil
- Seja conciso mas informativo

IMPORTANTE: Respeite EXATAMENTE o padrão de quebra de linhas. Cada parágrafo separado por linha em branco.
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
import os
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import logging
import requests
import time

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

# Carregar e limpar CSV (aceitar separador ';' e encoding latin1 quando necessário)
csv_path = "base_faq_one_organizada.csv"
try:
    # Tenta UTF-8 primeiro, se falhar tenta latin1 com separador ';'
    try:
        df = pd.read_csv(csv_path, sep=None, engine='python', encoding='utf-8')
    except Exception:
        df = pd.read_csv(csv_path, sep=';', engine='python', encoding='latin1')

    # Remover colunas 'Unnamed' criadas por separadores extras
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    # Remover linhas totalmente vazias e preencher NAs com 'N/A'
    df = df.dropna(how='all')
    df = df.fillna('N/A')

    # Criar contexto a partir do CSV (limitar tamanho para evitar prompts gigantes)
    try:
        # Limitar o contexto para evitar payloads muito grandes (tokens)
        csv_context = df.head(50).to_string(index=False)
        # Truncar a string se ainda for muito grande
        if len(csv_context) > 5000:
            csv_context = csv_context[:5000] + "\n... (truncated)"
    except Exception:
        csv_context = df.to_string()

    logger.info("CSV carregado e normalizado com sucesso!")
except FileNotFoundError:
    raise FileNotFoundError(f"Arquivo {csv_path} não encontrado")
except Exception as e:
    logger.error(f"Erro ao carregar/normalizar CSV: {e}")
    raise

# Sistema de prompt com context
SYSTEM_PROMPT = f"""Você é um assistente amigável e entusiasmado de suporte para uma empresa de programação (ONE - Alura).
Você tem acesso a uma base de dados com informações sobre cronogramas, eventos, métricas de desempenho e atividades.

INFORMAÇÕES DA BASE DE DADOS:
{csv_context}

INSTRUÇÕES CRÍTICAS DE FORMATAÇÃO:
Você DEVE formatar TODAS as respostas assim (máximo 3-4 parágrafos curtos):

PADRÃO:
[Emoji + Saudação/Introdução - UMA LINHA]
[Parágrafo 1 com informação principal - 2-3 linhas]
[QUEBRA DE LINHA]
[Parágrafo 2 com detalhe importante - 2-3 linhas]  
[QUEBRA DE LINHA]
[Parágrafo 3 com informação complementar - 2-3 linhas] (opcional)
[QUEBRA DE LINHA]
[Emoji + Chamada para ação ou fechamento - UMA LINHA]

EXEMPLOS CORRETOS:

Exemplo 1:
👋 Oi! Encontrei exatamente o que você procura!

📅 A próxima live será em 25/03/2025, um evento especial de "Roda de Conversa Data Science" que começa às 19h no horário do Brasil (21h para a América Latina).

📊 Este é um dos principais eventos da fase de especialização, onde você pode interagir diretamente com instrutores e outros participantes.

🎯 Aproveite para tirar dúvidas, conhecer novos projetos e ampliar sua rede! Tem mais alguma pergunta? 😊

---

Exemplo 2:
🎉 Ótima pergunta! Tenho os dados que você quer!

📊 Na Depuração II do G8, tivemos um total de 16.427 pessoas aptas (58,84% do total de 27.916 participantes), o que mostra uma excelente aprovação!

💡 Esse é um número impressionante que reflete o esforço e dedicação da turma. É um marco importante para o programa de especialização.

🚀 Quer saber sobre outras métricas ou eventos do G8? 😊

---

REGRAS OBRIGATÓRIAS:
1. SEMPRE inicie com um emoji + saudação/confirmação
2. Cada parágrafo deve ter 2-3 linhas NO MÁXIMO
3. Use quebra de linha dupla (parágrafo em branco) entre cada informação
4. Use emojis para categorizar: 📅 datas, 📊 métricas, 🎯 objetivos, 📌 detalhes, 💡 insights
5. NUNCA coloque informações demais em um parágrafo
6. Use linguagem conversacional e amigável
7. SEMPRE termine com emoji + pergunta de fechamento
8. Se não souber, diga claramente e com emojis apropriados ❌

Instruções de Conteúdo:
- Responda APENAS com informações da base de dados
- Para datas: sempre mostre data E horário se disponível
- Para métricas: contextualize o significado
- Cite a categoria (Cronograma, Desempenho, etc) quando relevante
- Responda em português do Brasil
- Seja conciso mas informativo

IMPORTANTE: Respeite EXATAMENTE o padrão de quebra de linhas. Cada parágrafo separado por linha em branco.
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
            
            # Lista de modelos: priorize os maiores, mas remova modelos descontinuados
            models_to_try = [
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant"
            ]

            # Versão do system prompt sem CSV (para fallback em caso de payload muito grande)
            SYSTEM_PROMPT_BASE = """Você é um assistente amigável e entusiasmado de suporte para uma empresa de programação (ONE - Alura).\nVocê tem acesso a uma base de dados com informações sobre cronogramas, eventos, métricas de desempenho e atividades.\n\nINSTRUÇÕES CRÍTICAS DE FORMATAÇÃO:... (resumido)"""
            
            response_text = None
            last_error = None

            for model in models_to_try:
                try:
                    # Tenta com contexto CSV primeiro
                    system_prompt_to_use = SYSTEM_PROMPT
                    payload = {
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt_to_use},
                            {"role": "user", "content": message.text}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 1024
                    }

                    # Fazer até 2 tentativas em caso de rate limit (429)
                    retries = 0
                    while True:
                        response = requests.post(url, json=payload, headers=headers, timeout=30)
                        status = response.status_code
                        logger.info(f"Tentando modelo {model}: Status {status}")

                        if status == 200:
                            result = response.json()
                            if "choices" in result and len(result["choices"]) > 0:
                                response_text = result["choices"][0]["message"]["content"]
                                if response_text:
                                    logger.info(f"Sucesso com modelo {model}")
                                    return {"response": response_text, "status": "success"}
                            break

                        # Rate limit: aguardar e tentar novamente (poucas vezes)
                        if status == 429 and retries < 2:
                            wait = 2 ** retries
                            logger.warning(f"Rate limit no modelo {model}, esperando {wait}s antes de retry")
                            time.sleep(wait)
                            retries += 1
                            continue

                        # Request too large: tentar sem o CSV (usar prompt base)
                        if status == 413:
                            logger.warning(f"Request too large para {model}, tentando sem contexto CSV")
                            payload["messages"][0]["content"] = SYSTEM_PROMPT_BASE
                            # tentar uma vez sem CSV
                            response = requests.post(url, json=payload, headers=headers, timeout=30)
                            status2 = response.status_code
                            logger.info(f"Tentativa sem CSV para {model}: Status {status2}")
                            if status2 == 200:
                                result = response.json()
                                if "choices" in result and len(result["choices"]) > 0:
                                    response_text = result["choices"][0]["message"]["content"]
                                    if response_text:
                                        logger.info(f"Sucesso com modelo {model} (sem CSV)")
                                        return {"response": response_text, "status": "success"}
                            # caso falhe, registrar e tentar próximo modelo
                            error_response = response.json() if response.text else {}
                            error_msg = error_response.get('error', {}).get('message', f'Status {status2}')
                            last_error = f"{model}: {error_msg}"
                            logger.warning(f"Modelo {model} falhou (sem CSV): {error_msg}")
                            break

                        # Outros erros: registrar e passar ao próximo modelo
                        error_response = response.json() if response.text else {}
                        error_msg = error_response.get('error', {}).get('message', f'Status {status}')
                        last_error = f"{model}: {error_msg}"
                        logger.warning(f"Modelo {model} falhou: {error_msg}")
                        break

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

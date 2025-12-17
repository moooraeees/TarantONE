# TarantONE — POC Chatbot

> Assistente de FAQ/cronogramas para o projeto ONE (POC). Backend em FastAPI, frontend estático em `index.html`.

Principais arquivos
- `main.py` — FastAPI app que lê `base_faq_one_organizada.csv` e consulta a API Groq.
- `index.html` — UI do chat (Vanilla JS + CSS).
- `base_faq_one_organizada.csv` — Dados de cronograma e métricas.
- `.env` — Contém `GROQ_API_KEY` (não comitar no Git).
- `Dockerfile` — Conteinerização (adicionado).

Como rodar localmente

1. Crie e ative um virtualenv (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Instale dependências:

```powershell
pip install -r requirements.txt
```

3. Crie arquivo `.env` (não comitar) com sua chave Groq:

```
GROQ_API_KEY=seu_token_aqui
```

4. Rode o servidor:

```powershell
# modo simples
python main.py

# ou com reload durante desenvolvimento
.venv\Scripts\uvicorn.exe main:app --host 0.0.0.0 --port 8000 --reload
```

5. Abra o frontend em: http://localhost:8000

Notas sobre CSV e encoding
- Se você ver caracteres corrompidos (�), abra o CSV e salve como UTF-8 (ou use `latin1`) antes de iniciar.

Deploy rápido (opções)

- Render: crie um Web Service, conecte ao GitHub, defina `Start Command`:

```
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Adicione `GROQ_API_KEY` nas Environment Variables do serviço.

- Railway: conecte repo e defina `Start Command` igual ao acima; adicione `GROQ_API_KEY` no dashboard.

- Docker (Cloud Run / Fly): use o `Dockerfile` abaixo e deploy conforme provedor.

Segurança
- Nunca comite chaves em `.env`. Se acidentalmente comitar, revogue a chave e gere uma nova.
- Para deploy em produção, guarde `GROQ_API_KEY` nas variáveis de ambiente do provedor.

Próximos passos sugeridos
- Implementar RAG (indexar CSV e buscar trechos relevantes em vez de enviar todo o CSV).
- Adicionar testes e logging centralizado.
- Automatizar deploy com GitHub Actions e GitHub Secrets.

---
© POC TarantONE
# ChatBot ONE - Assistente de Suporte

Chatbot web para responder perguntas sobre eventos, cronogramas e métricas usando a API Gemini.

## 🚀 Requisitos

- Python 3.8+
- Chave de API do Google Gemini

## 📋 Instalação

1. **Instale as dependências:**

```bash
pip install -r requirements.txt
```

2. **Configure a chave de API do Groq:**

Crie um arquivo `.env` na raiz do projeto e adicione sua chave:

```env
GROQ_API_KEY=sua_chave_aqui
```

Para obter uma chave **gratuita**, visite: https://console.groq.com/

> **Groq é gratuito e super rápido!** 🚀 Você recebe créditos grátis suficientes para testar bastante.

3. **Certifique-se que o arquivo CSV está no diretório:**

O arquivo `base_faq_one_organizada.csv` deve estar na mesma pasta que `main.py`

## ▶️ Executando a Aplicação

```bash
python main.py
```

A aplicação estará disponível em: **http://localhost:8000**

## 🎯 Funcionalidades

- ✅ Interface web responsiva e moderna
- ✅ Chatbot powered by Gemini AI
- ✅ Leitura automática do arquivo CSV
- ✅ Respostas baseadas em dados estruturados
- ✅ Suporte a perguntas naturais
- ✅ Design interativo com animações

## 📝 Exemplo de Perguntas

- "Qual é a data da próxima live?"
- "Quantas pessoas passaram no Depuração II?"
- "Quando é a graduação do G8?"
- "Quais são os eventos de Data Science?"

## 🔧 Estrutura do Projeto

```
Projeto_v3/
├── main.py                          # Backend FastAPI
├── index.html                       # Frontend
├── base_faq_one_organizada.csv     # Base de dados
├── requirements.txt                # Dependências Python
└── .env                            # Variáveis de ambiente
```

## 🛠️ Tecnologias Utilizadas

- **Backend:** FastAPI + Uvicorn
- **IA:** Groq API (Modelo Mixtral-8x7b) - GRATUITO
- **Frontend:** HTML5 + CSS3 + JavaScript
- **Data:** Pandas + CSV

## ⚙️ Configuração Avançada

### Alterar porta de execução

Edite `main.py` e mude a porta em:

```python
uvicorn.run(app, host="0.0.0.0", port=8080)  # Mude 8000 para sua porta
```

### Acessar de outras máquinas

O aplicativo está configurado para aceitar conexões externas. Acesse:

```
http://seu_ip:8000
```

## 📞 Suporte

Se encontrar problemas:
1. Verifique se a chave da API está correta em `.env`
2. Certifique-se que o CSV está no local correto
3. Verifique se todas as dependências foram instaladas: `pip install -r requirements.txt`

---

**Desenvolvido com ❤️ para suporte eficiente**

# 🎓 Professora Polly! - Speech-to-Speech English Learning Assistant

Assistente de voz em tempo real para aprender inglês usando AWS Bedrock (Amazon Nova) e Amazon Polly.

## 🚀 Deploy no Streamlit Cloud

### Passo 1: Configurar Variáveis de Ambiente
No Streamlit Cloud, adicione:
- `AWS_ACCESS_KEY_ID` - Sua access key da AWS
- `AWS_SECRET_ACCESS_KEY` - Sua secret key da AWS

### Passo 2: Deploy
O app será iniciado automaticamente com todas as dependências instaladas.

## 🎯 Como Usar

1. Clique em "Conectar"
2. Pressione e segure a tecla **ESPAÇO**
3. Fale em inglês
4. Solte a tecla **ESPAÇO**
5. Ouça a resposta da professora

## 🏗️ Arquitetura

- **Frontend**: Streamlit + WebSocket para captura de áudio
- **Backend**: FastAPI com WebSocket
- **Transcrição**: Google Speech Recognition (rápido e gratuito)
- **IA**: Amazon Nova Pro (Bedrock) para geração de respostas
- **Síntese de Voz**: Amazon Polly (voz Camila - português brasileiro)

## 📦 Dependências

- Python 3.9+
- AWS Bedrock access
- AWS Polly access
- FFmpeg (para conversão de áudio)

## 🔧 Desenvolvimento Local

```bash
# Instalar dependências
pip install -r requirements.txt

# Iniciar app (backend inicia automaticamente)
streamlit run app.py
```

## 📝 Licença

MIT

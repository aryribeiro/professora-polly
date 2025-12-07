import streamlit as st
import streamlit.components.v1 as components
import boto3
import os
from dotenv import load_dotenv
import base64

load_dotenv()

# Configurar AWS
@st.cache_resource
def get_clients():
    bedrock = boto3.client(
        service_name='bedrock-runtime',
        region_name='us-east-1',
        aws_access_key_id=st.secrets.get('AWS_ACCESS_KEY_ID', os.getenv('AWS_ACCESS_KEY_ID')),
        aws_secret_access_key=st.secrets.get('AWS_SECRET_ACCESS_KEY', os.getenv('AWS_SECRET_ACCESS_KEY'))
    )
    
    polly = boto3.client(
        service_name='polly',
        region_name='us-east-1',
        aws_access_key_id=st.secrets.get('AWS_ACCESS_KEY_ID', os.getenv('AWS_ACCESS_KEY_ID')),
        aws_secret_access_key=st.secrets.get('AWS_SECRET_ACCESS_KEY', os.getenv('AWS_SECRET_ACCESS_KEY'))
    )
    return bedrock, polly

bedrock, polly = get_clients()

SYSTEM_PROMPT = """You are having a ONE-ON-ONE conversation with a single Brazilian adult learning English. Speak directly to THEM (not "pessoal" or "vocês"). 

RULES:
- Keep responses SHORT (2-3 sentences max)
- Speak naturally like talking to ONE friend
- Mix Portuguese and English naturally
- Ask simple questions to keep conversation flowing
- Be warm and encouraging
- NEVER give long lessons or lists
- Focus on natural back-and-forth dialogue

Example:
"Oi! Como você está? How are you today?"
"Legal! Let's practice. What's your name?"
"Muito bem! Now tell me, do you like coffee?"

Keep it conversational and brief!"""

st.set_page_config(page_title="Professora Polly!", page_icon="🎓", layout="centered")

st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>🎓 Professora Polly!</h1><p>Conversa em Tempo Real - Speech-to-Speech</p></div>', unsafe_allow_html=True)

html_code = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 30px;
            padding: 50px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            text-align: center;
            max-width: 500px;
            width: 100%;
        }
        #connectButton {
            width: 200px;
            height: 200px;
            border-radius: 50%;
            border: none;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-size: 80px;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
            margin: 20px auto;
        }
        #connectButton:hover {
            transform: scale(1.05);
        }
        #connectButton.connected {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
            animation: pulse 2s infinite;
        }
        #connectButton.speaking {
            background: linear-gradient(135deg, #6bcf7f 0%, #48bb78 100%);
            animation: pulse 1s infinite;
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        #status {
            margin-top: 30px;
            font-size: 22px;
            font-weight: bold;
            color: #333;
        }
    </style>
</head>
<body>
    <div class="container">
        <button id="connectButton" onclick="toggleConnection()">🎤</button>
        <div id="status">Clique para conectar</div>
    </div>

    <script>
        let ws;
        let isConnected = false;
        let mediaRecorder;
        let stream;
        let currentAudio = null;
        
        const button = document.getElementById('connectButton');
        const status = document.getElementById('status');
        
        async function toggleConnection() {
            if (!isConnected) {
                await connect();
            } else {
                disconnect();
            }
        }
        
        async function connect() {
            try {
                // Sem WebSocket - usar Streamlit diretamente
                isConnected = true;
                button.className = 'connected';
                button.innerHTML = '🔴';
                status.textContent = '🎙️ Pressione ESPAÇO para falar';
                await startAudioCapture();
                return;
                
                ws.onopen = async () => {
                    console.log('WebSocket conectado');
                    isConnected = true;
                    button.className = 'connected';
                    button.innerHTML = '🔴';
                    status.textContent = '🎙️ Pressione ESPAÇO para falar';
                    
                    await startAudioCapture();
                };
                
                ws.onmessage = (event) => {
                    console.log('Áudio recebido');
                    playAudio(event.data);
                };
                
                ws.onerror = (error) => {
                    console.error('Erro WebSocket:', error);
                    status.textContent = '❌ Erro na conexão';
                };
                
                ws.onclose = () => {
                    console.log('WebSocket fechado');
                    if (isConnected) {
                        status.textContent = '❌ Conexão perdida. Clique para reconectar';
                        isConnected = false;
                        button.className = '';
                        button.innerHTML = '🎤';
                    }
                };
                
            } catch (err) {
                status.textContent = '❌ Erro: ' + err.message;
            }
        }
        
        function disconnect() {
            if (ws) {
                ws.close();
            }
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                mediaRecorder.stop();
            }
            if (currentAudio) {
                currentAudio.pause();
                currentAudio.currentTime = 0;
                currentAudio = null;
            }
            
            isConnected = false;
            button.className = '';
            button.innerHTML = '🎤';
            status.textContent = 'Desconectado';
        }
        
        async function startAudioCapture() {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {
                status.textContent = '❌ Use Chrome ou Edge';
                return;
            }
            
            const recognition = new SpeechRecognition();
            recognition.lang = 'pt-BR';
            recognition.continuous = false;
            recognition.interimResults = false;
            
            let isRecognizing = false;
            
            document.addEventListener('keydown', (e) => {
                if (e.code === 'Space' && !isRecognizing && isConnected) {
                    e.preventDefault();
                    isRecognizing = true;
                    recognition.start();
                    status.textContent = '🔴 Ouvindo... Solte ESPAÇO';
                }
            });
            
            document.addEventListener('keyup', (e) => {
                if (e.code === 'Space' && isRecognizing) {
                    e.preventDefault();
                    recognition.stop();
                }
            });
            
            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                console.log('Você disse:', transcript);
                status.textContent = '⏳ Processando...';
                
                // Enviar para Streamlit
                window.parent.postMessage({type: 'streamlit:setComponentValue', value: transcript}, '*');
            };
            
            recognition.onend = () => {
                isRecognizing = false;
            };
            
            recognition.onerror = (event) => {
                console.error('Erro reconhecimento:', event.error);
                isRecognizing = false;
                if (isConnected) {
                    if (event.error === 'no-speech') {
                        status.textContent = '⚠️ Não ouvi nada. Tente novamente';
                    } else if (event.error === 'aborted') {
                        status.textContent = '🎙️ Pressione ESPAÇO para falar';
                    } else {
                        status.textContent = '🎙️ Pressione ESPAÇO para falar';
                    }
                }
            };
        }
        
        // Receber áudio do Streamlit
        window.addEventListener('message', (event) => {
            if (event.data.type === 'playAudio') {
                playAudio(event.data.audio);
            }
        });
        
        function playAudio(audioB64) {
            if (!isConnected) return;
            
            if (currentAudio) {
                currentAudio.pause();
                currentAudio = null;
            }
            
            button.className = 'speaking';
            button.innerHTML = '🔊';
            status.textContent = '🔊 Professora falando...';
            
            const audioBytes = Uint8Array.from(atob(audioB64), c => c.charCodeAt(0));
            const audioBlob = new Blob([audioBytes], { type: 'audio/mpeg' });
            const audioUrl = URL.createObjectURL(audioBlob);
            currentAudio = new Audio(audioUrl);
            currentAudio.volume = 1.0;
            
            currentAudio.play();
            
            currentAudio.onended = () => {
                URL.revokeObjectURL(audioUrl);
                currentAudio = null;
                if (isConnected) {
                    button.className = 'connected';
                    button.innerHTML = '🔴';
                    status.textContent = '🎙️ Pressione ESPAÇO para falar';
                }
            };
        }
    </script>
</body>
</html>
"""

# Inicializar session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Processar nova mensagem
user_input = components.html(html_code, height=600)

if user_input and isinstance(user_input, str) and len(user_input.strip()) > 0:
    if user_input not in [msg.get('input') for msg in st.session_state.messages]:
        try:
            # Gerar resposta
            response = bedrock.converse(
                modelId='amazon.nova-pro-v1:0',
                messages=[{"role": "user", "content": [{"text": user_input.strip()}]}],
                system=[{"text": SYSTEM_PROMPT}],
                inferenceConfig={"temperature": 0.8, "topP": 0.9, "maxTokens": 100}
            )
            
            response_text = response['output']['message']['content'][0]['text']
            
            # Converter para áudio
            polly_response = polly.synthesize_speech(
                Text=response_text,
                OutputFormat='mp3',
                VoiceId='Camila',
                Engine='neural'
            )
            
            audio_bytes = polly_response['AudioStream'].read()
            audio_b64 = base64.b64encode(audio_bytes).decode()
            
            # Salvar
            st.session_state.messages.append({
                'input': user_input,
                'response': response_text,
                'audio': audio_b64
            })
            
            # Injetar áudio no iframe
            components.html(f"""
            <script>
                const audioB64 = '{audio_b64}';
                const audioBytes = Uint8Array.from(atob(audioB64), c => c.charCodeAt(0));
                const audioBlob = new Blob([audioBytes], {{type: 'audio/mpeg'}});
                const audioUrl = URL.createObjectURL(audioBlob);
                const audio = new Audio(audioUrl);
                audio.play();
            </script>
            """, height=0)
            
        except Exception as e:
            st.error(f"Erro: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    <strong>🎓 Professora Polly!</strong> - Desenvolvido para interação em tempo real<br>
    por <strong>Ary Ribeiro</strong>: <a href="mailto:aryribeiro@gmail.com">aryribeiro@gmail.com</a><br>
    <small>Versão 1.0 | Streamlit + Python</small>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    .main {
        background-color: #ffffff;
        color: #333333;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }
    /* Esconde completamente todos os elementos da barra padrão do Streamlit */
    header {display: none !important;}
    footer {display: none !important;}
    #MainMenu {display: none !important;}
    /* Remove qualquer espaço em branco adicional */
    div[data-testid="stAppViewBlockContainer"] {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    div[data-testid="stVerticalBlock"] {
        gap: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    /* Remove quaisquer margens extras */
    .element-container {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
    }
</style>
""", unsafe_allow_html=True)
import streamlit as st
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Professora Polly!", page_icon="🎓", layout="centered")

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

SYSTEM_PROMPT = """You are having a ONE-ON-ONE conversation with a single Brazilian adult learning English. Speak directly to THEM. Keep responses SHORT (2-3 sentences max). Mix Portuguese and English naturally. Be warm and encouraging."""

st.markdown('<div style="text-align: center;"><h1>🎓 Professora Polly!</h1><p>Aprendizado de Inglês com IA</p></div>', unsafe_allow_html=True)

if 'messages' not in st.session_state:
    st.session_state.messages = []

user_text = st.text_input("🎙️ Digite ou fale sua mensagem:", key="user_input", placeholder="Ex: Hello, how are you?")

if st.button("🔊 Enviar e Ouvir", type="primary", use_container_width=True):
    if user_text:
        with st.spinner('🤔 Pensando...'):
            response = bedrock.converse(
                modelId='amazon.nova-pro-v1:0',
                messages=[{"role": "user", "content": [{"text": user_text}]}],
                system=[{"text": SYSTEM_PROMPT}],
                inferenceConfig={"temperature": 0.8, "topP": 0.9, "maxTokens": 100}
            )
            
            response_text = response['output']['message']['content'][0]['text']
            
            polly_response = polly.synthesize_speech(
                Text=response_text,
                OutputFormat='mp3',
                VoiceId='Camila',
                Engine='neural'
            )
            
            audio_bytes = polly_response['AudioStream'].read()
            
            st.session_state.messages.append({'user': user_text, 'bot': response_text})
            
            st.success(f"🗣️ Você: {user_text}")
            st.info(f"🎓 Professora: {response_text}")
            st.audio(audio_bytes, format='audio/mp3')

if st.session_state.messages:
    with st.expander("📝 Histórico"):
        for msg in st.session_state.messages[-5:]:
            st.write(f"**Você:** {msg['user']}")
            st.write(f"**Professora:** {msg['bot']}")
            st.divider()

html_code_hidden = """
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

st.markdown("---")
st.markdown('<div style="text-align: center; color: #666;"><strong>🎓 Professora Polly!</strong><br>por Ary Ribeiro</div>', unsafe_allow_html=True)
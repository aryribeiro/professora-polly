import streamlit as st
import streamlit.components.v1 as components
import subprocess
import time
import os

# Iniciar backend automaticamente
@st.cache_resource
def start_backend():
    import sys
    import socket
    
    # Verificar se backend já está rodando
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', 8001))
    sock.close()
    
    if result == 0:
        return None  # Backend já está rodando
    
    # Iniciar backend
    backend_path = os.path.join(os.path.dirname(__file__), "backend.py")
    backend_process = subprocess.Popen(
        [sys.executable, backend_path]
    )
    time.sleep(3)
    return backend_process

start_backend()

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
                ws = new WebSocket('ws://localhost:8001/ws');
                
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
                
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ text: transcript }));
                    status.textContent = '⏳ Aguardando resposta...';
                } else {
                    status.textContent = '❌ Conexão perdida';
                }
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
        
        function playAudio(audioData) {
            if (!isConnected) return;
            
            if (currentAudio) {
                currentAudio.pause();
                currentAudio = null;
            }
            
            button.className = 'speaking';
            button.innerHTML = '🔊';
            status.textContent = '🔊 Professora falando...';
            
            const audioBlob = new Blob([audioData], { type: 'audio/mpeg' });
            const audioUrl = URL.createObjectURL(audioBlob);
            currentAudio = new Audio(audioUrl);
            currentAudio.volume = 1.0;
            
            currentAudio.play().then(() => {
                console.log('Reproduzindo áudio...');
            }).catch(e => {
                console.error('Erro ao reproduzir:', e);
            });
            
            currentAudio.onended = () => {
                console.log('Áudio finalizado');
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

components.html(html_code, height=600)

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
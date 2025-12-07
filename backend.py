from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import boto3
import json
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "Backend rodando", "websocket": "/ws"}

bedrock = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)



polly = boto3.client(
    service_name='polly',
    region_name='us-east-1',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)



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

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Cliente conectado")
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            user_text = message.get('text', 'Hello')
            
            response = bedrock.converse(
                modelId='amazon.nova-pro-v1:0',
                messages=[{
                    "role": "user",
                    "content": [{"text": user_text}]
                }],
                system=[{"text": SYSTEM_PROMPT}],
                inferenceConfig={
                    "temperature": 0.8,
                    "topP": 0.9,
                    "maxTokens": 100
                }
            )
            
            response_text = response['output']['message']['content'][0]['text']
            
            polly_response = polly.synthesize_speech(
                Text=response_text,
                OutputFormat='mp3',
                VoiceId='Camila',
                Engine='neural'
            )
            
            audio_bytes = polly_response['AudioStream'].read()
            await websocket.send_bytes(audio_bytes)
            print("✅ Resposta enviada")
                
    except Exception as e:
        if "WebSocketDisconnect" not in str(type(e).__name__):
            print(f"Erro: {type(e).__name__}")
    finally:
        try:
            await websocket.close()
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
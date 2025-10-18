from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from services.llm_service import init_gemini_model
from services.db_service import fetch_last_5_chats, init_database, store_chat
from services.agent_service import create_agent
from fastapi.responses import HTMLResponse
# from langchain.schema import StrOutputParser

app = FastAPI(title="💬 Product Info Assistant API", version="1.0")

# Initialize once
@app.on_event("startup")
def startup_event():
    global agent, llm
    llm = init_gemini_model()
    db = init_database()
    agent = create_agent(llm, db)
    # parser = StrOutputParser()

# Request schema
class QueryRequest(BaseModel):
    user_query: str

# Root endpoint
@app.get("/", response_class=HTMLResponse)
def get_chat_ui():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>💬 Product Info Assistant</title>
      <style>
        body {
          font-family: Arial, sans-serif;
          background-color: #f4f6f8;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 100vh;
          margin: 0;
        }
        .chat-container {
          width: 90%;
          max-width: 600px;
          background: white;
          border-radius: 12px;
          box-shadow: 0 4px 10px rgba(0,0,0,0.1);
          display: flex;
          flex-direction: column;
          padding: 16px;
        }
        .chat-box {
          flex: 1;
          overflow-y: auto;
          max-height: 70vh;
          margin-bottom: 10px;
          border: 1px solid #ddd;
          padding: 10px;
          border-radius: 8px;
        }
        .message {
          margin: 8px 0;
        }
        .user {
          text-align: right;
          color: #1565c0;
          font-weight: bold;
        }
        .assistant {
          text-align: left;
          color: #2e7d32;
        }
        input {
          width: 80%;
          padding: 10px;
          border-radius: 8px;
          border: 1px solid #ccc;
        }
        button {
          padding: 10px 16px;
          margin-left: 8px;
          border: none;
          background-color: #1976d2;
          color: white;
          border-radius: 8px;
          cursor: pointer;
        }
        button:hover {
          background-color: #125ea3;
        }
      </style>
    </head>
    <body>
      <div class="chat-container">
        <h2>💬 Product Info Assistant</h2>
        <div class="chat-box" id="chat-box"></div>
        <div>
          <input type="text" id="user-input" placeholder="Ask something..." />
          <button onclick="sendMessage()">Send</button>
        </div>
      </div>

      <script>
        async function sendMessage() {
          const input = document.getElementById('user-input');
          const chatBox = document.getElementById('chat-box');
          const message = input.value.trim();
          if (!message) return;

          // Display user message
          chatBox.innerHTML += `<div class="message user">You: ${message}</div>`;
          input.value = "";

          // Send to FastAPI
          try {
            const res = await fetch("/ask", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ user_query: message })
            });
            const data = await res.json();
            const reply = data.response || data.detail || "Error fetching response";

            chatBox.innerHTML += `<div class="message assistant">🤖: ${reply}</div>`;
            chatBox.scrollTop = chatBox.scrollHeight;
          } catch (err) {
            chatBox.innerHTML += `<div class="message assistant">⚠️ Error: ${err.message}</div>`;
          }
        }
      </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


# Chat endpoint
@app.post("/ask")
def ask_question(request: QueryRequest):
    user_query = request.user_query.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        last_chats = fetch_last_5_chats()
        chat_context = ""
        for chat in last_chats:
            chat_context += f"User: {chat['user_message']}\nAssistant: {chat['ai_response']}\n"

        # Step 2: Build contextual input
        contextual_prompt = (
            f"Below is the chat history between the user and the assistant.\n"
            f"Use it as context to answer the next question naturally and accurately.\n\n"
            f"{chat_context}\n"
            f"Current User Query: {user_query}\n"
        )

        # Step 1: Get raw agent response
        response = agent.invoke({"input": contextual_prompt})
        raw_output = response.get("output", "")

        # Step 2: Synthesize and clean the final response
        system_prompt = (
                    "You are a helpful and detailed conversational assistant. I will provide you with a User Query and a Raw LLM Response. "
                    
                    # CORE INSTRUCTION: Synthesize and expand, do not just clean.
                    "Your task is to **fully synthesize a complete, detailed, and polite final response** that directly answers the User Query. "
                    "Use the Raw LLM Response as your primary source of fact, but **expand upon it** using clear, easy-to-understand language. "
                    
                    # Cleaning Instructions (combined and simplified)
                    "Your final output must be completely clean, meaning you must remove all internal agent tags, errors, conversational preambles, and any unwanted symbols like **, *, or #. "
                    
                    # Format Requirement
                    "The final response should be a complete sentence or paragraph, grammatically correct, and highly readable."

                    # "End your response by suggesting a natural follow-up question the user might ask — "
                    # "but phrase it casually, like ChatGPT would (e.g., 'Would you like me to explain how it works in detail?')."
                )

        full_prompt = f"User Query: {user_query}\n\nResponse: {raw_output}\n\n{system_prompt}"
        cleaned_output = llm.invoke(full_prompt).content

        store_chat(user_query, cleaned_output)

        return {
            "user_query": user_query,
            "response": cleaned_output,
            "status": "✅ saved to chat_history"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")
    
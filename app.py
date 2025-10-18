from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from services.llm_service import init_gemini_model
from services.db_service import fetch_last_5_chats, init_database, store_chat
from services.agent_service import create_agent
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
@app.get("/")
def home():
    return {"message": "Welcome to the Product Info Assistant API"}

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
    
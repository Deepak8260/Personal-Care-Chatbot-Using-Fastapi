from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from services.llm_service import init_gemini_model
from services.db_service import fetch_last_5_chats, init_database, store_chat
from services.agent_service import create_agent
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
# from langchain.schema import StrOutputParser

app = FastAPI(title="💬 Product Info Assistant API", version="1.0")

# Mount frontend folder
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

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
def serve_frontend():
    """Serve the chatbot HTML UI"""
    return FileResponse("frontend/index.html")



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
        # app.py - Modify the contextual_prompt for the agent
        contextual_prompt = (
            # --- FINAL, AGGRESSIVE SEARCH DIRECTIVE ---
            f"AGENT SYSTEM DIRECTIVE: You are an expert at partial product matching. "
            f"Your primary goal is to find the product record if the user provides ANY part of the name.\n"
            
            f"1. **TOLERANCE:** You **MUST** use the **ILIKE** operator instead of LIKE or = (ILIKE is case-insensitive, essential for PostgreSQL/Supabase). "
            f"2. **KEYWORDS:** Break the user's current query into **4 to 6** distinct, unique words (nouns, brands, key features). Ignore common words like 'of', 'me', 'give'. "
            f"3. **WILDACARDS & OR:** You **MUST** combine ALL extracted keywords using the **OR** operator, enclosing each keyword in '%' wildcards on both sides. "
            f"   This ensures success if **ANY SINGLE KEYWORD** is found in the product_name column.\n"
            f"   Example query logic: `... WHERE product_name ILIKE '%keyword1%' OR product_name ILIKE '%keyword2%' OR ...`\n\n"
            # ----------------------------------------
            
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
    
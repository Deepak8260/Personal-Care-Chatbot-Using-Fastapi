from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from services.llm_service import init_gemini_model
from services.db_service import init_database
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
        # Step 1: Get raw agent response
        response = agent.invoke({"input": user_query})
        raw_output = response.get("output", "")

        # Step 2: Synthesize and clean the final response
        system_prompt = (
            "You are a helpful and detailed conversational assistant. "
            "I will provide you with a User Query and a Raw LLM Response. "
            "Your task is to **fully synthesize a complete, detailed, and polite final response** "
            "that directly answers the User Query. "
            "Use the Raw LLM Response as your primary source of fact, but **expand upon it** "
            "using clear, easy-to-understand language. "
            "Your final output must be completely clean and grammatically correct."
        )

        full_prompt = f"User Query: {user_query}\n\nResponse: {raw_output}\n\n{system_prompt}"
        cleaned_output = llm.invoke(full_prompt).content

        return {
            "user_query": user_query,
            "response": cleaned_output
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")

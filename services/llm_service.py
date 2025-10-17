from langchain_google_genai import ChatGoogleGenerativeAI
from config.settings import GEMINI_API_KEY

def init_gemini_model():
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        api_key=GEMINI_API_KEY,
        temperature=0.0
    )
    return llm

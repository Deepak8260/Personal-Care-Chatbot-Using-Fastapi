# 💬 Personal Care Product Chatbot (FastAPI + Gemini + LangChain + Supabase)

An intelligent AI-based chatbot that helps users get product information, benefits, and support details for **personal care products** through natural conversations.

This project integrates **FastAPI**, **LangChain agents**, **Google Gemini**, **SQLAlchemy**, and **Supabase (PostgreSQL)** into one seamless pipeline — converting plain English questions into SQL queries, fetching structured data, and returning well-formatted AI responses.

---



| **Platform**  | **Description**                                                                                   | **Live URL**                                                                                                |
| ------------- | ------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| **Render**    | Complete deployment of the full application (both FastAPI backend and LangChain-powered logic).   | 🔗 [https://personal-care-chatbot-fastapi.onrender.com](https://personal-care-chatbot-using-fastapi.onrender.com/) |
| **Streamlit** | Full app deployment with integrated backend and chat UI, accessible directly via Streamlit Cloud. | 💬 [https://personal-care-chatbot.streamlit.app](https://personal-care-chatbot-new.streamlit.app/)               |




## 🚀 Core Tech Stack

| Category           | Tool / Library                                      | Purpose                                                |
| ------------------ | --------------------------------------------------- | ------------------------------------------------------ |
| 🧠 LLM             | **Gemini 2.5 Flash** (via `langchain-google-genai`) | Natural language understanding and response generation |
| 🔗 Agent Framework | **LangChain**                                       | Orchestrates the logic between LLM, SQL, and reasoning |
| 🗃️ Database ORM   | **SQLAlchemy**                                      | Executes SQL queries, manages chat history             |
| ☁️ Cloud DB        | **Supabase (PostgreSQL)**                           | Stores product details & chat history                  |
| ⚙️ Backend         | **FastAPI**                                         | Handles API endpoints, connects frontend and backend   |
| 🖥️ Frontend       | **HTML, CSS, JS**                                   | Chat interface for user interaction                    |
| 🔐 Config          | **dotenv**                                          | Stores API keys and database credentials securely      |
| 🐳 Deployment      | **Docker**                                          | Containerizes the whole app for easy deployment        |

---

## 🧩 Folder Structure

```
personal-care-chatbot/
│
├── app.py                     # FastAPI main app (entry point)
├── config/
│   └── settings.py            # Loads API keys and database URL
├── services/
│   ├── llm_service.py         # Initializes Gemini LLM
│   ├── db_service.py          # Connects to Supabase DB using SQLAlchemy
│   ├── agent_service.py       # Defines LangChain SQL Agent
│
├── frontend/
│   ├── index.html             # Chatbot UI
│   ├── style.css              # Modern UI design (glass effect)
│   └── script.js              # Handles message sending
│
├── requirements.txt           # Dependencies
├── .env                       # API keys & DB credentials
└── Dockerfile                 # For container deployment
```

---

## 🧠 Complete Workflow — Step-by-Step (Behind the Scenes)

Here’s how **each component interacts** when a user asks a question:

---

### 🧩 Step 1 — User Sends a Query (Frontend)

* The user types a message in `index.html`.
* `script.js` captures it and sends it to the backend endpoint:

  ```http
  POST /ask
  {
    "user_query": "What is the price of Dove soap?"
  }
  ```

---

### ⚙️ Step 2 — FastAPI Receives Request (`app.py`)

FastAPI (in `app.py`) does the following:

1. **Fetches last 5 chats** from Supabase using:

   ```python
   from services.db_service import fetch_last_5_chats
   ```

   These chats give *context* for a more natural conversation.

2. **Combines** the user’s query with the last 5 messages → builds a **contextual prompt**.

3. Sends this to the **LangChain SQL Agent** for intelligent query processing.

---

### 🤖 Step 3 — LangChain SQL Agent (`agent_service.py`)

The **LangChain Agent** acts as the **central brain**.

It receives the contextual prompt and decides:

* If the query is about **structured data** (price, availability, category):
  → it **creates an SQL query** using LangChain’s `create_sql_agent()`.

* If the query is **descriptive** (e.g., “Is Dove soap good for dry skin?”):
  → it switches to **reasoning mode**, skipping SQL and using **Gemini’s internal knowledge**.

* If the query involves **returns, defects, or complaints**:
  → it immediately responds with:

  ```
  "Final Answer: For immediate assistance with defective products or returns, please call +91-9999333943."
  ```

The logic and behavior of the agent are defined in a **custom system prompt** inside `agent_service.py`.

---

### 🧮 Step 4 — SQLAlchemy Executes the Query (`db_service.py`)

If the agent decides to query the database:

1. The agent uses the **LangChain SQL Toolkit** which internally uses **SQLAlchemy** to connect to the Supabase DB.

2. SQLAlchemy (through the connection string in `.env`) executes the generated SQL query:

   ```python
   engine = create_engine(SUPABASE_DB_URL)
   db = SQLDatabase(engine=engine)
   ```

3. The query results (product details, price, etc.) are returned back to the agent.

---

### 🧠 Step 5 — Gemini Refines the Response (`llm_service.py`)

After getting the raw response (either from SQL or reasoning), it is passed again to **Gemini** using:

```python
cleaned_output = llm.invoke(full_prompt).content
```

Here Gemini acts as a **refiner and rewriter** — it:

* Removes technical tags or artifacts.
* Expands the answer into **natural, human-like text**.
* Makes the reply conversational and polished.

---

### 💾 Step 6 — Chat History Storage (`db_service.py`)

The final response (both question and answer) is stored into the `chat_history` table using:

```python
store_chat(user_message, cleaned_output)
```

This enables context-based conversations (last 5 messages are reused each time).

---

### 💬 Step 7 — Response Sent to Frontend

Finally, FastAPI returns:

```json
{
  "user_query": "What is the price of Dove soap?",
  "response": "The price of Dove Soap is ₹299 for 100g.",
  "status": "✅ saved to chat_history"
}
```

And the frontend (`script.js`) displays it beautifully in the chat UI.

---

## 🧱 Component Contributions Summary

| Component             | Technology Used             | Role                                          |
| --------------------- | --------------------------- | --------------------------------------------- |
| **Frontend**          | HTML, CSS, JS               | User interaction, sending/receiving messages  |
| **Backend Framework** | FastAPI                     | API handling, connects all services           |
| **AI Model**          | Gemini 2.5 Flash            | Natural language understanding and generation |
| **LangChain**         | `create_sql_agent()`        | Converts user query → SQL → response          |
| **Database Layer**    | SQLAlchemy + Supabase       | Executes SQL and stores chat logs             |
| **Memory**            | Custom (chat_history table) | Contextual continuity across messages         |
| **Containerization**  | Docker                      | Portable and consistent deployment            |

---

## 🧾 Example Conversation Flow

| Step | Component       | Example Action                                                                              |
| ---- | --------------- | ------------------------------------------------------------------------------------------- |
| 1️⃣  | Frontend        | User types “Show me all shampoos under ₹500.”                                               |
| 2️⃣  | FastAPI         | Passes query to LangChain Agent                                                             |
| 3️⃣  | LangChain Agent | Converts to SQL → `SELECT * FROM product_details WHERE category='shampoo' AND price < 500;` |
| 4️⃣  | SQLAlchemy      | Executes SQL on Supabase                                                                    |
| 5️⃣  | Supabase        | Returns matching product records                                                            |
| 6️⃣  | Gemini          | Formats into: “Here are some shampoos under ₹500...”                                        |
| 7️⃣  | FastAPI         | Stores chat and sends response to frontend                                                  |
| 8️⃣  | Frontend        | Displays the AI response beautifully in the UI                                              |

---

## 🧠 System Architecture Diagram (Text-Based)

```
User ──▶ Frontend (HTML/JS)
          │
          ▼
      FastAPI (app.py)
          │
          ▼
   LangChain Agent (Text→SQL)
          │
      ┌───┴───┐
      ▼       ▼
  SQLAlchemy   Gemini LLM
   (Executes)  (Refines)
      │            │
      ▼            ▼
  Supabase DB   Final Response
      │            │
      └───────▶ Chat History
                   │
                   ▼
               Frontend UI
```

---

## 🧰 How to Run the Project Locally

```bash
# Clone
git clone https://github.com/yourusername/personal-care-chatbot.git
cd personal-care-chatbot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Add credentials
echo "GEMINI_API_KEY=your_api_key" >> .env
echo "SUPABASE_DB_URL=your_supabase_url" >> .env

# Run the app
uvicorn app:app --reload
```

Visit 👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 🐳 Running with Docker

You don’t need to build the image manually — it’s already available on **Docker Hub**.
Simply **pull** and **run** it using the following commands 👇

### 🧾 Step 1 — Pull the Image

```bash
docker pull kumar3472/personal-care-fastapi:latest
```

### 🧾 Step 2 — Run the Container

You’ll need to provide your credentials via the `--env` or `--env-file` option so that the container can access the Gemini API and Supabase database.

#### Option 1 — Using `.env` file

(Recommended if you already have a `.env` file in the same directory)

```bash
docker run -d -p 8000:8000 --env-file .env kumar3472/personal-care-fastapi:latest
```

#### Option 2 — Passing Environment Variables Directly

```bash
docker run -d -p 8000:8000 \
  -e GEMINI_API_KEY=your_api_key \
  -e SUPABASE_DB_URL=your_supabase_database_url \
  kumar3472/personal-care-fastapi:latest
```

Now open your browser at 👉 **[http://localhost:8000](http://localhost:8000)**
Your chatbot will be live and ready to use! 🚀

---

## 🔍 Example Queries

| Type            | Example Query                              | Agent Behavior                    |
| --------------- | ------------------------------------------ | --------------------------------- |
| 💰 Price Query  | “What’s the price of L’Oreal conditioner?” | Converts to SQL + fetches from DB |
| 💡 General Info | “Is Dove good for oily skin?”              | Uses reasoning via Gemini         |
| 📞 Support      | “My product is defective”                  | Triggers support message          |

---

## 🧑‍💻 Author

**👤 Deepak Kumar Mohanty**
🎓 BCA Graduate | 💻 Data Scientist & Python Developer
📍 Balasore, Odisha, India
---

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from bot.bot import ResumeJobMatchingBot  # Import the bot class
from models.schemas import GraphQueryInput  # Import request model
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Fetch environment variables
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Ensure all environment variables are set
if not all([NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, OPENAI_API_KEY, GROQ_API_KEY]):
    raise ValueError("❌ Missing environment variables in .env file!")

# ✅ Correctly initialize an instance of ResumeJobMatchingBot
bot = ResumeJobMatchingBot(
    neo4j_uri=NEO4J_URI,
    neo4j_username=NEO4J_USERNAME,
    neo4j_password=NEO4J_PASSWORD,
    openai_api_key=OPENAI_API_KEY,
    groq_api_key=GROQ_API_KEY
)

# ✅ Call `initialize_indexes` on the instance
bot.initialize_indexes()

# Initialize FastAPI app
app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Resume Job Matching API!"}

# 🚀 1️⃣ Find Candidates for a Job
@app.get("/match-candidates/")
async def match_candidates(job_title: str):
    return {"job_title": job_title, "matches": bot.advanced_candidate_matching(job_title)}

# 🚀 2️⃣ Job-Matching Chat
@app.get("/chat-response/")
async def chat_response(query: str, job_title: str = None):
    return {"query": query, "response": bot.chat_response(query, job_title)}

# 🚀 3️⃣ Retrieve Graph Data
@app.post("/retrieve-graph-info/")
async def retrieve_graph_info(data: GraphQueryInput):
    result = bot.retrieve_graph_info(data.query)
    return {"query": data.query, "cypher_query": result["cypher_query"], "results": result["results"]}
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_ollama import OllamaEmbeddings
from langchain_google_community.calendar.utils import (
    get_google_credentials, build_resource_service
)
import os
import pickle
from datetime import datetime, timedelta
from app.utils.logger import logger

FAISS_INDEX_PATH = "calendar_faiss_index"

def init_calendar_vectorstore():
    creds = get_google_credentials(
        token_file=os.getenv("GOOGLE_CALENDAR_TOKEN"),
        scopes=["https://www.googleapis.com/auth/calendar.readonly"],
        client_secrets_file=os.getenv("GOOGLE_CREDENTIALS")
    )
    service = build_resource_service(creds)

    time_min = (datetime.utcnow() - timedelta(days=365)).isoformat() + 'Z'
    time_max = (datetime.utcnow() + timedelta(days=3 * 365)).isoformat() + 'Z'

    events = service.events().list(
        calendarId='primary',
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute().get("items", [])

    texts = []
    for event in events:
        start = event.get("start", {}).get("dateTime", "")
        summary = event.get("summary", "")
        desc = event.get("description", "")
        loc = event.get("location", "")
        texts.append(f"{start}\n{summary}\n{desc}\n{loc}")

    llm_choice = os.getenv("LLM_CHOICE")
    embeddings = None
    match llm_choice:
        case "OLLAMA":
            embeddings = OllamaEmbeddings(model=os.getenv("EMBEDDING_LLM_MODEL"),base_url=os.getenv("OLLAMA_URL"))
        case "OPENAI":
            embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_texts(texts, embeddings)

    vectorstore.save_local(FAISS_INDEX_PATH)
    return vectorstore

def load_vectorstore():
    logger.debug("Loading vectorstore from %s", FAISS_INDEX_PATH)
    llm_choice = os.getenv("LLM_CHOICE")
    embeddings = None
    match llm_choice:
        case "OLLAMA":
            embeddings = OllamaEmbeddings(model=os.getenv("EMBEDDING_LLM_MODEL"), base_url=os.getenv("OLLAMA_URL"))
        case "OPENAI":
            embeddings = OpenAIEmbeddings()
    
    vectorestore = FAISS.load_local(
        folder_path=FAISS_INDEX_PATH,
        embeddings=embeddings,
        allow_dangerous_deserialization=True  # <- Explizit erlauben
    )
    logger.debug("Vectorstore loaded successfully.")
    return vectorestore

def get_similar_events(query: str, k: int = 100):
    vectorstore = load_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    return retriever.invoke(query)

def print_all_vectorstore_texts():
    vectorstore = load_vectorstore()
    results = vectorstore.similarity_search("", k=100)
    logger.debug("Printing all events in the vectorstore:\n")
    for i, doc in enumerate(results, 1):
        logger.debug("Event %s:\n%s\n", i, doc.page_content)
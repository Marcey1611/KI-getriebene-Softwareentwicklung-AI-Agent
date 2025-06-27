from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_ollama import OllamaEmbeddings
from langchain_google_community.calendar.utils import (
    get_google_credentials, build_resource_service
)
import os
import pickle
from datetime import datetime, timedelta

FAISS_INDEX_PATH = "calendar_faiss_index"

def init_calendar_vectorstore():
    creds = get_google_credentials(
        token_file=os.getenv("GOOGLE_CALENDAR_TOKEN"),
        scopes=["https://www.googleapis.com/auth/calendar.readonly"],
        client_secrets_file=os.getenv("GOOGLE_CREDENTIALS")
    )
    service = build_resource_service(creds)

    events = service.events().list(
        calendarId='primary',
        timeMin=datetime.utcnow().isoformat() + 'Z',
        timeMax=(datetime.utcnow() + timedelta(days=90)).isoformat() + 'Z',
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

    # Speichern
    vectorstore.save_local(FAISS_INDEX_PATH)

    return vectorstore

def load_vectorstore():
    llm_choice = os.getenv("LLM_CHOICE")
    embeddings = None
    match llm_choice:
        case "OLLAMA":
            embeddings = OllamaEmbeddings(model=os.getenv("EMBEDDING_LLM_MODEL"), base_url=os.getenv("OLLAMA_URL"))
        case "OPENAI":
            embeddings = OpenAIEmbeddings()
    return FAISS.load_local(
        folder_path=FAISS_INDEX_PATH,
        embeddings=embeddings,
        allow_dangerous_deserialization=True  # <- Explizit erlauben
    )

def get_similar_events(query: str, k: int = 3):
    vectorstore = load_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    return retriever.get_relevant_documents(query)
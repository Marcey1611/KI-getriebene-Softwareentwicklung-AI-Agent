import os
import time

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_google_community import GmailToolkit
from langchain_google_community.gmail.utils import (
    get_gmail_credentials,
    build_resource_service,
)

# 🔐 .env laden
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
openai_key = os.getenv("OPENAI_API_KEY")

# 🧠 LLM initialisieren
llm = ChatGroq(api_key=api_key, model="llama-3.3-70b-versatile")
#llm =  ChatOpenAI(api_key=openai_key,)

# 🛠️ Gmail Toolkit vorbereiten
credentials = get_gmail_credentials(
    token_file=os.getenv("GOOGLE_MAIL_TOKEN"),
    client_secrets_file=os.getenv("GOOGLE_CREDENTIALS"),
    scopes=["https://mail.google.com/"],
)
resource = build_resource_service(credentials=credentials)
toolkit = GmailToolkit(api_resource=resource)
gmail_tools = toolkit.get_tools()

from langchain_core.prompts import HumanMessagePromptTemplate, SystemMessagePromptTemplate, ChatPromptTemplate
from app.custom_calendar_tools.calendar_tool import cal_toolkit
tools = gmail_tools + cal_toolkit.get_tools()

system_prompt = SystemMessagePromptTemplate.from_template(
    "You are a helpful assistant that processes Gmail messages to extract calendar event details. The current date is {current_time}. The time information is for your internal context only. If an error occurs during processing, skip the rest of the message. Do not create or invent any emails, events, or content that is not explicitly present in the user's Gmail messages. However, you may be creative and flexible in interpreting how event details such as time, location, or title are expressed, as long as your interpretation is grounded in the actual message content."
)
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

# Define a chat model
model = ChatGroq(api_key=api_key, model="llama-3.1-8b-instant")
memory_exe = MemorySaver()
app = create_react_agent(
    model,
    tools=tools,
    checkpointer=memory_exe
)
retrieve_message_prompt = HumanMessagePromptTemplate.from_template(
    "You have received a Gmail message with the ID: {msg_id}.\n"
    "Use the tool `get_gmail_message` to retrieve the full text content of this email.\n"
    "Do not attempt to interpret or extract event details yet. Just retrieve the message."
)

analyze_message_prompt = HumanMessagePromptTemplate.from_template(
    "Determine whether this email contains information about a calendar event or meeting.\n"
    "If it does, extract the following fields:\n"
    "- title\n"
    "- start_datetime (in 'YYYY-MM-DD HH:MM:SS' format)\n"
    "- end_datetime (in 'YYYY-MM-DD HH:MM:SS' format; if not provided, estimate a reasonable end time)\n"
    "- timezone (default to 'Europe/Berlin')\n"
    "- attendees (list of email addresses; if an attendee's email is unknown, exclude them)\n"
    "- location (optional; include only if mentioned)\n"
    "- description\n\n"
    "Return the data as a valid JSON string using double quotes. Omit any fields that are not mentioned.\n"
    "If no meeting details are found, respond with:\n"
    "'No calendar entry found. No action taken.'"
)

create_event_prompt_template = HumanMessagePromptTemplate.from_template(
    "Now call the `create_calendar_event` tool with these values.\n"
    "Ensure that all datetime values use ISO 'YYYY-MM-DD HH:MM:SS' format, and attendees is a list of email strings."
)

def run_agent_executor(msg_id):
    from datetime import datetime
    now = datetime.now()
    config = {"configurable": {"thread_id": msg_id}}
    retrieve_prompt_template = ChatPromptTemplate.from_messages([
        system_prompt,
        retrieve_message_prompt
    ])

    retrieve_prompt =  retrieve_prompt_template.format_messages(current_time=now,msg_id=msg_id)
    retrieve_response = app.invoke(
        {"messages": retrieve_prompt},config=config,
    )
    email_content = retrieve_response["messages"][-1].content
    print(email_content)
    analyze_prompt = analyze_message_prompt.format_messages()
    analyze_response = app.invoke({"messages": analyze_prompt}, config=config)
    event_extraction = analyze_response["messages"][-1].content
    print(event_extraction)
    if "No calendar entry found" in event_extraction:
        print("ℹ️ Kein Termin erkannt. Keine Aktion nötig.")
        return
    create_event_prompt = create_event_prompt_template.format_messages()

    events = app.stream(
        {"messages": create_event_prompt},
        stream_mode="values",config=config
    )
    for event in events:
        event["messages"][-1].pretty_print()
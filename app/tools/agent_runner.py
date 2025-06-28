import os
from datetime import datetime
from multiprocessing import Process
from multiprocessing import Queue
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_google_community import GmailToolkit
from langchain_google_community.gmail.utils import (
    get_gmail_credentials,
    build_resource_service,
)
from langchain_core.prompts import ChatPromptTemplate
from app.tools.agent_prompts import system_prompt, retrieve_message_prompt,analyze_message_prompt,create_event_prompt_template, check_conflicts_prompt_template, add_event_to_vectorstore_prompt_template
from app.custom_calendar_tools.calendar_tool import cal_toolkit
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from app.rag.rag_calendar import init_calendar_vectorstore
from app.custom_calendar_tools.check_conflicts import check_conflicts
from app.custom_calendar_tools.add_event_to_vectorstore import add_event_to_vectorstore
from langchain.tools import Tool

credentials = get_gmail_credentials(
    token_file=os.getenv("GOOGLE_MAIL_TOKEN"),
    client_secrets_file=os.getenv("GOOGLE_CREDENTIALS"),
    scopes=["https://mail.google.com/"],
)

check_conflicts_tool = Tool(
    name="check_conflicts",
    func=check_conflicts,
    description="Prüft, ob zu dem angegebenen Zeitpunkt bereits ein Termin im Kalender existiert. "
)

add_event_to_vectorstore_tool = Tool(
    name="add_event_to_vectorstore",
    func=add_event_to_vectorstore,
    description="Speichert einen Kalender-Termin im Vektorstore. Erwartet ein JSON mit: summary, start_datetime, description, location."
)

class AgentRunner:
    def __init__(self):

        print("📥 Lade Kalender-Events in Vektor-Datenbank ...")
        init_calendar_vectorstore()
        print("✅ Kalender-Events als Vektoren gespeichert.")

        llm_choice = os.getenv("LLM_CHOICE")
        llm = None
        match llm_choice:
            case "OLLAMA":
                llm = ChatOllama(model=os.getenv("LLM_MODEL"),base_url=os.getenv("OLLAMA_URL"))
            case "OPENAI":
                llm = ChatOpenAI(model=os.getenv("LLM_MODEL"),api_key=os.getenv("OPENAI_API_KEY"))
        resource = build_resource_service(credentials=credentials)
        toolkit = GmailToolkit(api_resource=resource)
        gmail_tools = toolkit.get_tools()
        tools = gmail_tools + cal_toolkit.get_tools()
        tools.append(check_conflicts_tool)
        tools.append(add_event_to_vectorstore_tool)
        memory_exe = MemorySaver()
        self.app = create_react_agent(
            llm,
            tools=tools,
            checkpointer=memory_exe
        )

    def run_agent_executor(self,msg_id):
        now = datetime.now()
        config = {"configurable": {"thread_id": msg_id}}
        retrieve_prompt_template = ChatPromptTemplate.from_messages([
            system_prompt,
            retrieve_message_prompt
        ])

        retrieve_prompt =  retrieve_prompt_template.format_messages(current_time=now,msg_id=msg_id)
        retrieve_response = self.app.invoke(
            {"messages": retrieve_prompt},config=config,
        )
        email_content = retrieve_response["messages"][-1].content
        print(email_content)


        analyze_prompt = analyze_message_prompt.format_messages()
        analyze_response = self.app.invoke({"messages": analyze_prompt}, config=config)
        event_extraction = analyze_response["messages"][-1].content
        print(event_extraction)
        if "No calendar entry found" in event_extraction:
            print("There is no Event in the Mail.")
            return
        
        check_conflicts_prompt = check_conflicts_prompt_template.format_messages()
        check_conflicts_response = self.app.invoke({"messages": check_conflicts_prompt}, config=config)
        conflicts_check = check_conflicts_response["messages"][-1].content
        print(conflicts_check)
        if "Appointment period is already booked." in conflicts_check:
            print("Appointment period is already booked.")
            return

        create_event_prompt = create_event_prompt_template.format_messages()
        create_event_response = self.app.invoke({"messages": create_event_prompt}, config=config)
        event_creation = create_event_response["messages"][-1].content
        print(event_creation)

        add_event_to_vectorstore_prompt = add_event_to_vectorstore_prompt_template.format_messages()

        events = self.app.stream(
            {"messages": add_event_to_vectorstore_prompt},
            stream_mode="values",config=config
        )
        for event in events:
            event["messages"][-1].pretty_print()
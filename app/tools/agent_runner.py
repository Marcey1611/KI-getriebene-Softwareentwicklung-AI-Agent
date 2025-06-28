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
from app.rag.rag_calendar import init_calendar_vectorstore, print_all_vectorstore_texts
from app.custom_calendar_tools.check_conflicts import check_conflicts
from app.custom_calendar_tools.add_event_to_vectorstore import add_event_to_vectorstore
from langchain.tools import Tool
from app.utils.logger import logger

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

        logger.info("Loading calendar events to vectostore...")
        init_calendar_vectorstore()
        print_all_vectorstore_texts()
        logger.info("Stored alendar events successfully to vectorestore.")

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

        logger.debug("------------------------------ Retrieving email content ------------------------------")
        logger.info("Retrieving email content for message ID: %s", msg_id)
        retrieve_prompt =  retrieve_prompt_template.format_messages(current_time=now,msg_id=msg_id)
        retrieve_response = self.app.invoke({"messages": retrieve_prompt},config=config,)
        email_content = retrieve_response["messages"][-1].content
        logger.debug(f"Result retrieving email content: {email_content}")
        logger.info("Successfully retrieved email content. Continuing...\n\n\n")

        logger.debug("------------------------------ Analyzing email content ------------------------------")
        logger.info("Analyzing email content for message ID: %s", msg_id)
        analyze_prompt = analyze_message_prompt.format_messages()
        analyze_response = self.app.invoke({"messages": analyze_prompt}, config=config)
        event_extraction = analyze_response["messages"][-1].content
        logger.debug("Extracted email content: %s", event_extraction)
        if "No calendar entry found" in event_extraction:
            logger.info("There are no event details in the email. Halting processing for current email.")
            return
        logger.info("Successfully extracted event content from email. Continuing...\n\n\n")

        logger.debug("------------------------------ Conflicts check ------------------------------") 
        logger.info("Checking for conflicts in the calendar for message ID: %s", msg_id)
        check_conflicts_prompt = check_conflicts_prompt_template.format_messages()
        check_conflicts_response = self.app.invoke({"messages": check_conflicts_prompt}, config=config)
        conflicts_check = check_conflicts_response["messages"][-1].content
        logger.debug("Result conflicts check: %s", conflicts_check)
        if "Appointment period is already booked." in conflicts_check:
            logger.info("Appointment period is already booked. Halting processing for current email.")
            logger.info("Finisched process for current email.\n\n\n")
            return
        logger.info("Appointment period is available. Continuing...\n\n\n")

        logger.debug("------------------------------ Creating calendar event ------------------------------")
        logger.info("Creating calendar event for message ID: %s", msg_id)
        create_event_prompt = create_event_prompt_template.format_messages()
        create_event_response = self.app.invoke({"messages": create_event_prompt}, config=config)
        event_creation = create_event_response["messages"][-1].content
        logger.debug("Result event creation: %s", event_creation)
        logger.info("Event created successfully. Continuing...\n\n\n")

        logger.debug("------------------------------ Update vectorstore ------------------------------")
        logger.info("Adding event to vectorstore for message ID: %s", msg_id)
        add_event_to_vectorstore_prompt = add_event_to_vectorstore_prompt_template.format_messages()
        add_event_to_vectorstore_response = self.app.invoke({"messages": add_event_to_vectorstore_prompt}, config=config)
        add_event_to_vectorstore_result = add_event_to_vectorstore_response["messages"][-1].content
        logger.debug("Result adding event to vectorstore: %s", add_event_to_vectorstore_result)
        logger.info("Added event to vectorstore successfully.\n\n\n")

        logger.info("Finisched process for current email successfully.\n\n\n")
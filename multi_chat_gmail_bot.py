import uuid
import os

from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
from langchain_google_community import GmailToolkit
from langchain_google_community.gmail.utils import (
    get_gmail_credentials,
    build_resource_service,
)




load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
def main():
    credentials = get_gmail_credentials(
        token_file="../ai_agent_config/google-mail-token.json",
        client_secrets_file=os.getenv("GOOGLE_CREDENTIALS"),
        scopes=["https://mail.google.com/"],
    )
    resource = build_resource_service(credentials=credentials)

    toolkit = GmailToolkit(api_resource=resource)
    gmail_tools = toolkit.get_tools()
    memory = MemorySaver()
    model = ChatGroq(api_key=api_key, model="llama-3.3-70b-versatile")
    app = create_react_agent(
        model,
        tools=gmail_tools,
        checkpointer=memory,
    )

    # Erzeuge einen festen Thread ID für diese Session
    thread_id = uuid.uuid4()

    print("Starte Chat. Tippe 'exit' zum Beenden.")
    chat_list = []
    selected = str(thread_id)
    chat_list.append(selected)
    while True:
        user_input = input(f"Du {selected}: ")
        if user_input.lower() == "switch":
            print(f"Chats: {chat_list} // For new Chat type 'new_chat'")
            switch_input = input(f"Select chat:").lower()
            if switch_input == "new_chat":
                selected = str(uuid.uuid4())
                chat_list.append(selected)
            elif switch_input in chat_list:
                selected = switch_input
            else:
                print("Chat-ID nicht gefunden.")
        elif user_input.lower() == "exit":
            print("Chat beendet.")
            break
        else:
            input_message = HumanMessage(content=user_input)
            config = {"configurable": {"thread_id": selected}}
            # Streame die Antwort (du kannst auch non-streaming machen, falls dir das lieber ist)
            for event in app.stream({"messages": [input_message]}, config, stream_mode="values"):
                # Gib die letzte Nachricht des Events aus
                event["messages"][-1].pretty_print()


if __name__ == "__main__":
    main()

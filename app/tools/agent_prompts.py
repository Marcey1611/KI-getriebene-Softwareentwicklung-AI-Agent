from langchain_core.prompts import HumanMessagePromptTemplate, SystemMessagePromptTemplate, ChatPromptTemplate


system_prompt = SystemMessagePromptTemplate.from_template(
    "You are a helpful assistant that processes Gmail messages to extract calendar event details. The current date is {current_time}. The time information is for your internal context only. If an error occurs during processing, skip the rest of the message. Do not create or invent any emails, events, or content that is not explicitly present in the user's Gmail messages. However, you may be creative and flexible in interpreting how event details such as time, location, or title are expressed, as long as your interpretation is grounded in the actual message content."
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
    "- start_datetime (use the ISO8601DateTime)\n"
    "- end_datetime (use the ISO8601DateTime; if not provided, estimate a reasonable end time)\n"
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
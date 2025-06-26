
from app.mailing.gmail_pub_sub import GmailPubSub
from app.tools.agent_runner import AgentRunner
from dotenv import load_dotenv


def main():
    load_dotenv()
    agent = AgentRunner()
    gmail_pub_sub = GmailPubSub(agent=agent)
    gmail_pub_sub.run()


if __name__ == '__main__':
    main()
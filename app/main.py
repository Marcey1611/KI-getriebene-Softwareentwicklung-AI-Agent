
from app.mailing.gmail_pub_sub import GmailPubSub
from app.tools.agent_runner import AgentRunner
from dotenv import load_dotenv
from app.utils.logger import logger


def main():
    logger.debug("------------------------------ Initializing ------------------------------")
    logger.info("Starting initialization of AI Mail Agent...\n")
    load_dotenv()
    agent = AgentRunner()
    gmail_pub_sub = GmailPubSub(agent=agent)
    logger.info("Successfully initialized AI Mail Agent. Starting routine...\n\n\n")
    logger.debug("------------------------------ Waiting ------------------------------")
    gmail_pub_sub.run()


if __name__ == '__main__':
    main()
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.agent_runner import run_agent

if __name__ == "__main__":
    run_agent("19791fe26701e1c8")

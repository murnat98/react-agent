import asyncio
import argparse
from react_agent.agent import ReActAgent


async def main(query: str, verbosity: int):
    workflow = ReActAgent(verbose=False, timeout=None)
    answer = await workflow.run(query=query, verbosity_level=verbosity)
    print("Answer:", answer)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run ReActAgent with a custom query.")
    parser.add_argument("query", type=str, help="The query to run.")
    parser.add_argument(
        "--verbosity", "-v", type=int, default=1, help="Verbosity level (default: 1)"
    )
    args = parser.parse_args()

    asyncio.run(main(query=args.query, verbosity=args.verbosity))

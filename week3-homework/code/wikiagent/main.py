import sys
from typing import List
from wikiagent.wikipagent import SearchAndFetchAgent


import asyncio

async def run_demo(queries: List[str]) -> None:
    agent = SearchAndFetchAgent(top_k=3)

    for q in queries:
        resp = await agent.answer(q)
        print("Agent's answer:")
        print(resp.get("summary", "No answer returned."))


def main(argv: List[str] = None) -> None:
    argv = argv or sys.argv[1:]
    if not argv:
        queries = ["capybara"]
    else:
        queries = [" ".join(argv)]

    asyncio.run(run_demo(queries))


if __name__ == "__main__":
    main()
import sys
from typing import List
from wikiagent.wikipagent import SearchAndFetchAgent
from wikiagent._logging_ import AgentLogger


import asyncio

async def run_demo(queries: List[str], logger: AgentLogger) -> None:
    agent = SearchAndFetchAgent(top_k=3)

    for q in queries:
        print(f"\nUser query: {q}")
        logger.log_query(q)
        
        resp = await agent.answer(q)
        agent_result = resp.get("summary", "No answer returned.")
        
        # Convert AgentRunResult to string if needed
        if hasattr(agent_result, 'output'):
            answer = agent_result.output
        else:
            answer = str(agent_result)
        
        print("Agent's answer:")
        print(answer)
        logger.log_response(answer)


def main(argv: List[str] = None) -> None:
    argv = argv or sys.argv[1:]
    if not argv:
        queries = ["capybara"]
    else:
        queries = [" ".join(argv)]

    logger = AgentLogger()
    asyncio.run(run_demo(queries, logger))
    
    log_file = logger.save()
    print(f"\n✅ Logs saved to: {log_file}")


if __name__ == "__main__":
    main()
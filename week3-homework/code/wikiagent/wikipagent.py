from toyaikit.tools import wrap_instance_methods
from pydantic_ai import Agent
from wikiagent.tools import WikipediaTools, get_wikipedia_tools

class SearchAndFetchAgent:
    def __init__(self, top_k: int = 3, tools=None):
        self.top_k = top_k
        self.fetched_pages = []
        if tools is None:
            wiki_tools = get_wikipedia_tools()
            # Wrap the get_page method to track fetched pages
            original_get_page = wiki_tools.get_page
            def tracked_get_page(page_title):
                result = original_get_page(page_title)
                self.fetched_pages.append(page_title)
                return result
            wiki_tools.get_page = tracked_get_page
            tools = wrap_instance_methods(wiki_tools, ["search", "get_page"])
        self.tools = tools
        instructions = """
You are a Wikipedia agent with two tools: search and get_page.

When a user asks a question:
1. Use the search tool to find relevant Wikipedia pages for the topic.
2. After searching, use the get_page tool to fetch the raw content of the most relevant pages (at least 2 pages).
3. Read the page content and answer the user's question as clearly and directly as possible, using information from the pages.
4. ALWAYS include references at the end of your answer, listing the Wikipedia pages you used with their titles and links.

Important rules:
- Do NOT call `search` using a Wikipedia URL as the query.
- Only perform a search if the user provides a natural-language question or topic.
- After fetching pages, ALWAYS answer the user's question using the page content. Do not simply respond that the page has been indexed or that you are searching.
- Your output should be a direct answer to the user's question, followed by a References section listing all pages you fetched.
- Include Wikipedia links in the References section (format: Title - https://en.wikipedia.org/wiki/PageTitle).
"""
        self.agent = Agent(
            name="wikipedia_search_agent",
            instructions=instructions,
            tools=self.tools,
            model="openai:gpt-4o-mini"
        )

    async def answer(self, query: str) -> dict:
        self.fetched_pages.clear()
        response = await self.agent.run(
            user_prompt=query
        )
        return {
            "summary": response,
            "pages": self.fetched_pages
        }
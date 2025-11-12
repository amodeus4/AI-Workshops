import pytest
from wikiagent.wikipagent import SearchAndFetchAgent

@pytest.mark.asyncio
async def test_agent_provides_answer():
    """Test that the agent provides a meaningful answer to the query."""
    agent = SearchAndFetchAgent()
    result = await agent.answer("Where do capybaras live?")
    output = getattr(result["summary"], "output", str(result["summary"]))
    assert output, "Agent did not provide an answer"
    assert "South America" in output or "capybara" in output.lower(), "Agent answer does not contain expected information"

@pytest.mark.asyncio
async def test_agent_fetches_content():
    """Test that the agent fetches and uses page content in its answer."""
    agent = SearchAndFetchAgent()
    result = await agent.answer("Where do capybaras live?")
    output = getattr(result["summary"], "output", str(result["summary"]))
    # should provide detailed information 
    assert len(output) > 50, "Agent answer is too short, likely did not fetch page content"

@pytest.mark.asyncio
async def test_references_included_in_answer():
    """Test that the agent includes references in its answer."""
    agent = SearchAndFetchAgent()
    result = await agent.answer("Where do capybaras live? Please include references.")
    output = getattr(result["summary"], "output", str(result["summary"]))
  
    has_reference = "wikipedia" in output.lower() or "refer" in output.lower() or "http" in output.lower()
    assert has_reference, "References not included in the answer"
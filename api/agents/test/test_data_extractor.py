import asyncio
from api.agents.data_extractor_agent import DataExtractorAgent

async def main():
    agent = DataExtractorAgent()
    result = await agent.run(
        query="blockchain technology academic research",
        max_results=3,
        year_from=2020,
        year_to=2024,
        research_domain="Web3 and Blockchain Technology"
    )
    print(result)

if __name__ == "__main__":
    asyncio.run(main()) 
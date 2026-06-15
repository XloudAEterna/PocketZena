import asyncio
import httpx

POKEAPI_BASE_URL = "https://pokeapi.co/api/v2"

async def test_resolve_partial():
    query = "pika"
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{POKEAPI_BASE_URL}/pokemon?limit=2000")
        if response.status_code == 200:
            data = response.json()
            names = [r["name"] for r in data["results"]]
            matches = [n for n in names if n.startswith(query)]
            print(f"Matches for '{query}': {matches}")
            
            query2 = "char"
            matches2 = [n for n in names if n.startswith(query2)]
            print(f"Matches for '{query2}': {matches2[:5]}...")

if __name__ == "__main__":
    asyncio.run(test_resolve_partial())

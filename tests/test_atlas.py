import asyncio
import httpx
import json
from datetime import datetime

async def test_query():
    async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minute timeout
        try:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Sending query to Atlas...")
            response = await client.post(
                'http://localhost:8000/query',
                json={'content': 'What is a dimension?'}
            )
            
            print("\nStatus Code:", response.status_code)
            
            if response.status_code == 200:
                result = response.json()
                print("\nResponse:")
                print(json.dumps(result, indent=2))
            else:
                print("\nError Response:", response.text)
                
        except httpx.ReadTimeout:
            print("\nRequest timed out - this is expected while waiting for branch responses")
            print("Check the database for logged messages and processing metrics")
        except Exception as e:
            print(f"\nUnexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(test_query())
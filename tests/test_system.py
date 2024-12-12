import asyncio
import httpx
import json
from datetime import datetime

async def test_system_query():
    query = "What is history?"
    print(f"\n=== Testing System Response to: '{query}' ===")
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}\n")

    async with httpx.AsyncClient(timeout=300.0) as client:  # 5-minute timeout
        try:
            print("Sending query to Atlas...")
            response = await client.post(
                'http://localhost:8000/query',
                json={'content': query}
            )
            
            print(f"\nResponse Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                print("\n=== Initial Analysis ===")
                print(result.get('initial_analysis', 'Not provided'))
                
                print("\n=== Reflections ===")
                print(f"Number of reflections: {result.get('reflection_count', 0)}")
                
                print("\n=== Branch Responses ===")
                for branch, response in result.get('branch_responses', {}).items():
                    print(f"\n{branch.upper()} Response:")
                    print(response)
                
                print("\n=== Final Response ===")
                print(result.get('final_response', 'Not provided'))
                
                # Save complete response to file for detailed analysis
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"test_response_{timestamp}.json"
                with open(filename, 'w') as f:
                    json.dump(result, f, indent=2)
                print(f"\nComplete response saved to: {filename}")
                
            else:
                print("\nError Response:", response.text)
                
        except httpx.ReadTimeout:
            print("\nRequest timed out - this might be expected if branches are processing")
        except Exception as e:
            print(f"\nUnexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(test_system_query())
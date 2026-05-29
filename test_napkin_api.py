import httpx
import asyncio

async def test_napkin():
    api_key = 'sk-d8fa8b810464a3965f9562c4646761ce5717cd94a06e7d7c1d208c5cd6f690ed'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'format': 'svg',
        'content': 'Photosynthesis process and energy conversion'
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post('https://api.napkin.ai/v1/visual', json=payload, headers=headers)
        print(f'Status: {resp.status_code}')
        if resp.status_code == 201:
            data = resp.json()
            print(f'Success! Request ID: {data.get("id")}')
            print(f'Response: {data}')
        else:
            print(f'Error: {resp.text}')

asyncio.run(test_napkin())

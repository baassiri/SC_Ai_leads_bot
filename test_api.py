import requests

response = requests.get('http://127.0.0.1:5000/api/personas')
data = response.json()

print(f"Success: {data.get('success')}")
print(f"Total personas: {data.get('total')}")

if data.get('personas'):
    print("\nPersonas from API:")
    for p in data['personas']:
        print(f"  - {p['name']}: {p.get('message_tone', 'N/A')}")
else:
    print("\n❌ No personas returned from API!")
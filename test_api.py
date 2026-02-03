"""Quick test script for the chat API"""
import requests
import json

def test_chat():
    url = "http://localhost:8000/api/chat"
    data = {"message": "Namaste", "session_id": None}
    
    try:
        response = requests.post(url, json=data, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server. Make sure it's running on port 8000")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_chat()

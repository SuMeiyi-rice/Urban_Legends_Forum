import requests
import json

BASE_URL = 'http://127.0.0.1:5000/api'

def register():
    url = f"{BASE_URL}/register"
    data = {
        "username": "repro_user",
        "password": "password123",
        "email": "repro@example.com"
    }
    try:
        response = requests.post(url, json=data)
        if response.status_code == 201 or response.status_code == 400: # 400 if already exists
            print("Register: OK")
            return True
        else:
            print(f"Register Failed: {response.status_code} {response.text}")
            return False
    except Exception as e:
        print(f"Register Error: {e}")
        return False

def login():
    url = f"{BASE_URL}/login"
    data = {
        "username": "repro_user",
        "password": "password123"
    }
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print("Login: OK")
            return response.json()['token']
        else:
            print(f"Login Failed: {response.status_code} {response.text}")
            return None
    except Exception as e:
        print(f"Login Error: {e}")
        return None

def create_story(token):
    url = f"{BASE_URL}/stories"
    headers = {'Authorization': f'Bearer {token}'}
    data = {
        "title": "Test Story for Repro",
        "content": "This is a test story to reproduce the comment error.",
        "category": "urban_legend"
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 201:
            print("Create Story: OK")
            return response.json()['story']['id']
        else:
            print(f"Create Story Failed: {response.status_code} {response.text}")
            return None
    except Exception as e:
        print(f"Create Story Error: {e}")
        return None

def add_comment(token, story_id):
    url = f"{BASE_URL}/stories/{story_id}/comments"
    headers = {'Authorization': f'Bearer {token}'}
    data = {
        "content": "This is a test comment."
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 201:
            print("Add Comment: OK")
            print(response.json())
        else:
            print(f"Add Comment Failed: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Add Comment Error: {e}")

if __name__ == "__main__":
    if register():
        token = login()
        if token:
            story_id = create_story(token)
            if story_id:
                add_comment(token, story_id)

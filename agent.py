from dotenv import load_dotenv
load_dotenv()
from anthropic import Anthropic
import httpx

client = Anthropic()

BASE_URL = "http://localhost:8000"

messages = []


tools = [
    {
        "name": "get_task_status",
        "description": "查詢某個 task 目前的狀態。當使用者詢問特定 task 的狀態時呼叫。",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer", "description": "要查詢的 task 的 id"}
            },
            "required": ["task_id"]
        }
    }
]

def get_token():
    resp = httpx.post(
        f"{BASE_URL}/login",
        json={"username": "claude_test", "password": "123456"},
    )
    resp.raise_for_status()
    return resp.json()['token']


def get_task_status(task_id):
    try:
        token = get_token()
        resp = httpx.get(
            f"{BASE_URL}/tasks/{task_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
    except httpx.RequestError as e:
        return {"content": f"tools connection failed:{e}", "is_error": True}
    except httpx.HTTPStatusError as e:
        return {"content": f"tools authorization failed:{e}", "is_erroe": True}

    if resp.status_code == 200:
        task = resp.json()
        return {"content": f"task {task_id} status is {task['status']}", "is_error": False}
    if resp.status_code == 404:
        return {"content": f"task {task_id} not found", "is_error": False}
    return {"content": f"task {task_id} select error (HTTP {resp.status_code})", "is_error": True}

available_tools = {
    "get_task_status": get_task_status,
}
if __name__ == "__main__":
    while True:
        user_input = input("Enter message: ")
        if user_input == "q":
            break

        messages.append({"role": "user", "content": user_input})

        while True:
            resp = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=1024,
                messages=messages,
                tools=tools,
            )

            messages.append({"role": "assistant", "content": resp.content})

            for block in resp.content:
                if block.type == "text":
                        print("Claude:", block.text)
                if block.type == "tool_use":
                    try:
                        func = available_tools[block.name]
                        result = func(**block.input)
                    except (KeyError, TypeError) as e:
                        result = {"content": f"tools call failed:{e}", "is_error": True}

                    print("tool call:", block.name, block.input)
                    print("tool result:", result)

                    messages.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result['content'],
                            "is_error": result['is_error'],
                        }]
                    })

            if resp.stop_reason != "tool_use":
                break
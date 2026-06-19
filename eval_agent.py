import agent

results = []

def check(name, got, excepted):
    ok = (got == excepted)
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'} {name}: is_error={got} (預期 {excepted}) ")

check("task 1 存在 (200)", agent.get_task_status(1)['is_error'], False)
check("task 999 查無 (404)", agent.get_task_status(999)['is_error'], False)

real_url = agent.BASE_URL
agent.BASE_URL = "http://localhost:9999"
try:
    check("連線故障", agent.get_task_status(1)['is_error'], True)
finally:
    agent.BASE_URL = real_url

resp = agent.client.messages.create(
    model='claude-haiku-4-5',
    max_tokens=1024,
    messages=[{"role": "user", "content": "task 1 的狀態"}],
    tools=agent.tools,
)

tool_uses = [b for b in resp.content if b.type == "tool_use"]
ok = bool(tool_uses) and tool_uses[0].name == "get_task_status" and tool_uses[0].input == {"task_id": 1}
results.append(ok)
print(f"{'PASS' if ok else 'FAIL'}  工具選擇: 期望 get_task_status(task_id=1)，實得 "
      f"{[(b.name, b.input) for b in tool_uses]}")

print(f"\n{sum(results)}/{len(results)} passed")

def run_two_rounds(user_text):
    msgs = [{"role": "user", "content": user_text}]

    r1 = agent.client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        messages=msgs,
        tools=agent.tools,
    )
    msgs.append({"role": "assistant", "content": r1.content})

    for block in r1.content:
        if block.type == "tool_use":
            try:
                result = agent.available_tools[block.name](**block.input)
            except (KeyError, TypeError) as e:
                result = {"content": f"工具呼叫失敗:{e}", "is_error": True}
            msgs.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result["content"],
                    "is_error": result["is_error"],
                }]
            })

    r2 = agent.client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        messages=msgs,
        tools=agent.tools,
    )
    reply = "".join(b.text for b in r2.content if b.type == "text")
    return reply.lower()

real_url = agent.BASE_URL
agent.BASE_URL = "http://localhost:9999"

try:
    reply = run_two_rounds("task 1 的狀態")
finally:
    agent.BASE_URL = real_url

bad_words = ["todo", "in_progress", "done"]
ok = all(w not in reply for w in bad_words)and any(w in reply for w in ["連線", "稍後", "重試", "無法"])
results.append(ok)
print(f"{'PASS' if ok else 'FAIL'}  第三圈/故障不瞎掰: 回覆裡不該有狀態值，實得 reply={reply!r}")

reply = run_two_rounds("task 999 的狀態")
panic_words = ["錯誤", "error", "失敗", "異常"]
ok = all(w not in reply for w in panic_words)and any(w in reply for w in ["not found", "找不到", "不存在"])
results.append(ok)
print(f"{'PASS' if ok else 'FAIL'}  第三圈/查無不恐慌: 回覆不該講成災難，實得 reply={reply!r}")
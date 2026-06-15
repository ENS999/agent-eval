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
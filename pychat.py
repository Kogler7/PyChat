import os
import json
import datetime

from rich.console import Console
from rich.markdown import Markdown
console = Console()

system_role = "wiki"
total_tokens = 0
exit_flag = False
key_path = os.path.join(os.path.dirname(__file__), "wjy.key")


def read_key(path: str):
    with open(path, "r") as f:
        return f.read().strip()


def report(content: str, role: str = "openai", end='\n'):
    now = datetime.datetime.now().strftime("%H:%M:%S")
    color = "yellow"
    if role == "system":
        color = "green"
    elif role == "client":
        color = "blue"
    console.print(f"[bold {color}][{now}] @{role} > [/bold {color}] {content}", end=end)


def parse_command(content: str):
    command = content[1:]
    if command == "exit":
        global exit_flag
        exit_flag = True
        report("Exiting...", "system")
    elif command[:4] == "role":
        command = command[5:]
        if command == "":
            report("Set system role: ", "system", end="")
            system_role = input()
        else:
            system_role = command
        if system_role == "":
            system_role = "wiki"
        report("System role: " + system_role, "system")


def get_response(question: str, system_role: str = "wiki"):
    rsp = None
    with console.status("[bold green]Generating answer..."):
        rsp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_role},
                {"role": "user", "content": question}
            ]
        )
    res = json.dumps(rsp, indent=4, ensure_ascii=False)
    res = json.loads(res)
    choices = res["choices"]
    for (i, choice) in enumerate(choices):
        md = Markdown(choice["message"]["content"])
        report("[[italic]Response " + str(i) + "[/]]: ")
        console.print(md)
    used_tokens = res["usage"]["total_tokens"]
    global total_tokens
    total_tokens += used_tokens
    report(
        f"[italic]Tokens used/total: {used_tokens}/{total_tokens}[/]", "system")


report("Welcome to OpenAI Chatbot! Type '\\exit' to exit.", "system")

with console.status("[bold green]Loading openAI...") as status:
    import openai
    openai.api_key = read_key(key_path)


while True:
    if exit_flag:
        break
    report("", "client", end="")
    client_input = input()
    if client_input.startswith('\\'):
        parse_command(client_input)
    else:
        get_response(client_input, system_role)

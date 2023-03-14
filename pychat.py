import os
import json
import datetime

from rich.console import Console
from rich.markdown import Markdown

console = Console()

system_role = "wiki"
total_tokens = 0
exit_flag = False
key_path = None
log_path = None
in_context = False
assist_list = []


def read_key(path: str):
    with open(path, "r") as f:
        return f.read().strip()


def log_print(content: str, role: str, end: str = '\r\n'):
    if log_path is not None:
        now = datetime.datetime.now().strftime("%H:%M:%S")
        with open(log_path, 'a+') as f:
            f.write(f"[{now}] {role} > ")
            f.write(content)
            f.write(end)


def report(content: str, role: str = "openai", end='\n'):
    now = datetime.datetime.now().strftime("%H:%M:%S")
    color = "yellow"
    if role == "system":
        color = "green"
    elif role == "client":
        color = "blue"
    console.print(
        f"[bold {color}][{now}] @{role} > [/bold {color}] {content}", end=end)


def initialize():
    for dir, dirname, names in os.walk(os.path.dirname(__file__)):
        for name in names:
            if ".key" in name:
                global key_path
                key_path = os.path.join(dir, name)
                break

    if key_path is None:
        console.print("[bold red]No key file found![\]")
        exit(1)

    now = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    global log_path
    log_path = os.path.join(os.path.dirname(__file__), "log")
    if not os.path.exists(log_path):
        os.mkdir(log_path)
    log_path = os.path.join(log_path, now + ".log")

    report("[bold]Welcome to OpenAI Chatbot![/] Type '\\exit' to exit.", "system")

    with console.status("[bold green]Loading openAI..."):
        import openai
        openai.api_key = read_key(key_path)

    report(f"Using key file: [underline]{key_path}[/]", "system")
    report(
        f"Chat will be recorded in file: [underline]{log_path}[/]", "system")


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
    elif command[:7] == "context":
        command = command[8:]
        global in_context
        if "on" in command:
            in_context = True
            assist_list.clear()
        elif "off" in command:
            in_context = False
            assist_list.clear()
        report("Context mode: " + ("on" if in_context else "off"), "system")
    elif command[:4] == "help":
        report("Available commands:", "system")
        report("  \\role [role] - Set system role", "system")
        report("  \\exit - Exit the chatbot", "system")
        report("  \\context [on/off] - Turn on/off context mode", "system") 
    else:
        report("Invalid command", "system")


def get_response(question: str, system_role: str = "wiki"):
    rsp = None
    log_print(question, role="Client")
    with console.status("[bold green]Generating answer..."):
        import openai
        rsp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_role},
                {"role": "user", "content": question}
            ] + assist_list,
        )
    res = json.dumps(rsp, indent=4, ensure_ascii=False)
    res = json.loads(res)
    choices = res["choices"]
    for (i, choice) in enumerate(choices):
        content = choice["message"]["content"]
        report(f"[[italic]Response {i+1}/{len(choices)}[/]]: ")
        console.print(Markdown(content))
        log_print(content, role="OpenAI")
        if in_context:
            assist_list.append({"role": "assistant", "content": content})
    used_tokens = res["usage"]["total_tokens"]
    global total_tokens
    total_tokens += used_tokens
    report(
        f"[italic]Tokens used/total: {used_tokens}/{total_tokens}[/]", "system")


if __name__ == "__main__":
    initialize()

    while True:
        if exit_flag:
            break
        report("", "client", end="")
        client_input = input()
        if client_input.startswith('\\'):
            parse_command(client_input)
        else:
            get_response(client_input, system_role)

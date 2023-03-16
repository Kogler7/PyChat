import os
import json
import datetime

from rich.console import Console
from rich.markdown import Markdown

console = Console()

model = "gpt-3.5-turbo"
system_role = "assistant"
total_tokens = 0
exit_flag = False
key_path = None
log_path = None
with_context = False
context_locked = False
temperature = 0.5
max_tokens = 2000
assist_list = []
record_list = []


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
        f"[bold {color}][{now}] @{role} > [/bold {color}] {content}", end=end
    )


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

    date = datetime.datetime.now().strftime("%Y%m%d")
    now = datetime.datetime.now().strftime("%H%M%S")
    global log_path
    log_path = os.path.join(os.path.dirname(__file__), "log")
    log_path = os.path.join(log_path, date)
    if not os.path.exists(log_path):
        os.mkdir(log_path)
    log_path = os.path.join(log_path, now + ".log")

    report("[bold]Welcome to OpenAI Chatbot! Type '\\exit' to exit.", "system")
    report("Commands start with ‘\\’. Type '\\help' to see available commands.", "system")
    report(f"Using key file: [underline]{key_path}[/].", "system")
    report(
        f"Chat will be recorded in file: [underline]{log_path}[/].", "system"
    )

    with console.status("[bold green]Loading openAI..."):
        import openai
        openai.api_key = read_key(key_path)
    report(
        "[bold]Hello! I'm available now. How can I help you? "+
        "You can [yellow]type your question below[/].")


def parse_command(content: str):
    global system_role
    global temperature
    global max_tokens
    global with_context
    global context_locked
    command = content[1:]
    if command == "exit":
        global exit_flag
        exit_flag = True
        report("Exiting...", "system")
    if command[:4] == "mode":
        # print all settings
        report("Current settings:", "system")
        report(f"    Model:             {model}", "system")
        report(f"    System role:       {system_role}", "system")
        report(f"    Temperature:       {temperature}", "system")
        report(f"    Max tokens:        {max_tokens}", "system")
        report(
            f"    Context mode:      {'on' if with_context else 'off'}", "system")
        report(f"    Context locked:    {context_locked}", "system")
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
    elif command[:4] == "temp":
        command = command[5:]
        if command == "":
            report("Set temperature: ", "system", end="")
            temperature = float(input())
        else:
            temperature = float(command)
        report("Temperature: " + str(temperature), "system")
    elif command[:3] == "max":
        command = command[4:]
        if command == "":
            report("Set max tokens: ", "system", end="")
            max_tokens = int(input())
        else:
            max_tokens = int(command)
        report("Max tokens: " + str(max_tokens), "system")
    elif command[:3] == "ctx":
        command = command[4:]
        if "on" in command:
            with_context = True
        elif "new" in command:
            with_context = True
            assist_list.clear()
        elif "off" in command:
            with_context = False
        elif "lock" in command:
            context_locked = True
        elif "unlock" in command:
            context_locked = False
        # ctx save/load
        report("Context mode: " + ("on" if with_context else "off"), "system")
    elif command[:3] == "rcd":
        command = command[4:]
        # rcd save/load
        pass
    elif command[:4] == "with":
        # with context
        command = command[5:]
        index = command.strip().split(' ')[0]
        question = command[len(index):].strip()
        if "ctx" in index:
            report("Assist with context ...", "system")
            get_response(question, assist=assist_list)
        if "last" in index:
            index = -1
        else:
            index = int(index)
        try:
            record = record_list[index]
            report(f"Assist with record {index} ...", "system")
            get_response(question, assist=record)
        except Exception as e:
            report("[red bold]Error: [/]" + str(e), "system")
    elif command[:4] == "help":
        report("Available commands:", "system")
        report("    \\exit  - Exit the chatbot", "system")
        report("    \\mode  - Show current settings", "system")
        report("    \\role \[role desc]         - Set system role", "system")
        report("    \\temp \[temperature]       - Set temperature", "system")
        report(
            "    \\with \[index] \[question]  - Assist with a record", "system")
        report("    \\max  \[max_tokens]        - Set max tokens", "system")
        report(
            "    \\ctx  \[on/off/new]        - Turn on/off context mode", "system")
    else:
        report("Invalid command", "system")


def get_response(question: str, role: str = None, assist=None):
    try:
        rsp = None
        start_time = datetime.datetime.now()
        log_print(question, role="Client")
        messages = [
            {"role": "system", "content": role if role is not None else system_role}]
        if assist is not None:
            messages += assist
        elif with_context:
            messages += assist_list
        messages += [{"role": "user", "content": question}]
        with console.status("[bold green]Generating answer..."):
            import openai
            rsp = openai.ChatCompletion.create(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                messages=messages,
            )
        response = json.loads(json.dumps(rsp, indent=4, ensure_ascii=False))
        choices = response["choices"]
        time_elapsed = datetime.datetime.now() - start_time
        time_elapsed = int(time_elapsed.total_seconds())
        content = choices[0]["message"]["content"]
        report(
            f"[bold]Record <{len(record_list)}>[/]: ")
        console.print(Markdown(content))
        log_print(content, role="OpenAI")
        record_list.append([
            {"role": "user", "content": question},
            {"role": "assistant", "content": content}
        ])
        if with_context and not context_locked:
            assist_list.append({"role": "user", "content": question})
            assist_list.append({"role": "assistant", "content": content})
        used_tokens = response["usage"]["total_tokens"]
        global total_tokens
        total_tokens += used_tokens
        report(
            f"[bold]Tokens used/total: {used_tokens}/{total_tokens}, " +
            f"Time used: [green]{time_elapsed}s[/].",
            "system"
        )
    except Exception as e:
        report("[red bold]Error: [/]" + str(e), "system")
        log_print(str(e), role="Error")


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

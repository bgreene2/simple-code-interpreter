import ollama
import os
import re
import subprocess
import time

# Set parameters
# ----------
ollama_client_url = 'http://localhost:11434'
model = 'mixtral'
# ----------

system_prompt = f"""
You are {model}, a large language model.

# Tools

## python

When you send a message containing Python code to python, it will be executed in a temporary Python process. State does not persist between invocations.

* Example: <execute-tool name="python" input="{{input}}" output="{{output}}", errors="{{errors}}", timedOut="{{timedOut}}">
** Your commands to be executed go into the "input" field. Remember to print the results to stdout. The stdout from the tool will then be inserted into the "output" field. The stderr from the tool will be inserted into the "errors" field. The "timedOut" field flags whether the execution timed out.
"""

python_pattern = r'<execute-tool name="python" input="((?:[^"\\]|\\.)*)"'

def main():
    # point at ollama server
    client = ollama.Client(host=ollama_client_url)

    # keep track of message history -- NOTE: there is no max size
    messages = []

    # append system prompt
    messages.append({'role':'system','content':system_prompt})

    # the user should normally have the next turn, unless python tool was just used, in which case the assistant gets a chance to react to the tool's output
    user_message_next = True

    # loop until ctrl-c
    while True:
        print()
        if user_message_next:
            # read user's input
            user_input = input('User: ')

            # append user's input to the message history
            messages.append({'role':'user','content':user_input})

        print('Assistant:', end='', flush=True)
        
        # it's the assitant's turn. Capture its output in this string
        string = ''

        # the assistant's output will stream chunk by chunk
        # example chunk: {'model': 'mixtral:latest', 'created_at': '2024-02-24T18:18:02.287801Z', 'message': {'role': 'assistant', 'content': ' <'}
        user_message_next = True
        for chunk in client.chat(model=model, messages=messages, stream=True):
            piece = chunk['message']['content']
            # print each chunk
            print(piece, end='', flush=True)

            # append to the running string
            string = string + piece

            # if the assitant is invoking the python tool, read what it's put in to the 'input' field, and call a subprocess and insert the output into the 'output' field
            # NOTE: this assumes that each chunk is one token. It doesn't take into account any text that may be present after the python_pattern, if any
            python_match = re.search(python_pattern, string)
            if python_match:
                captured_input = python_match.group(1)
                captured_input = format_input(captured_input)
                print(f"\nPython Input: {captured_input}", flush=True)
                
                # prompt the user to allow the command to be executed
                input('Execute command? Ctrl-C to cancel.')

                print('Python Output: ', end='', flush=True)

                timed_out, output, errors = execute_python(captured_input)
                if timed_out:
                    print("Execution timed out.")
                print(f"Stdout: {output}")
                print(f"Stderr: {errors}", flush=True)

                output = escape_double_quotes(output)
                errors = escape_double_quotes(errors)

                string = f"{string} output=\"{output}\" errors=\"{errors}\" timedOut=\"{timed_out}\">\n"

                # interrupt the assistant's generation, discard everything after the tool invocation, and start again in a new turn
                user_message_next = False
                break

        messages.append({'role':'assistant','content':string})


def escape_double_quotes(text):
  return text.replace('"', '\\"')

def format_input(text):
    return text.replace('\\n', '\n')

def execute_python(command, timeout=60):
    proc = subprocess.Popen(['python'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    try:
        outs, errs = proc.communicate(input=command, timeout=timeout)
        return False, outs, errs
    except TimeoutExpired:
        proc.kill()
        outs, errs = proc.communicate()
        return True, outs, errs


if __name__ == '__main__':
    main()


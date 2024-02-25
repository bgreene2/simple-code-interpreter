# Simple code interpreter

This is a simple demonstration of an LLM using a code interpreter tool.

It is intended to be the bare minimum necessary to get the concept to work.

It takes no arguments, and all configurable params are hardcoded at the top of the script.

It does no validation.

## How it works

The LLM streams its output.

When the program detects that the LLM is invoking the tool, the program halts the LLM's generation, runs the LLM's command in a subprocess, and writes the output of that command into the LLM's context.

Then, the program gives the LLM another conversation turn to react to the output.

## Tool syntax

I asked Mixtral what would be a good syntax to use for an LLM invoking a code interpreter tool, and it came up with this structure, so it's what I implemented.

When the LLM emits `<execute-tool name="python" input="..."`, the tool is invoked with the given input.

Then the rest of the 'execute-tool' tag is filled in with ` output="{output}", errors="{errors}", timedOut="{timedOut}">`.

When all is said in done, the LLM's context will contain `<execute-tool name="python" input="{input}" output="{output}", errors="{errors}", timedOut="{timedOut}">`.

## Requirements

* You need Python on your system.
* You need access to an Ollama API.
* That Ollama API needs to serve mixtral.

## Quickstart

1. Install ollama on your system (https://ollama.com)
2. Pull mixtral: `ollama pull mixtral`
3. Install requirments: `pip install -r requirements.txt`
4. Run program: `python main.py`

To run mixtral on your computer, you need about 32GB of memory.

You can edit the script to use a smaller LLM, but mixtral is the smallest one I've found so far that uses tools out of the box.

## Example chatlog

```
User: What is the sin of 2 to the 4th?
Assistant: <execute-tool name="python" input="import math; print(math.sin(2**4))"
Python Input: import math; print(math.sin(2**4))
Execute command? Ctrl-C to cancel.
Python Output: Stdout: -0.2879033166650653

Stderr:

Assistant:
The sin of 2 to the power of 4 is approximately -0.2879.
```
In this case, this is what the LLM sees once the tools is invoked:

`<execute-tool name="python" input="import math; print(math.sin(2**4))" output="-0.2879033166650653", errors="", timedOut="False">`


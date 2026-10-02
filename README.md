# Tool-Using Assistant (Python)

A small command-line assistant that **chooses a tool** for each request, runs it, and prints which tool it used. It is rule-based (no API key, no network) so the agent loop is easy to read: observe -> choose tool -> act -> respond.

## Tools
- **calculate**: safe math (parses the expression with `ast`; never calls `eval`)
- **convert**: km/miles, kg/lb, C/F
- **notes**: save and search notes, stored in `notes.json`
- 10 automated tests

## Run
Needs Python 3.9+.
```
python agent.py
you> what is 12*(3+4)
you> 100 c to f
you> note: study DSA
you> find notes dsa
python -m unittest -v
```

## Design notes
- `Agent.choose_tool` is the decision step. Replacing it with an LLM call that returns a tool name and arguments is the natural upgrade, and the tools stay unchanged.
- Tool errors are caught and reported instead of crashing the loop.

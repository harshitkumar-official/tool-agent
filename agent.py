"""A tiny tool-using assistant: it reads a request, picks a tool, runs it, and shows its steps.

The router is rule-based on purpose (no API keys, no network), so you can see exactly how an
agent loop works: observe request -> choose tool -> act -> respond. Swapping `choose_tool`
for an LLM call is the natural next step.
"""
import ast
import json
import operator
import re
from pathlib import Path

# ---------- Tool 1: calculator (safe: parses the expression, never uses eval) ----------
_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.USub: operator.neg,
}


def calculate(expression):
    def ev(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](ev(node.operand))
        raise ValueError("unsupported expression")

    result = ev(ast.parse(expression.strip(), mode="eval").body)
    return str(int(result)) if float(result).is_integer() else f"{result:.4f}".rstrip("0")


# ---------- Tool 2: unit converter ----------
_CONVERSIONS = {
    ("km", "miles"): lambda v: v * 0.621371,
    ("miles", "km"): lambda v: v / 0.621371,
    ("kg", "lb"): lambda v: v * 2.20462,
    ("lb", "kg"): lambda v: v / 2.20462,
    ("c", "f"): lambda v: v * 9 / 5 + 32,
    ("f", "c"): lambda v: (v - 32) * 5 / 9,
}


def convert(value, src, dst):
    fn = _CONVERSIONS.get((src.lower(), dst.lower()))
    if fn is None:
        raise ValueError(f"cannot convert {src} to {dst}")
    return f"{fn(value):.2f} {dst}"


# ---------- Tool 3: notes (saved to a JSON file) ----------
class Notes:
    def __init__(self, path="notes.json"):
        self.path = Path(path)
        self.items = json.loads(self.path.read_text()) if self.path.exists() else []

    def add(self, text):
        self.items.append(text)
        self.path.write_text(json.dumps(self.items))
        return f"Saved note #{len(self.items)}"

    def search(self, word):
        hits = [f"#{i + 1}: {t}" for i, t in enumerate(self.items) if word.lower() in t.lower()]
        return "\n".join(hits) if hits else "No matching notes."


# ---------- The agent ----------
class Agent:
    def __init__(self, notes_path="notes.json"):
        self.notes = Notes(notes_path)
        self.trace = []  # which tool ran for each request, for debugging/learning

    def choose_tool(self, text):
        """Return (tool_name, args). This is the 'decision' step."""
        t = text.strip()
        m = re.match(r"(?:convert\s+)?(-?\d+(?:\.\d+)?)\s*(km|miles|kg|lb|c|f)\s+(?:to|in)\s+(km|miles|kg|lb|c|f)$", t, re.I)
        if m:
            return "convert", (float(m.group(1)), m.group(2), m.group(3))
        m = re.match(r"(?:note|remember)[:\s]+(.+)", t, re.I)
        if m:
            return "notes.add", (m.group(1),)
        m = re.match(r"(?:find|search)\s+notes?\s+(?:for\s+)?(.+)", t, re.I)
        if m:
            return "notes.search", (m.group(1),)
        m = re.match(r"(?:calc(?:ulate)?|what is|what's)?\s*([\d\s+\-*/().%^]+)\??$", t, re.I)
        if m and re.search(r"\d", m.group(1)):
            return "calculate", (m.group(1).replace("^", "**"),)
        return "none", ()

    def handle(self, text):
        tool, args = self.choose_tool(text)
        self.trace.append(tool)
        try:
            if tool == "convert":
                return convert(*args)
            if tool == "notes.add":
                return self.notes.add(*args)
            if tool == "notes.search":
                return self.notes.search(*args)
            if tool == "calculate":
                return calculate(*args)
        except (ValueError, SyntaxError, ZeroDivisionError) as err:
            return f"Tool '{tool}' failed: {err}"
        return "I can calculate, convert units (km/miles, kg/lb, C/F) and keep notes. Try: 12*(3+4)"


def main():
    agent = Agent()
    print("Assistant ready. Type a request, or 'quit'.")
    while True:
        try:
            text = input("you> ")
        except EOFError:
            break
        if text.strip().lower() == "quit":
            break
        print("bot>", agent.handle(text), f"  [tool: {agent.trace[-1]}]")


if __name__ == "__main__":
    main()

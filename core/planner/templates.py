"""Code Templates for Scaffolding Functional Applications in KritiAI."""

CALCULATOR_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Modern Calculator — Created by KritiAI</title>
  <style>
    :root {
      --bg-color: #0b0f19;
      --card-bg: rgba(22, 30, 49, 0.85);
      --card-border: rgba(255, 255, 255, 0.08);
      --btn-num: #1e293b;
      --btn-op: #3b82f6;
      --btn-func: #334155;
      --btn-equal: #10b981;
      --text: #f8fafc;
      --text-muted: #94a3b8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body {
      background: radial-gradient(circle at top, #1e293b 0%, var(--bg-color) 100%);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      color: var(--text);
    }
    .calculator {
      background: var(--card-bg);
      backdrop-filter: blur(20px);
      border: 1px solid var(--card-border);
      border-radius: 20px;
      padding: 24px;
      width: 340px;
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
    }
    .header {
      font-size: 13px;
      color: var(--text-muted);
      margin-bottom: 12px;
      display: flex;
      justify-content: space-between;
    }
    .display {
      background: rgba(15, 23, 42, 0.6);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 16px;
      margin-bottom: 20px;
      text-align: right;
    }
    .history {
      font-size: 13px;
      color: var(--text-muted);
      min-height: 18px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .current {
      font-size: 32px;
      font-weight: 600;
      color: var(--text);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .buttons {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 10px;
    }
    button {
      background: var(--btn-num);
      border: 1px solid var(--card-border);
      color: var(--text);
      font-size: 18px;
      font-weight: 500;
      height: 56px;
      border-radius: 12px;
      cursor: pointer;
      transition: all 0.15s ease;
      user-select: none;
    }
    button:hover {
      filter: brightness(1.2);
      transform: translateY(-2px);
    }
    button:active {
      transform: translateY(0);
    }
    button.op { background: var(--btn-op); font-weight: 600; }
    button.func { background: var(--btn-func); }
    button.equal { background: var(--btn-equal); grid-column: span 2; font-weight: 700; }
    .footer {
      margin-top: 16px;
      font-size: 11px;
      color: var(--text-muted);
      text-align: center;
    }
  </style>
</head>
<body>
  <div class="calculator">
    <div class="header">
      <span>KritiAI Calculator</span>
      <span>v1.0</span>
    </div>
    <div class="display">
      <div id="history" class="history"></div>
      <div id="current" class="current">0</div>
    </div>
    <div class="buttons">
      <button class="func" onclick="clearAll()">AC</button>
      <button class="func" onclick="deleteLast()">DEL</button>
      <button class="func" onclick="appendOp('%')">%</button>
      <button class="op" onclick="appendOp('/')">÷</button>

      <button onclick="appendNum('7')">7</button>
      <button onclick="appendNum('8')">8</button>
      <button onclick="appendNum('9')">9</button>
      <button class="op" onclick="appendOp('*')">×</button>

      <button onclick="appendNum('4')">4</button>
      <button onclick="appendNum('5')">5</button>
      <button onclick="appendNum('6')">6</button>
      <button class="op" onclick="appendOp('-')">−</button>

      <button onclick="appendNum('1')">1</button>
      <button onclick="appendNum('2')">2</button>
      <button onclick="appendNum('3')">3</button>
      <button class="op" onclick="appendOp('+')">+</button>

      <button onclick="appendNum('0')">0</button>
      <button onclick="appendNum('.')">.</button>
      <button class="equal" onclick="calculate()">=</button>
    </div>
    <div class="footer">Created automatically by KritiAI Execution Layer</div>
  </div>

  <script>
    let currentInput = "0";
    let equation = "";

    const displayCurrent = document.getElementById("current");
    const displayHistory = document.getElementById("history");

    function updateDisplay() {
      displayCurrent.innerText = currentInput;
      displayHistory.innerText = equation;
    }

    function appendNum(num) {
      if (currentInput === "0" && num !== ".") {
        currentInput = num;
      } else if (num === "." && currentInput.includes(".")) {
        return;
      } else {
        currentInput += num;
      }
      updateDisplay();
    }

    function appendOp(op) {
      if (currentInput === "" && equation !== "") {
        equation = equation.slice(0, -1) + op;
      } else {
        equation += (currentInput + " " + op + " ");
        currentInput = "";
      }
      updateDisplay();
    }

    function calculate() {
      if (!currentInput && !equation) return;
      let fullExpr = equation + currentInput;
      try {
        let cleanExpr = fullExpr.replace(/×/g, "*").replace(/÷/g, "/").replace(/−/g, "-");
        // Safe evaluation
        let result = Function('"use strict"; return (' + cleanExpr + ')')();
        displayHistory.innerText = fullExpr + " =";
        currentInput = String(Number(result.toFixed(8)));
        equation = "";
        displayCurrent.innerText = currentInput;
      } catch (e) {
        displayCurrent.innerText = "Error";
        currentInput = "";
        equation = "";
      }
    }

    function clearAll() {
      currentInput = "0";
      equation = "";
      updateDisplay();
    }

    function deleteLast() {
      if (currentInput.length > 1) {
        currentInput = currentInput.slice(0, -1);
      } else {
        currentInput = "0";
      }
      updateDisplay();
    }

    // Keyboard support
    window.addEventListener("keydown", (e) => {
      if ((e.key >= '0' && e.key <= '9') || e.key === '.') appendNum(e.key);
      else if (e.key === '+' || e.key === '-' || e.key === '*' || e.key === '/' || e.key === '%') appendOp(e.key);
      else if (e.key === 'Enter' || e.key === '=') calculate();
      else if (e.key === 'Backspace') deleteLast();
      else if (e.key === 'Escape') clearAll();
    });
  </script>
</body>
</html>
"""

CALCULATOR_PY = '''"""Modern Desktop GUI Calculator created by KritiAI."""
import tkinter as tk
from tkinter import ttk

class CalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("KritiAI Desktop Calculator")
        self.root.geometry("320x420")
        self.root.resizable(False, False)
        self.root.configure(bg="#0f172a")

        self.expression = ""

        # Display Entry
        self.display_var = tk.StringVar(value="0")
        display = tk.Entry(
            root,
            textvariable=self.display_var,
            font=("Segoe UI", 24, "bold"),
            bg="#1e293b",
            fg="#f8fafc",
            bd=0,
            justify="right",
            insertbackground="#f8fafc"
        )
        display.pack(fill="x", padx=16, pady=(20, 10), ipady=12)

        # Buttons Grid
        btn_frame = tk.Frame(root, bg="#0f172a")
        btn_frame.pack(fill="both", expand=True, padx=16, pady=10)

        buttons = [
            ('C', 0, 0, '#ef4444'), ('DEL', 0, 1, '#475569'), ('%', 0, 2, '#3b82f6'), ('/', 0, 3, '#3b82f6'),
            ('7', 1, 0, '#334155'), ('8', 1, 1, '#334155'), ('9', 1, 2, '#334155'), ('*', 1, 3, '#3b82f6'),
            ('4', 2, 0, '#334155'), ('5', 2, 1, '#334155'), ('6', 2, 2, '#334155'), ('-', 2, 3, '#3b82f6'),
            ('1', 3, 0, '#334155'), ('2', 3, 1, '#334155'), ('3', 3, 2, '#334155'), ('+', 3, 3, '#3b82f6'),
            ('0', 4, 0, '#334155'), ('.', 4, 1, '#334155'), ('=', 4, 2, '#10b981')
        ]

        for text, r, c, bg_color in buttons:
            colspan = 2 if text == '=' else 1
            btn = tk.Button(
                btn_frame,
                text=text,
                font=("Segoe UI", 14, "bold"),
                bg=bg_color,
                fg="#ffffff",
                activebackground="#60a5fa",
                activeforeground="#ffffff",
                bd=0,
                cursor="hand2",
                command=lambda t=text: self.on_button_click(t)
            )
            btn.grid(row=r, column=c, columnspan=colspan, sticky="nsew", padx=4, pady=4)

        for i in range(5):
            btn_frame.rowconfigure(i, weight=1)
        for i in range(4):
            btn_frame.columnconfigure(i, weight=1)

        # Bind keyboard
        root.bind('<Key>', self.on_key)

    def on_button_click(self, char):
        if char == 'C':
            self.expression = ""
            self.display_var.set("0")
        elif char == 'DEL':
            self.expression = self.expression[:-1]
            self.display_var.set(self.expression if self.expression else "0")
        elif char == '=':
            try:
                result = str(eval(self.expression))
                self.display_var.set(result)
                self.expression = result
            except Exception:
                self.display_var.set("Error")
                self.expression = ""
        else:
            self.expression += str(char)
            self.display_var.set(self.expression)

    def on_key(self, event):
        if event.char in '0123456789+-*/.':
            self.on_button_click(event.char)
        elif event.keysym in ('Return', 'KP_Enter'):
            self.on_button_click('=')
        elif event.keysym == 'BackSpace':
            self.on_button_click('DEL')
        elif event.keysym == 'Escape':
            self.on_button_click('C')

if __name__ == "__main__":
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()
'''

CALCULATOR_BAT = """@echo off
echo Launching KritiAI Calculator...
start "" "%~dp0calculator.html"
exit
"""

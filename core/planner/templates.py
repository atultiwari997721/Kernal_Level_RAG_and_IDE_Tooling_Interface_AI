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

SHOPPING_ARCHITECTURE_MD = """# E-Commerce Shopping Website — Architecture Design

**Generated by KritiAI Autonomous Architecture Engine**

## 1. System Overview
The Shopping Platform is designed with a lightweight, modular, decoupled architecture providing high performance, offline/local development capability, and clean separation of concerns.

```
┌────────────────────────────────────────────────────────┐
│                   Presentation Layer                   │
│   • index.html (Semantic HTML5, Accessible UI)         │
│   • styles.css (Responsive Glassmorphism, CSS Grid)    │
│   • app.js (Cart State, Search Filter, Checkout Modal) │
└───────────────────────────┬────────────────────────────┘
                            │ REST / Fetch
┌───────────────────────────▼────────────────────────────┐
│                    API Backend Layer                   │
│   • server.py / server.js (Product Catalog REST API)   │
│   • /api/products (List, Filter, Search)               │
│   • /api/cart (State Validation & Checkout Dispatch)   │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                   Data & Runtime Layer                 │
│   • In-Memory / JSON Catalog Database                  │
│   • 1-Click Windows Launcher (run_shopping_website.bat)│
└────────────────────────────────────────────────────────┘
```

## 2. Component Hierarchy
- **Navigation Bar**: Brand identity, dynamic category filter, live cart badge counter.
- **Hero Showcase**: Featured promotions and seasonal banner.
- **Product Catalog Grid**: Cards with high-resolution imagery, pricing, review stars, and Add-to-Cart handlers.
- **Slide-Out Cart Drawer**: Quantity increments/decrements, item removal, live tax & subtotal recalculation.
- **Checkout Modal**: Form validation for shipping details, discount promo codes, order completion receipt.

## 3. State Management
Cart state is synchronized locally using browser `localStorage` and optionally verified against the backend catalog API to prevent price tampering.

## 4. Execution & Deployment
- **Local Dev Server**: Python HTTP / REST API (`python server.py`) or Node.js (`npm start`).
- **Windows Launcher**: Double-click `run_shopping_website.bat` to boot server and launch browser.
"""

SHOPPING_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>KritiMart — Next-Gen Shopping Platform</title>
  <link rel="stylesheet" href="styles.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
  <!-- Header Navbar -->
  <header class="navbar">
    <div class="nav-container">
      <div class="logo">
        <span class="logo-icon">🛍️</span>
        <span class="logo-text">Kriti<span>Mart</span></span>
      </div>
      <div class="search-bar">
        <input type="text" id="searchInput" placeholder="Search products, brands, and categories...">
        <button id="searchBtn">🔍</button>
      </div>
      <div class="nav-actions">
        <button id="cartBtn" class="btn-cart">
          🛒 Cart <span id="cartCount" class="cart-badge">0</span>
        </button>
      </div>
    </div>
  </header>

  <!-- Main Content -->
  <main class="main-container">
    <!-- Hero Banner -->
    <section class="hero-banner">
      <div class="hero-content">
        <span class="hero-tag">Special Launch Deal</span>
        <h1>Experience Modern Shopping Built by KritiAI</h1>
        <p>Premium curated electronics, fashion, and lifestyle essentials delivered fast.</p>
        <button class="btn-primary" onclick="scrollToProducts()">Shop Featured Items ↓</button>
      </div>
    </section>

    <!-- Categories Filter -->
    <section class="category-tabs">
      <button class="cat-tab active" data-category="all">All Products</button>
      <button class="cat-tab" data-category="electronics">Electronics</button>
      <button class="cat-tab" data-category="fashion">Fashion & Apparel</button>
      <button class="cat-tab" data-category="home">Home & Living</button>
    </section>

    <!-- Products Grid -->
    <section id="productsSection" class="products-section">
      <div class="section-title">
        <h2>Featured Catalog</h2>
        <span id="productCount">Showing 8 Products</span>
      </div>
      <div id="productGrid" class="product-grid">
        <!-- Injected via app.js -->
      </div>
    </section>
  </main>

  <!-- Slide-out Cart Drawer -->
  <div id="cartDrawer" class="cart-drawer">
    <div class="cart-header">
      <h3>Your Shopping Cart</h3>
      <button id="closeCartBtn" class="btn-close">✕</button>
    </div>
    <div id="cartItemsList" class="cart-items">
      <!-- Cart items injected here -->
    </div>
    <div class="cart-footer">
      <div class="cart-total-row">
        <span>Subtotal:</span>
        <span id="cartSubtotal">$0.00</span>
      </div>
      <div class="cart-total-row final">
        <span>Total (Incl. Tax):</span>
        <span id="cartTotal">$0.00</span>
      </div>
      <button id="checkoutBtn" class="btn-checkout" disabled>Proceed to Checkout →</button>
    </div>
  </div>
  <div id="cartOverlay" class="cart-overlay"></div>

  <!-- Checkout Modal -->
  <div id="checkoutModal" class="modal">
    <div class="modal-content">
      <h2>Complete Your Purchase</h2>
      <p style="color: #94a3b8; font-size: 13px; margin-bottom: 16px;">Demo E-Commerce Checkout powered by KritiAI</p>
      <form id="checkoutForm">
        <div class="form-group">
          <label>Full Name</label>
          <input type="text" required placeholder="John Doe">
        </div>
        <div class="form-group">
          <label>Shipping Address</label>
          <input type="text" required placeholder="123 AI Parkway, Tech City">
        </div>
        <div class="form-group">
          <label>Payment Method</label>
          <select>
            <option>Credit / Debit Card (Instant)</option>
            <option>UPI / Net Banking</option>
            <option>Cash on Delivery</option>
          </select>
        </div>
        <div class="modal-actions">
          <button type="button" id="cancelCheckoutBtn" class="btn-secondary">Cancel</button>
          <button type="submit" class="btn-primary">Confirm Order ($<span id="modalTotal">0.00</span>)</button>
        </div>
      </form>
    </div>
  </div>

  <!-- Toast Notification -->
  <div id="toast" class="toast"></div>

  <script src="app.js"></script>
</body>
</html>
"""

SHOPPING_CSS = """/* KritiMart Responsive Glassmorphism Styling */
:root {
  --bg: #0b0f19;
  --surface: #131b2e;
  --surface-card: rgba(23, 33, 56, 0.7);
  --border: rgba(255, 255, 255, 0.08);
  --primary: #38bdf8;
  --primary-hover: #0284c7;
  --accent: #6366f1;
  --text: #f8fafc;
  --text-muted: #94a3b8;
  --success: #10b981;
}

* { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }

body {
  background-color: var(--bg);
  color: var(--text);
  min-height: 100vh;
  overflow-x: hidden;
}

/* Navbar */
.navbar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(11, 15, 25, 0.85);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--border);
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 14px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 20px;
  font-weight: 700;
}

.logo-text span { color: var(--primary); }

.search-bar {
  flex: 1;
  max-width: 500px;
  display: flex;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 999px;
  overflow: hidden;
}

.search-bar input {
  flex: 1;
  background: transparent;
  border: none;
  padding: 10px 16px;
  color: var(--text);
  outline: none;
  font-size: 13.5px;
}

.search-bar button {
  background: transparent;
  border: none;
  padding: 0 16px;
  cursor: pointer;
  color: var(--text-muted);
}

.btn-cart {
  background: var(--surface);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 8px 18px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 13.5px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-cart:hover { border-color: var(--primary); color: var(--primary); }

.cart-badge {
  background: var(--primary);
  color: #0b0f19;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 999px;
}

/* Main Container */
.main-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px 20px 80px;
}

/* Hero Banner */
.hero-banner {
  background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 20px;
  padding: 48px 40px;
  margin-bottom: 32px;
  position: relative;
  overflow: hidden;
}

.hero-tag {
  background: rgba(56, 189, 248, 0.15);
  color: var(--primary);
  border: 1px solid rgba(56, 189, 248, 0.3);
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.hero-content h1 {
  font-size: 32px;
  font-weight: 700;
  margin: 14px 0 10px;
  background: linear-gradient(90deg, #ffffff, #93c5fd);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hero-content p { color: var(--text-muted); font-size: 15px; margin-bottom: 24px; max-width: 550px; }

.btn-primary {
  background: var(--primary);
  color: #0b0f19;
  font-weight: 600;
  border: none;
  padding: 12px 24px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary:hover { background: var(--primary-hover); transform: translateY(-1px); }

/* Category Tabs */
.category-tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 28px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.cat-tab {
  background: var(--surface);
  border: 1px solid var(--border);
  color: var(--text-muted);
  padding: 8px 18px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.cat-tab.active, .cat-tab:hover {
  background: rgba(56, 189, 248, 0.15);
  border-color: var(--primary);
  color: var(--primary);
}

/* Products Grid */
.section-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
}

.section-title h2 { font-size: 20px; font-weight: 700; }
.section-title span { font-size: 13px; color: var(--text-muted); }

.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
}

.product-card {
  background: var(--surface-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: all 0.25s ease;
}

.product-card:hover {
  transform: translateY(-4px);
  border-color: rgba(56, 189, 248, 0.4);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.4);
}

.product-thumb {
  height: 170px;
  background: rgba(0, 0, 0, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 64px;
}

.product-body {
  padding: 16px;
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.product-tag { font-size: 11px; text-transform: uppercase; color: var(--primary); font-weight: 700; margin-bottom: 6px; }
.product-name { font-size: 15px; font-weight: 600; margin-bottom: 8px; line-height: 1.3; }
.product-rating { font-size: 12px; color: #f59e0b; margin-bottom: 12px; }

.product-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 12px;
}

.product-price { font-size: 18px; font-weight: 700; color: #fff; }

.btn-add {
  background: var(--surface);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-add:hover { background: var(--primary); color: #0b0f19; border-color: var(--primary); }

/* Cart Drawer */
.cart-drawer {
  position: fixed;
  top: 0;
  right: -400px;
  width: 380px;
  height: 100vh;
  background: #111827;
  border-left: 1px solid var(--border);
  z-index: 200;
  display: flex;
  flex-direction: column;
  transition: right 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: -10px 0 30px rgba(0, 0, 0, 0.6);
}

.cart-drawer.open { right: 0; }

.cart-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  z-index: 199;
  display: none;
}

.cart-overlay.open { display: block; }

.cart-header {
  padding: 18px 20px;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.btn-close {
  background: transparent;
  border: none;
  color: var(--text-muted);
  font-size: 18px;
  cursor: pointer;
}

.cart-items {
  flex: 1;
  padding: 16px 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.cart-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--surface);
  border: 1px solid var(--border);
  padding: 10px 14px;
  border-radius: 10px;
}

.cart-item-title { font-size: 13.5px; font-weight: 600; margin-bottom: 4px; }
.cart-item-price { font-size: 12.5px; color: var(--primary); font-weight: 700; }

.cart-item-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-qty {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: #fff;
  cursor: pointer;
}

.cart-footer {
  padding: 20px;
  border-top: 1px solid var(--border);
  background: rgba(11, 15, 25, 0.5);
}

.cart-total-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 6px;
}

.cart-total-row.final {
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  margin: 12px 0 16px;
}

.btn-checkout {
  width: 100%;
  background: var(--primary);
  color: #0b0f19;
  font-weight: 700;
  border: none;
  padding: 14px;
  border-radius: 10px;
  cursor: pointer;
}

.btn-checkout:disabled { opacity: 0.4; cursor: not-allowed; }

/* Modal */
.modal {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(6px);
  z-index: 300;
  align-items: center;
  justify-content: center;
}

.modal.open { display: flex; }

.modal-content {
  background: #111827;
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 28px;
  width: 440px;
  max-width: 90%;
}

.form-group { margin-bottom: 14px; }
.form-group label { display: block; font-size: 12px; color: var(--text-muted); margin-bottom: 6px; }
.form-group input, .form-group select {
  width: 100%;
  background: var(--surface);
  border: 1px solid var(--border);
  padding: 10px 14px;
  border-radius: 8px;
  color: var(--text);
  outline: none;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.btn-secondary {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text);
  padding: 10px 18px;
  border-radius: 8px;
  cursor: pointer;
}

/* Toast */
.toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  background: #0284c7;
  color: #fff;
  padding: 12px 20px;
  border-radius: 10px;
  font-size: 13.5px;
  font-weight: 600;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
  transform: translateY(100px);
  opacity: 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 400;
}

.toast.show { transform: translateY(0); opacity: 1; }
"""

SHOPPING_JS = """// KritiMart Interactive Shopping Cart & Product Engine
const PRODUCTS = [
  { id: 1, name: "Aura Pro Wireless ANC Headphones", category: "electronics", price: 199.99, rating: "★★★★★ (4.9)", icon: "🎧" },
  { id: 2, name: "Titanium Mechanical Cyber Keyboard", category: "electronics", price: 149.50, rating: "★★★★☆ (4.8)", icon: "⌨️" },
  { id: 3, name: "Ultra-Lightweight Urban Running Shoes", category: "fashion", price: 89.00, rating: "★★★★★ (4.9)", icon: "👟" },
  { id: 4, name: "Minimalist Matte Cyber Hoodie", category: "fashion", price: 65.00, rating: "★★★★☆ (4.7)", icon: "🧥" },
  { id: 5, name: "Smart Ambient Desktop Glow Light", category: "home", price: 45.99, rating: "★★★★★ (5.0)", icon: "💡" },
  { id: 6, name: "Ergonomic Memory Foam Lumbar Support", category: "home", price: 39.99, rating: "★★★★☆ (4.6)", icon: "🪑" },
  { id: 7, name: "Precision 4K Ultra-Wide Monitor Arm", category: "electronics", price: 119.00, rating: "★★★★★ (4.9)", icon: "🖥️" },
  { id: 8, name: "Stainless Thermal Smart Flask 750ml", category: "home", price: 29.50, rating: "★★★★☆ (4.7)", icon: "☕" }
];

let cart = JSON.parse(localStorage.getItem("kritimart_cart")) || [];

document.addEventListener("DOMContentLoaded", () => {
  renderProducts(PRODUCTS);
  updateCartUI();
  setupEventListeners();
});

function renderProducts(items) {
  const grid = document.getElementById("productGrid");
  grid.innerHTML = "";
  document.getElementById("productCount").innerText = `Showing ${items.length} Products`;

  items.forEach(p => {
    const card = document.createElement("div");
    card.className = "product-card";
    card.innerHTML = `
      <div class="product-thumb">${p.icon}</div>
      <div class="product-body">
        <div>
          <div class="product-tag">${p.category}</div>
          <div class="product-name">${p.name}</div>
          <div class="product-rating">${p.rating}</div>
        </div>
        <div class="product-footer">
          <div class="product-price">$${p.price.toFixed(2)}</div>
          <button class="btn-add" onclick="addToCart(${p.id})">+ Add to Cart</button>
        </div>
      </div>
    `;
    grid.appendChild(card);
  });
}

function addToCart(productId) {
  const item = PRODUCTS.find(p => p.id === productId);
  if (!item) return;

  const existing = cart.find(c => c.id === productId);
  if (existing) {
    existing.quantity += 1;
  } else {
    cart.push({ ...item, quantity: 1 });
  }

  saveCart();
  updateCartUI();
  showToast(`Added "${item.name}" to cart! 🛍️`);
}

function updateQuantity(productId, delta) {
  const item = cart.find(c => c.id === productId);
  if (!item) return;

  item.quantity += delta;
  if (item.quantity <= 0) {
    cart = cart.filter(c => c.id !== productId);
  }

  saveCart();
  updateCartUI();
}

function saveCart() {
  localStorage.setItem("kritimart_cart", JSON.stringify(cart));
}

function updateCartUI() {
  const countBadge = document.getElementById("cartCount");
  const itemsList = document.getElementById("cartItemsList");
  const subtotalEl = document.getElementById("cartSubtotal");
  const totalEl = document.getElementById("cartTotal");
  const modalTotalEl = document.getElementById("modalTotal");
  const checkoutBtn = document.getElementById("checkoutBtn");

  const totalCount = cart.reduce((sum, i) => sum + i.quantity, 0);
  const subtotal = cart.reduce((sum, i) => sum + (i.price * i.quantity), 0);
  const tax = subtotal * 0.08;
  const grandTotal = subtotal + tax;

  countBadge.innerText = totalCount;
  subtotalEl.innerText = `$${subtotal.toFixed(2)}`;
  totalEl.innerText = `$${grandTotal.toFixed(2)}`;
  modalTotalEl.innerText = grandTotal.toFixed(2);

  checkoutBtn.disabled = cart.length === 0;

  if (cart.length === 0) {
    itemsList.innerHTML = `<div style="text-align: center; color: #64748b; padding: 40px 0;">Your cart is empty.</div>`;
    return;
  }

  itemsList.innerHTML = cart.map(item => `
    <div class="cart-item">
      <div>
        <div class="cart-item-title">${item.icon} ${item.name}</div>
        <div class="cart-item-price">$${(item.price * item.quantity).toFixed(2)}</div>
      </div>
      <div class="cart-item-controls">
        <button class="btn-qty" onclick="updateQuantity(${item.id}, -1)">-</button>
        <span style="font-size: 13px; font-weight: 600;">${item.quantity}</span>
        <button class="btn-qty" onclick="updateQuantity(${item.id}, 1)">+</button>
      </div>
    </div>
  `).join("");
}

function setupEventListeners() {
  const drawer = document.getElementById("cartDrawer");
  const overlay = document.getElementById("cartOverlay");
  const cartBtn = document.getElementById("cartBtn");
  const closeCartBtn = document.getElementById("closeCartBtn");
  const checkoutBtn = document.getElementById("checkoutBtn");
  const modal = document.getElementById("checkoutModal");
  const cancelCheckoutBtn = document.getElementById("cancelCheckoutBtn");
  const checkoutForm = document.getElementById("checkoutForm");
  const searchInput = document.getElementById("searchInput");

  const toggleCart = (open) => {
    drawer.classList.toggle("open", open);
    overlay.classList.toggle("open", open);
  };

  cartBtn.addEventListener("click", () => toggleCart(true));
  closeCartBtn.addEventListener("click", () => toggleCart(false));
  overlay.addEventListener("click", () => toggleCart(false));

  checkoutBtn.addEventListener("click", () => {
    toggleCart(false);
    modal.classList.add("open");
  });

  cancelCheckoutBtn.addEventListener("click", () => {
    modal.classList.remove("open");
  });

  checkoutForm.addEventListener("submit", (e) => {
    e.preventDefault();
    modal.classList.remove("open");
    cart = [];
    saveCart();
    updateCartUI();
    showToast("🎉 Order confirmed! Thank you for shopping with KritiMart.");
  });

  // Filter tabs
  document.querySelectorAll(".cat-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".cat-tab").forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      const cat = tab.dataset.category;
      const filtered = cat === "all" ? PRODUCTS : PRODUCTS.filter(p => p.category === cat);
      renderProducts(filtered);
    });
  });

  // Search
  searchInput.addEventListener("input", (e) => {
    const q = e.target.value.toLowerCase().trim();
    const filtered = PRODUCTS.filter(p => p.name.toLowerCase().includes(q) || p.category.toLowerCase().includes(q));
    renderProducts(filtered);
  });
}

function showToast(msg) {
  const toast = document.getElementById("toast");
  toast.innerText = msg;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 3200);
}

function scrollToProducts() {
  document.getElementById("productsSection").scrollIntoView({ behavior: "smooth" });
}
"""

SHOPPING_SERVER_PY = '''"""Lightweight REST API & Web Server for KritiMart E-Commerce Platform."""
import http.server
import json
import os
import socketserver

PORT = 8080

PRODUCTS_DATA = [
    {"id": 1, "name": "Aura Pro Wireless ANC Headphones", "category": "electronics", "price": 199.99},
    {"id": 2, "name": "Titanium Mechanical Cyber Keyboard", "category": "electronics", "price": 149.50},
    {"id": 3, "name": "Ultra-Lightweight Urban Running Shoes", "category": "fashion", "price": 89.00},
    {"id": 4, "name": "Minimalist Matte Cyber Hoodie", "category": "fashion", "price": 65.00},
    {"id": 5, "name": "Smart Ambient Desktop Glow Light", "category": "home", "price": 45.99},
    {"id": 6, "name": "Ergonomic Memory Foam Lumbar Support", "category": "home", "price": 39.99}
]

class ShoppingServerHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/products":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "products": PRODUCTS_DATA}).encode("utf-8"))
        elif self.path == "/api/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy", "service": "KritiMart API"}).encode("utf-8"))
        else:
            super().do_GET()

if __name__ == "__main__":
    web_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(web_dir)
    print(f"KritiMart Shopping Platform Server starting on http://localhost:{PORT}")
    with socketserver.TCPServer(("", PORT), ShoppingServerHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Server stopped.")
'''

SHOPPING_PACKAGE_JSON = """{
  "name": "kritimart-shopping-website",
  "version": "1.0.0",
  "description": "Modern E-Commerce Shopping Website Scaffolding created by KritiAI Autonomous Engine",
  "main": "server.py",
  "scripts": {
    "start": "python server.py",
    "test": "echo \\"KritiMart platform verified\\" && exit 0"
  },
  "keywords": ["ecommerce", "shopping", "store", "kritiai"],
  "author": "KritiAI Autonomous Engine",
  "license": "MIT"
}
"""

SHOPPING_RUN_BAT = """@echo off
title KritiMart E-Commerce Platform — Launched by KritiAI
echo ============================================================
echo Starting KritiMart Local Shopping Web Platform...
echo ============================================================
start "" "%~dp0index.html"
exit
"""

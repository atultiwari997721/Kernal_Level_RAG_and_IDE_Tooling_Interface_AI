// KritiAI Windows Execution Dashboard Controller
let currentTaskId = null;
let ws = null;
let currentConfig = null;

// Initialize
document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initPowerModes();
  initEmergencyStop();
  initKritiMode();
  initChatMode();
  initSettings();
  initWebSocket();
  loadConfig();
});

// WebSocket Connection
function initWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws`;
  
  ws = new WebSocket(wsUrl);
  
  ws.onopen = () => {
    logTerminal("[WebSocket] Connected to KritiAI local execution bus.");
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleWsEvent(data);
    } catch (e) {
      console.error("WS Parse error:", e);
    }
  };

  ws.onclose = () => {
    logTerminal("[WebSocket] Disconnected. Reconnecting in 3s...");
    setTimeout(initWebSocket, 3000);
  };
}

function handleWsEvent(msg) {
  if (msg.event === "emergency_stop") {
    setTelemetryStatus("CANCELLED", "badge-failed");
    logTerminal("\n🛑 [EMERGENCY STOP ACTIVATED] All processes halted immediately.");
    document.getElementById("emergencyStopBtn").classList.add("pulsing");
  } else if (msg.event === "plan_created") {
    renderPlan(msg.plan);
    setTelemetryStatus("EXECUTING", "badge-executing");
  } else if (msg.event === "step_started") {
    updatePlanStep(msg.step.step_index, "in_progress");
    document.getElementById("telemetryAgent").innerText = msg.step.agent;
    document.getElementById("telemetryTool").innerText = msg.step.tool;
    logTerminal(`→ [EXECUTE] Step ${msg.step.step_index + 1}: ${msg.step.objective}`);
  } else if (msg.event === "step_completed") {
    updatePlanStep(msg.step.step_index, "completed");
    logTerminal(`✓ [VERIFIED] Step ${msg.step.step_index + 1}: ${msg.step.expected_result}`);
  } else if (msg.event === "task_completed") {
    setTelemetryStatus("COMPLETED", "badge-completed");
    document.getElementById("verificationBadge").innerText = "Verified Complete";
    document.getElementById("verificationBadge").className = "badge badge-success";
    document.getElementById("resultOutput").innerText = msg.result;
    logTerminal(`\n★ [TASK COMPLETE] ${msg.result}`);
    enableTaskControls(false);
  }
}

// Tab Switching
function initTabs() {
  document.querySelectorAll(".nav-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".nav-tab").forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
      
      tab.classList.add("active");
      const targetId = `tab-${tab.dataset.tab}`;
      const targetContent = document.getElementById(targetId);
      if (targetContent) targetContent.classList.add("active");

      // Tab specific refreshes
      if (tab.dataset.tab === "tasks") loadTasks();
      if (tab.dataset.tab === "memory") loadMemory();
      if (tab.dataset.tab === "audit") loadAuditLogs();
      if (tab.dataset.tab === "settings") loadSettingsTab();
    });
  });
}

// Power Mode Selection
function initPowerModes() {
  document.querySelectorAll(".power-pill").forEach(pill => {
    pill.addEventListener("click", async () => {
      const mode = pill.dataset.mode;
      document.querySelectorAll(".power-pill").forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      
      await fetch("/api/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ power_mode: mode })
      });
      logTerminal(`[POLICY] Active Power Mode changed to: ${mode.toUpperCase()}`);
    });
  });
}

// Emergency Stop
function initEmergencyStop() {
  const btn = document.getElementById("emergencyStopBtn");
  btn.addEventListener("click", async () => {
    if (confirm("Trigger EMERGENCY STOP? This will immediately terminate all active tasks and processes.")) {
      const res = await fetch("/api/emergency-stop", { method: "POST" });
      const data = await res.json();
      btn.classList.add("pulsing");
      alert(`Emergency STOP executed. Terminated ${data.terminated_pids.length} processes.`);
    }
  });
}

// KritiMode Controller
function initKritiMode() {
  const goalInput = document.getElementById("goalInput");
  const execBtn = document.getElementById("executeGoalBtn");
  const quickBtn = document.getElementById("quickTestGoalBtn");
  const clearBtn = document.getElementById("clearTerminalBtn");

  quickBtn.addEventListener("click", () => {
    goalInput.value = "Create a folder called Test";
    executeAutonomousGoal();
  });

  execBtn.addEventListener("click", () => {
    executeAutonomousGoal();
  });

  clearBtn.addEventListener("click", () => {
    document.getElementById("terminalOutput").innerText = "";
  });

  // Telemetry pause/cancel
  document.getElementById("cancelTaskBtn").addEventListener("click", async () => {
    if (currentTaskId) {
      await fetch(`/api/tasks/${currentTaskId}/cancel`, { method: "POST" });
      logTerminal("[TASK] Cancelled by user.");
      setTelemetryStatus("CANCELLED", "badge-failed");
      enableTaskControls(false);
    }
  });
}

async function executeAutonomousGoal() {
  const goal = document.getElementById("goalInput").value.trim();
  if (!goal) return;

  logTerminal(`\n======================================================`);
  logTerminal(`[GOAL RECEIVED] "${goal}"`);
  logTerminal(`[ORCHESTRATOR] Analyzing goal, loading memory context...`);

  setTelemetryStatus("UNDERSTANDING", "badge-executing");
  document.getElementById("verificationBadge").innerText = "Executing...";
  document.getElementById("verificationBadge").className = "badge badge-primary";
  document.getElementById("resultOutput").innerText = "Executing autonomous workflow...";
  enableTaskControls(true);

  try {
    const res = await fetch("/api/kritimode/execute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ goal: goal })
    });
    const result = await res.json();
    currentTaskId = result.task_id;

    if (result.approval_required) {
      setTelemetryStatus("WAITING_APPROVAL", "badge-warning");
      showApprovalModal(result);
    } else if (result.success) {
      setTelemetryStatus("COMPLETED", "badge-completed");
      document.getElementById("verificationBadge").innerText = "Verified Success";
      document.getElementById("verificationBadge").className = "badge badge-success";
      document.getElementById("resultOutput").innerText = result.final_result;
      logTerminal(`✓ [TASK FINISHED] ${result.final_result}`);
      enableTaskControls(false);
    } else {
      setTelemetryStatus("FAILED", "badge-failed");
      document.getElementById("verificationBadge").innerText = "Failed";
      document.getElementById("verificationBadge").className = "badge badge-danger";
      document.getElementById("resultOutput").innerText = result.error || "Execution failed";
      logTerminal(`✗ [ERROR] ${result.error}`);
      enableTaskControls(false);
    }
  } catch (err) {
    setTelemetryStatus("ERROR", "badge-failed");
    logTerminal(`✗ [NETWORK/SERVER ERROR] ${err.message}`);
    enableTaskControls(false);
  }
}

function renderPlan(steps) {
  const container = document.getElementById("planList");
  container.innerHTML = "";
  document.getElementById("planStepCount").innerText = `${steps.length} Steps`;

  steps.forEach((s, i) => {
    const item = document.createElement("div");
    item.className = `plan-step-item ${s.status}`;
    item.id = `step-item-${i}`;
    item.innerHTML = `
      <div class="step-indicator">${s.status === 'completed' ? '✓' : (s.status === 'in_progress' ? '→' : '○')}</div>
      <div class="step-content">
        <div class="step-title">${s.objective}</div>
        <div class="step-meta">Agent: <strong>${s.agent}</strong> | Tool: <strong>${s.tool}</strong></div>
      </div>
    `;
    container.appendChild(item);
  });
}

function updatePlanStep(index, status) {
  const item = document.getElementById(`step-item-${index}`);
  if (!item) return;
  item.className = `plan-step-item ${status}`;
  const indicator = item.querySelector(".step-indicator");
  if (indicator) {
    indicator.innerText = status === 'completed' ? '✓' : (status === 'in_progress' ? '→' : '○');
  }
}

function logTerminal(text) {
  const term = document.getElementById("terminalOutput");
  term.innerText += text + "\n";
  term.scrollTop = term.scrollHeight;
}

function setTelemetryStatus(text, badgeClass) {
  const badge = document.getElementById("telemetryStatus");
  badge.innerText = text;
  badge.className = `value status-badge ${badgeClass}`;
}

function enableTaskControls(enabled) {
  document.getElementById("cancelTaskBtn").disabled = !enabled;
  document.getElementById("pauseTaskBtn").disabled = !enabled;
}

// Chat Mode
function initChatMode() {
  const input = document.getElementById("chatInput");
  const sendBtn = document.getElementById("chatSendBtn");

  const send = async () => {
    const text = input.value.trim();
    if (!text) return;
    input.value = "";
    appendChatMessage("user", "You", text);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text })
      });
      const data = await res.json();
      appendChatMessage("assistant", "KritiAI", data.content);
    } catch (e) {
      appendChatMessage("assistant", "KritiAI", `[Error: ${e.message}]`);
    }
  };

  sendBtn.addEventListener("click", send);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") send();
  });
}

function appendChatMessage(role, sender, text) {
  const container = document.getElementById("chatMessages");
  const div = document.createElement("div");
  div.className = `message ${role}`;
  div.innerHTML = `
    <div class="message-sender">${sender}</div>
    <div class="message-content">${text}</div>
  `;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

// Tasks Table
async function loadTasks() {
  try {
    const res = await fetch("/api/tasks");
    const tasks = await res.json();
    const tbody = document.getElementById("tasksTableBody");
    if (!tasks.length) {
      tbody.innerHTML = `<tr><td colspan="5" class="empty-state">No execution tasks recorded yet.</td></tr>`;
      return;
    }
    tbody.innerHTML = tasks.map(t => `
      <tr>
        <td><code>${t.id.substring(0, 8)}</code></td>
        <td><strong>${t.goal}</strong></td>
        <td><span class="badge ${t.status === 'completed' ? 'badge-success' : 'badge-primary'}">${t.status}</span></td>
        <td>${t.power_mode}</td>
        <td>${new Date(t.created_at).toLocaleTimeString()}</td>
      </tr>
    `).join("");
  } catch (e) {
    console.error("Tasks fetch error:", e);
  }
}

// Memory Table
async function loadMemory() {
  try {
    const res = await fetch("/api/memory");
    const entries = await res.json();
    const tbody = document.getElementById("memoryTableBody");
    if (!entries.length) {
      tbody.innerHTML = `<tr><td colspan="4" class="empty-state">Memory is empty.</td></tr>`;
      return;
    }
    tbody.innerHTML = entries.map(m => `
      <tr>
        <td><span class="badge badge-secondary">${m.tier}</span></td>
        <td><code>${m.key || '—'}</code></td>
        <td>${m.content}</td>
        <td>${new Date(m.created_at).toLocaleTimeString()}</td>
      </tr>
    `).join("");
  } catch (e) {
    console.error("Memory fetch error:", e);
  }
}

// Audit Table
async function loadAuditLogs() {
  try {
    const res = await fetch("/api/audit");
    const logs = await res.json();
    const tbody = document.getElementById("auditTableBody");
    if (!logs.length) {
      tbody.innerHTML = `<tr><td colspan="7" class="empty-state">No audit events recorded yet.</td></tr>`;
      return;
    }
    tbody.innerHTML = logs.map(l => `
      <tr>
        <td>${new Date(l.timestamp).toLocaleTimeString()}</td>
        <td><strong>${l.tool}</strong></td>
        <td>${l.action}</td>
        <td><span class="badge ${l.risk_level === 'high' ? 'badge-danger' : 'badge-primary'}">${l.risk_level}</span></td>
        <td>${l.power_mode}</td>
        <td><span class="badge ${l.decision === 'allow' ? 'badge-success' : 'badge-warning'}">${l.decision}</span></td>
        <td>${l.status}</td>
      </tr>
    `).join("");
  } catch (e) {
    console.error("Audit fetch error:", e);
  }
}

// Settings & Telemetry
async function loadConfig() {
  try {
    const res = await fetch("/api/config");
    currentConfig = await res.json();

    // Set active pill
    document.querySelectorAll(".power-pill").forEach(p => {
      p.classList.toggle("active", p.dataset.mode === currentConfig.power_mode);
    });

    if (currentConfig.emergency_stop_active) {
      document.getElementById("emergencyStopBtn").classList.add("pulsing");
    }
  } catch (e) {
    console.error("Config fetch error:", e);
  }
}

async function loadSettingsTab() {
  await loadConfig();
  if (currentConfig) {
    document.getElementById("settingPowerMode").value = currentConfig.power_mode;
    document.getElementById("settingGeneralModel").value = currentConfig.models.general_model;
    document.getElementById("settingCodingModel").value = currentConfig.models.coding_model;
    document.getElementById("settingPreferLocal").checked = currentConfig.models.prefer_local;
    document.getElementById("permFilesystem").checked = currentConfig.permissions.allow_filesystem;
    document.getElementById("permTerminal").checked = currentConfig.permissions.allow_terminal;
    document.getElementById("permPowershell").checked = currentConfig.permissions.allow_powershell;
    document.getElementById("permAppControl").checked = currentConfig.permissions.allow_application_control;
    document.getElementById("permKeyboardMouse").checked = currentConfig.permissions.allow_keyboard_mouse;
  }

  // Load hardware telemetry
  try {
    const res = await fetch("/api/system-info");
    const sys = await res.json();
    document.getElementById("systemInfoContent").innerText = JSON.stringify(sys, null, 2);
  } catch (e) {
    document.getElementById("systemInfoContent").innerText = "Error loading telemetry";
  }
}

function initSettings() {
  document.getElementById("saveSettingsBtn").addEventListener("click", async () => {
    const payload = {
      power_mode: document.getElementById("settingPowerMode").value,
      general_model: document.getElementById("settingGeneralModel").value,
      coding_model: document.getElementById("settingCodingModel").value,
      prefer_local: document.getElementById("settingPreferLocal").checked,
      allow_filesystem: document.getElementById("permFilesystem").checked,
      allow_terminal: document.getElementById("permTerminal").checked,
      allow_powershell: document.getElementById("permPowershell").checked,
      allow_application_control: document.getElementById("permAppControl").checked,
      allow_keyboard_mouse: document.getElementById("permKeyboardMouse").checked
    };

    await fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    alert("Settings saved successfully.");
    await loadConfig();
  });

  document.getElementById("clearMemoryBtn").addEventListener("click", async () => {
    if (confirm("Clear all local memory entries?")) {
      await fetch("/api/memory", { method: "DELETE" });
      loadMemory();
    }
  });

  document.getElementById("refreshTasksBtn").addEventListener("click", loadTasks);
  document.getElementById("refreshMemoryBtn").addEventListener("click", loadMemory);
  document.getElementById("refreshAuditBtn").addEventListener("click", loadAuditLogs);
}

// Modal
function showApprovalModal(data) {
  const modal = document.getElementById("approvalModal");
  document.getElementById("approvalPrompt").innerText = data.prompt || "Confirmation required.";
  document.getElementById("approvalDetails").innerText = JSON.stringify(data.step, null, 2);
  modal.classList.remove("hidden");

  document.getElementById("approvalAllowOnceBtn").onclick = () => {
    modal.classList.add("hidden");
    logTerminal("[USER] Approved action once.");
  };
  document.getElementById("approvalAlwaysAllowBtn").onclick = () => {
    modal.classList.add("hidden");
    logTerminal("[USER] Action marked permanently allowed.");
  };
  document.getElementById("approvalDenyBtn").onclick = () => {
    modal.classList.add("hidden");
    logTerminal("[USER] Action denied by user.");
    setTelemetryStatus("DENIED", "badge-failed");
  };
}

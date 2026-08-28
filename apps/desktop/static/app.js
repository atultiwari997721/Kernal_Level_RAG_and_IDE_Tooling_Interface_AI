// ==========================================================================
// KritiAI Desktop Controller — Modern Soothing Glassmorphism Engine
// ==========================================================================

let currentTaskId = null;
let ws = null;
let currentConfig = null;
let lastTaskData = null;

document.addEventListener("DOMContentLoaded", () => {
  initNavigation();
  initPowerModes();
  initEmergencyStop();
  initKritiMode();
  initChatMode();
  initSettings();
  initWebSocket();
  loadConfig();
});

// ==========================================================================
// WebSocket Connection
// ==========================================================================
function initWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws`;

  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    logTerminal("[SYS]", "Connected to KritiAI local execution bus.");
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleWsEvent(data);
    } catch (e) {
      console.error("WS parse error:", e);
    }
  };

  ws.onclose = () => {
    logTerminal("[SYS]", "Disconnected from local bus. Reconnecting in 3s...");
    setTimeout(initWebSocket, 3000);
  };
}

function handleWsEvent(msg) {
  if (msg.event === "emergency_stop") {
    setTelemetryStatus("STOPPED", "status-err");
    logTerminal("[STOP]", "EMERGENCY STOP ACTIVATED. All tasks halted.", "log-err");
    document.getElementById("emergencyStopBtn").classList.add("pulsing");
    enableTaskControls(false);
  } else if (msg.event === "plan_created") {
    renderPlan(msg.plan);
    setTelemetryStatus("EXECUTING", "status-active");
    logTerminal("[PLAN]", `Generated ${msg.plan.length} verifiable execution step(s).`, "log-plan");
  } else if (msg.event === "step_started") {
    updatePlanStep(msg.step.step_index, "in_progress");
    document.getElementById("telemetryAgent").innerText = msg.step.agent;
    document.getElementById("telemetryTool").innerText = msg.step.tool;
    logTerminal("[EXEC]", `Step ${msg.step.step_index + 1}: ${msg.step.objective}`, "log-exec");
  } else if (msg.event === "step_completed") {
    updatePlanStep(msg.step.step_index, "completed");
    logTerminal("[VERIFY]", `✓ Step ${msg.step.step_index + 1} verified: ${msg.step.expected_result}`, "log-verif");
  } else if (msg.event === "task_completed") {
    setTelemetryStatus("COMPLETED", "status-done");
    const badge = document.getElementById("verificationBadge");
    badge.innerText = "Verified Complete";
    badge.className = "status-pill status-done";
    document.getElementById("resultOutput").innerText = msg.result;
    logTerminal("[COMPLETE]", `★ Task completed successfully.`, "log-done");
    enableTaskControls(false);

    // Setup interactive action buttons based on task metadata
    lastTaskData = msg;
    showOutcomeActionButtons(msg);
  }
}

// ==========================================================================
// Navigation & Tab Switching
// ==========================================================================
function initNavigation() {
  // Mode toggle buttons (KritiMode & Chat Mode)
  document.querySelectorAll(".mode-toggle-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      switchTab(btn.dataset.tab);
    });
  });

  // Secondary nav tabs
  document.querySelectorAll(".nav-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      switchTab(tab.dataset.tab);
    });
  });
}

function switchTab(tabId) {
  // Update mode toggle buttons
  document.querySelectorAll(".mode-toggle-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.tab === tabId);
  });

  // Update nav tabs
  document.querySelectorAll(".nav-tab").forEach(tab => {
    tab.classList.toggle("active", tab.dataset.tab === tabId);
  });

  // Show target content
  document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
  const target = document.getElementById(`tab-${tabId}`);
  if (target) target.classList.add("active");

  if (tabId === "tasks") loadTasks();
  if (tabId === "memory") loadMemory();
  if (tabId === "audit") loadAuditLogs();
  if (tabId === "settings") loadSettingsTab();
}

// ==========================================================================
// Power Modes & Emergency STOP
// ==========================================================================
function initPowerModes() {
  document.querySelectorAll(".power-btn[data-mode]").forEach(btn => {
    btn.addEventListener("click", async () => {
      const mode = btn.dataset.mode;
      document.querySelectorAll(".power-btn[data-mode]").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");

      await fetch("/api/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ power_mode: mode })
      });
      logTerminal("[POLICY]", `Power Mode set to: ${mode.toUpperCase()}`, "log-plan");
    });
  });
}

function initEmergencyStop() {
  const btn = document.getElementById("emergencyStopBtn");
  btn.addEventListener("click", async () => {
    if (confirm("Activate EMERGENCY STOP? This will immediately terminate all active tasks and running processes.")) {
      const res = await fetch("/api/emergency-stop", { method: "POST" });
      const data = await res.json();
      btn.classList.add("pulsing");
      logTerminal("[STOP]", `Emergency STOP triggered. Terminated: ${data.terminated_pids.length} process(es).`, "log-err");
    }
  });
}

// ==========================================================================
// KritiMode Controller & Quick Chips
// ==========================================================================
function initKritiMode() {
  const goalInput = document.getElementById("goalInput");
  const execBtn = document.getElementById("executeGoalBtn");
  const clearBtn = document.getElementById("clearTerminalBtn");

  // Quick Chips
  document.querySelectorAll(".chip-btn").forEach(chip => {
    chip.addEventListener("click", () => {
      goalInput.value = chip.dataset.goal;
      executeAutonomousGoal();
    });
  });

  execBtn.addEventListener("click", () => {
    executeAutonomousGoal();
  });

  goalInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      executeAutonomousGoal();
    }
  });

  clearBtn.addEventListener("click", () => {
    document.getElementById("terminalOutput").innerText = "";
  });

  // Telemetry cancel
  document.getElementById("cancelTaskBtn").addEventListener("click", async () => {
    if (currentTaskId) {
      await fetch(`/api/tasks/${currentTaskId}/cancel`, { method: "POST" });
      logTerminal("[TASK]", "Task cancelled by user.", "log-err");
      setTelemetryStatus("CANCELLED", "status-err");
      enableTaskControls(false);
    }
  });
}

async function executeAutonomousGoal() {
  const goal = document.getElementById("goalInput").value.trim();
  if (!goal) return;

  hideOutcomeActionButtons();
  logTerminal("\n------------------------------------------------------------");
  logTerminal("[INTENT]", `Goal submitted: "${goal}"`, "log-intent");

  setTelemetryStatus("ANALYZING", "status-active");
  const badge = document.getElementById("verificationBadge");
  badge.innerText = "Executing...";
  badge.className = "status-pill status-active";
  document.getElementById("resultOutput").innerText = "Analyzing objective and formulating verified plan...";
  enableTaskControls(true);

  try {
    const res = await fetch("/api/kritimode/execute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ goal: goal })
    });
    const result = await res.json();
    currentTaskId = result.task_id;
    lastTaskData = result;

    if (result.approval_required) {
      setTelemetryStatus("APPROVAL NEEDED", "status-active");
      showApprovalModal(result);
    } else if (result.success) {
      setTelemetryStatus("COMPLETED", "status-done");
      badge.innerText = "Verified Success";
      badge.className = "status-pill status-done";
      document.getElementById("resultOutput").innerText = result.final_result;
      logTerminal("[SUCCESS]", result.final_result, "log-done");
      enableTaskControls(false);
      showOutcomeActionButtons(result);
    } else {
      setTelemetryStatus("FAILED", "status-err");
      badge.innerText = "Failed";
      badge.className = "status-pill status-err";
      document.getElementById("resultOutput").innerText = result.error || "Execution failed.";
      logTerminal("[ERROR]", result.error || "Execution failed.", "log-err");
      enableTaskControls(false);
    }
  } catch (err) {
    setTelemetryStatus("ERROR", "status-err");
    logTerminal("[ERROR]", `Network error: ${err.message}`, "log-err");
    enableTaskControls(false);
  }
}

function renderPlan(steps) {
  const container = document.getElementById("planList");
  container.innerHTML = "";
  document.getElementById("planStepCount").innerText = `${steps.length} Steps`;

  steps.forEach((s, i) => {
    const item = document.createElement("div");
    item.className = `pipeline-step ${s.status}`;
    item.id = `step-item-${i}`;
    item.innerHTML = `
      <div class="step-badge">${s.status === 'completed' ? '✓' : (s.status === 'in_progress' ? '⟳' : i + 1)}</div>
      <div class="step-details">
        <div class="step-objective">${s.objective}</div>
        <div class="step-chips">
          <span class="step-tag">${s.agent}</span>
          <span class="step-tag">${s.tool}</span>
        </div>
      </div>
    `;
    container.appendChild(item);
  });
}

function updatePlanStep(index, status) {
  const item = document.getElementById(`step-item-${index}`);
  if (!item) return;
  item.className = `pipeline-step ${status}`;
  const badge = item.querySelector(".step-badge");
  if (badge) {
    badge.innerText = status === 'completed' ? '✓' : (status === 'in_progress' ? '⟳' : index + 1);
  }
}

function logTerminal(tag, message, highlightClass = "") {
  const term = document.getElementById("terminalOutput");
  const time = new Date().toLocaleTimeString();
  const line = `[${time}] ${tag} ${message}\n`;
  term.innerText += line;
  term.scrollTop = term.scrollHeight;
}

function setTelemetryStatus(text, pillClass) {
  const badge = document.getElementById("telemetryStatus");
  badge.innerText = text;
  badge.className = `status-pill ${pillClass}`;
}

function enableTaskControls(enabled) {
  document.getElementById("cancelTaskBtn").disabled = !enabled;
  document.getElementById("pauseTaskBtn").disabled = !enabled;
}

function hideOutcomeActionButtons() {
  document.getElementById("btnOpenFolder").style.display = "none";
  document.getElementById("btnOpenBrowser").style.display = "none";
  document.getElementById("btnLaunchApp").style.display = "none";
}

function showOutcomeActionButtons(taskData) {
  hideOutcomeActionButtons();
  const intent = taskData.intent_type || "";
  const target = taskData.target || "";

  if (intent === "create_calculator" || intent === "create_folder" || intent === "create_file") {
    const folderBtn = document.getElementById("btnOpenFolder");
    folderBtn.style.display = "inline-flex";
    folderBtn.onclick = () => openPathOnWindows(target);

    if (intent === "create_calculator") {
      const launchBtn = document.getElementById("btnLaunchApp");
      launchBtn.style.display = "inline-flex";
      launchBtn.innerText = "▶️ Launch Calculator";
      launchBtn.onclick = () => openPathOnWindows(`${target}\\calculator.html`);
    }
  }

  if (intent === "play_youtube" || intent === "search_web") {
    const browserBtn = document.getElementById("btnOpenBrowser");
    browserBtn.style.display = "inline-flex";
    browserBtn.onclick = () => {
      // Re-trigger playback or open
      fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: `open url https://www.youtube.com/results?search_query=${encodeURIComponent(target)}` })
      });
    };
  }
}

async function openPathOnWindows(pathStr) {
  if (!pathStr) return;
  try {
    await fetch("/api/open-path", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: pathStr })
    });
    logTerminal("[SYS]", `Opened in Windows Explorer / default application: ${pathStr}`);
  } catch (e) {
    console.error("Open path error:", e);
  }
}

// ==========================================================================
// Chat Mode
// ==========================================================================
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
      appendChatMessage("assistant", "KritiAI Assistant", data.content);
    } catch (e) {
      appendChatMessage("assistant", "KritiAI Assistant", `[Error: ${e.message}]`);
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
  div.className = `chat-bubble ${role}`;
  div.innerHTML = `
    <div class="chat-sender-label">${sender}</div>
    <div>${text}</div>
  `;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

// ==========================================================================
// Tables (Tasks, Memory, Audit)
// ==========================================================================
async function loadTasks() {
  try {
    const res = await fetch("/api/tasks");
    const tasks = await res.json();
    const tbody = document.getElementById("tasksTableBody");
    if (!tasks.length) {
      tbody.innerHTML = `<tr><td colspan="5" class="empty-cell">No tasks recorded yet.</td></tr>`;
      return;
    }
    tbody.innerHTML = tasks.map(t => `
      <tr>
        <td><code style="color: var(--accent-cyan);">${t.id.substring(0, 8)}</code></td>
        <td><strong>${t.goal}</strong></td>
        <td><span class="status-pill ${t.status === 'completed' ? 'status-done' : 'status-active'}">${t.status}</span></td>
        <td>${t.power_mode}</td>
        <td>${new Date(t.created_at).toLocaleTimeString()}</td>
      </tr>
    `).join("");
  } catch (e) {
    console.error("Tasks error:", e);
  }
}

async function loadMemory() {
  try {
    const res = await fetch("/api/memory");
    const entries = await res.json();
    const tbody = document.getElementById("memoryTableBody");
    if (!entries.length) {
      tbody.innerHTML = `<tr><td colspan="4" class="empty-cell">Memory is empty.</td></tr>`;
      return;
    }
    tbody.innerHTML = entries.map(m => `
      <tr>
        <td><span class="step-tag">${m.tier}</span></td>
        <td><code>${m.key || '—'}</code></td>
        <td>${m.content}</td>
        <td>${new Date(m.created_at).toLocaleTimeString()}</td>
      </tr>
    `).join("");
  } catch (e) {
    console.error("Memory error:", e);
  }
}

async function loadAuditLogs() {
  try {
    const res = await fetch("/api/audit");
    const logs = await res.json();
    const tbody = document.getElementById("auditTableBody");
    if (!logs.length) {
      tbody.innerHTML = `<tr><td colspan="7" class="empty-cell">No audit events recorded yet.</td></tr>`;
      return;
    }
    tbody.innerHTML = logs.map(l => `
      <tr>
        <td>${new Date(l.timestamp).toLocaleTimeString()}</td>
        <td><strong>${l.tool}</strong></td>
        <td>${l.action}</td>
        <td><span class="status-pill ${l.risk_level === 'high' ? 'status-err' : 'status-active'}">${l.risk_level}</span></td>
        <td>${l.power_mode}</td>
        <td><span class="status-pill ${l.decision === 'allow' ? 'status-done' : 'status-active'}">${l.decision}</span></td>
        <td>${l.status}</td>
      </tr>
    `).join("");
  } catch (e) {
    console.error("Audit error:", e);
  }
}

// ==========================================================================
// Settings & Telemetry
// ==========================================================================
async function loadConfig() {
  try {
    const res = await fetch("/api/config");
    currentConfig = await res.json();

    document.querySelectorAll(".power-btn[data-mode]").forEach(p => {
      p.classList.toggle("active", p.dataset.mode === currentConfig.power_mode);
    });

    if (currentConfig.emergency_stop_active) {
      document.getElementById("emergencyStopBtn").classList.add("pulsing");
    }
  } catch (e) {
    console.error("Config error:", e);
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

  try {
    const res = await fetch("/api/system-info");
    const sys = await res.json();
    document.getElementById("systemInfoContent").innerText = JSON.stringify(sys, null, 2);
  } catch (e) {
    document.getElementById("systemInfoContent").innerText = "Error loading hardware telemetry";
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

// ==========================================================================
// Approval Modal
// ==========================================================================
function showApprovalModal(data) {
  const modal = document.getElementById("approvalModal");
  document.getElementById("approvalPrompt").innerText = data.prompt || "Confirmation required for computer action.";
  document.getElementById("approvalDetails").innerText = JSON.stringify(data.step, null, 2);
  modal.classList.remove("hidden");

  document.getElementById("approvalAllowOnceBtn").onclick = () => {
    modal.classList.add("hidden");
    logTerminal("[USER]", "Approved action once.", "log-verif");
  };
  document.getElementById("approvalAlwaysAllowBtn").onclick = () => {
    modal.classList.add("hidden");
    logTerminal("[USER]", "Action marked permanently allowed.", "log-verif");
  };
  document.getElementById("approvalDenyBtn").onclick = () => {
    modal.classList.add("hidden");
    logTerminal("[USER]", "Action denied by user.", "log-err");
    setTelemetryStatus("DENIED", "status-err");
  };
}

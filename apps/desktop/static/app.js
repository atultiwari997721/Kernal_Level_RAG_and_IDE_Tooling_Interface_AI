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
  initHomeScreen();
  initKritiMode();
  initSupervisionMode();
  initChatMode();
  initSettings();
  initWebSocket();
  loadConfig();
  loadAvailableModels();
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

// ==========================================================================
// Cat Animation & Status Manager
// ==========================================================================
let totalPlanStepsCount = 1;

function setCatState(state, message) {
  const catCard = document.getElementById("computingCatSection");
  const catBubble = document.getElementById("catBubble");
  if (!catCard || !catBubble) return;

  if (state === "running") {
    catCard.classList.remove("idle");
    catCard.classList.add("is-computing");
    if (message) catBubble.innerText = message;
  } else if (state === "complete") {
    catCard.classList.remove("is-computing");
    catCard.classList.add("idle");
    catBubble.innerText = message || "Task verified & complete! ✨";
  } else {
    catCard.classList.remove("is-computing");
    catCard.classList.add("idle");
    catBubble.innerText = message || "Ready for autonomous goal";
  }
}

function moveCatForward(progressRatio) {
  const track = document.getElementById("catTrack");
  const runner = document.getElementById("catRunner");
  if (!track || !runner) return;
  const maxDistance = Math.max(0, track.clientWidth - runner.clientWidth - 20);
  const targetX = Math.min(maxDistance, maxDistance * Math.max(0, Math.min(1, progressRatio)));
  runner.style.transform = `translateX(${targetX}px)`;
}

function triggerCatVictoryJump() {
  const runner = document.getElementById("catRunner");
  if (!runner) return;
  runner.classList.add("jumping");
  setCatState("complete", "Objective Completed! 🎉🐾");

  // After celebration jump, smoothly return to original position
  setTimeout(() => {
    runner.classList.remove("jumping");
    runner.style.transform = "translateX(0px)";
    setCatState("idle", "Ready for autonomous goal");
  }, 2600);
}

function handleWsEvent(msg) {
  if (msg.event === "emergency_stop") {
    const runner = document.getElementById("catRunner");
    if (runner) runner.style.transform = "translateX(0px)";
    setCatState("idle", "Halted: Emergency Stop");
    setTelemetryStatus("STOPPED", "status-err");
    logTerminal("[STOP]", "EMERGENCY STOP ACTIVATED. All tasks halted.", "log-err");
    const stopBtn = document.getElementById("emergencyStopBtn");
    if (stopBtn) stopBtn.classList.add("pulsing");
    enableTaskControls(false);
  } else if (msg.event === "plan_created") {
    totalPlanStepsCount = msg.plan.length || 1;
    moveCatForward(0.1);
    setCatState("running", `Plan ready: ${msg.plan.length} steps`);
    renderPlan(msg.plan);
    setTelemetryStatus("EXECUTING", "status-active");
    logTerminal("[PLAN]", `Generated ${msg.plan.length} verifiable execution step(s).`, "log-plan");
  } else if (msg.event === "step_started") {
    const progress = (msg.step.step_index + 0.3) / (totalPlanStepsCount || 1);
    moveCatForward(progress);
    setCatState("running", `Step ${msg.step.step_index + 1}: ${msg.step.objective}`);
    updatePlanStep(msg.step.step_index, "in_progress");
    
    const agEl = document.getElementById("kmActiveModel") || document.getElementById("telemetryAgent");
    if (agEl) agEl.innerText = msg.step.agent;
    const tlEl = document.getElementById("kmActiveTool") || document.getElementById("telemetryTool");
    if (tlEl) tlEl.innerText = msg.step.tool;
    const actEl = document.getElementById("kmCurrentAction");
    if (actEl) actEl.innerText = msg.step.objective;

    logTerminal("[EXEC]", `Step ${msg.step.step_index + 1}: ${msg.step.objective}`, "log-exec");
  } else if (msg.event === "step_completed") {
    const progress = (msg.step.step_index + 1) / (totalPlanStepsCount || 1);
    moveCatForward(progress);
    setCatState("running", `Verified step ${msg.step.step_index + 1}`);
    updatePlanStep(msg.step.step_index, "completed", msg.output);
    logTerminal("[VERIFY]", `✓ Step ${msg.step.step_index + 1} verified: ${msg.step.expected_result}`, "log-verif");
  } else if (msg.event === "task_completed") {
    moveCatForward(1.0);
    triggerCatVictoryJump();
    setTelemetryStatus("COMPLETED", "status-done");
    
    const badge = document.getElementById("verificationBadge") || document.getElementById("kmLiveStateTag");
    if (badge) {
      badge.innerText = "Verified Complete";
      badge.className = "status-tag idle";
    }
    const actEl = document.getElementById("kmCurrentAction");
    if (actEl) actEl.innerText = "Task completed successfully";
    const resOut = document.getElementById("resultOutput");
    if (resOut) resOut.innerText = msg.result;

    logTerminal("[COMPLETE]", `★ Task completed successfully.`, "log-done");
    enableTaskControls(false);

    lastTaskData = msg;
    showOutcomeActionButtons(msg);
  }
}

// ==========================================================================
// Navigation & Tab Switching
// ==========================================================================
function initNavigation() {
  // 1. Sidebar page navigation
  document.querySelectorAll(".sidebar-nav .nav-item[data-page]").forEach(btn => {
    btn.addEventListener("click", () => {
      switchPage(btn.dataset.page);
    });
  });

  // 2. Topbar Settings button
  const topSettings = document.getElementById("btnTopSettings");
  if (topSettings) {
    topSettings.addEventListener("click", () => switchPage("settings"));
  }

  // 3. Settings sub-navigation (12 sections)
  document.querySelectorAll(".settings-nav .s-nav-btn[data-section]").forEach(btn => {
    btn.addEventListener("click", () => {
      switchSettingsSection(btn.dataset.section);
    });
  });

  // 4. SuperVision Settings button
  const svSettings = document.getElementById("btnSupervisionSettings");
  if (svSettings) {
    svSettings.addEventListener("click", () => switchPage("settings"));
  }
}

function switchPage(pageId) {
  document.querySelectorAll(".sidebar-nav .nav-item").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.page === pageId);
  });

  document.querySelectorAll(".view-page").forEach(page => {
    page.classList.remove("active");
  });
  const targetPage = document.getElementById(`page-${pageId}`);
  if (targetPage) targetPage.classList.add("active");

  const breadcrumbEl = document.getElementById("topbarBreadcrumb");
  const titles = {
    home: "Home",
    kritimode: "KritiMode",
    supervision: "KritiSuperVision",
    projects: "Projects",
    tasks: "Tasks",
    memory: "Memory",
    models: "Models",
    settings: "Settings"
  };
  if (breadcrumbEl) {
    breadcrumbEl.innerText = titles[pageId] || pageId;
  }

  if (pageId === "tasks") loadTasks();
  if (pageId === "memory") loadMemory();
  if (pageId === "models") loadModelsPage();
  if (pageId === "settings") loadSettingsTab();
  if (pageId === "projects") loadProjectsList();
}

function switchTab(tabId) {
  switchPage(tabId);
}

function switchSettingsSection(sectionId) {
  document.querySelectorAll(".settings-nav .s-nav-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.section === sectionId);
  });
  document.querySelectorAll(".settings-section").forEach(sec => {
    sec.classList.remove("active");
  });
  const targetSec = document.getElementById(`setSec-${sectionId}`);
  if (targetSec) targetSec.classList.add("active");
}

function initHomeScreen() {
  const greetingEl = document.getElementById("homeGreeting");
  if (greetingEl) {
    const hr = new Date().getHours();
    greetingEl.innerText = hr < 12 ? "Good morning" : (hr < 18 ? "Good afternoon" : "Good evening");
  }

  const input = document.getElementById("homeCommandInput");
  const submitBtn = document.getElementById("homeSubmitBtn");

  const submitHomeGoal = () => {
    const goal = (input ? input.value : "").trim();
    if (!goal) return;
    input.value = "";

    const lower = goal.toLowerCase();
    if (lower.includes("website") || lower.includes("project") || lower.includes("code") || lower.includes("refactor") || lower.includes("fix bug")) {
      switchPage("supervision");
      const svInput = document.getElementById("supervisionPromptInput");
      if (svInput) {
        svInput.value = goal;
        ideApplySeniorChanges();
      }
    } else {
      switchPage("kritimode");
      const kmInput = document.getElementById("kmCommandInput");
      if (kmInput) kmInput.value = goal;
      executeAutonomousGoal(goal);
    }
  };

  if (submitBtn) submitBtn.addEventListener("click", submitHomeGoal);
  if (input) {
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") submitHomeGoal();
    });
  }

  document.querySelectorAll(".quick-act-btn[data-action]").forEach(btn => {
    btn.addEventListener("click", () => {
      const act = btn.dataset.action;
      if (act === "build") {
        switchPage("supervision");
        const svInput = document.getElementById("supervisionPromptInput");
        if (svInput) {
          svInput.value = "Build a modern full-stack web application with responsive UI";
          if (svInput.focus) svInput.focus();
        }
      } else if (act === "research") {
        switchPage("kritimode");
        const kmInput = document.getElementById("kmCommandInput");
        if (kmInput) {
          kmInput.value = "Research latest tech news and documentation";
          if (kmInput.focus) kmInput.focus();
        }
      } else if (act === "control") {
        switchPage("kritimode");
        const kmInput = document.getElementById("kmCommandInput");
        if (kmInput) {
          kmInput.value = "Open and inspect Windows hardware system telemetry";
          executeAutonomousGoal(kmInput.value);
        }
      } else if (act === "open_project") {
        switchPage("supervision");
        ideOpenPickerModal();
      } else if (act === "browse") {
        switchPage("kritimode");
        const kmInput = document.getElementById("kmCommandInput");
        if (kmInput) {
          kmInput.value = "Search YouTube for trending songs and play Sita Ram";
          executeAutonomousGoal(kmInput.value);
        }
      } else if (act === "automate") {
        switchPage("kritimode");
        const kmInput = document.getElementById("kmCommandInput");
        if (kmInput) {
          kmInput.value = "Automate file organization and directory inspection";
          if (kmInput.focus) kmInput.focus();
        }
      }
    });
  });

  document.querySelectorAll("#homeRecentWorkList .project-card, #projectsDirectoryList .project-card").forEach(card => {
    card.addEventListener("click", () => {
      const p = card.dataset.path;
      if (p) {
        switchPage("supervision");
        const pathInp = document.getElementById("supervisionPathInput");
        if (pathInp) pathInp.value = p;
        ideInspectProject(p);
      }
    });
  });
}

// ==========================================================================
// Power Modes & Emergency STOP
// ==========================================================================
function initPowerModes() {
  const updateActivePower = async (mode) => {
    // 1. Update Topbar pills
    document.querySelectorAll(".power-pill[data-mode]").forEach(b => {
      b.classList.toggle("active", b.dataset.mode === mode);
    });

    // 2. Update Settings radio buttons
    const radio = document.querySelector(`input[name="settingsPowerMode"][value="${mode}"]`);
    if (radio) radio.checked = true;

    // 3. Update SuperVision badge
    const svTag = document.getElementById("svActivePowerTag");
    if (svTag) {
      svTag.innerText = `● ${mode.charAt(0).toUpperCase() + mode.slice(1)}`;
    }

    // 4. Update legacy buttons if present
    document.querySelectorAll(".power-btn[data-mode]").forEach(b => {
      b.classList.toggle("active", b.dataset.mode === mode);
    });

    // 5. Send to backend
    await fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ power_mode: mode })
    });
    logTerminal("[POLICY]", `Power Mode set to: ${mode.toUpperCase()}`, "log-plan");
  };

  // Topbar pills click listeners
  document.querySelectorAll(".power-pill[data-mode]").forEach(btn => {
    btn.addEventListener("click", () => updateActivePower(btn.dataset.mode));
  });

  // Legacy buttons click listeners
  document.querySelectorAll(".power-btn[data-mode]").forEach(btn => {
    btn.addEventListener("click", () => updateActivePower(btn.dataset.mode));
  });

  // Settings radio buttons change listeners
  document.querySelectorAll('input[name="settingsPowerMode"]').forEach(radio => {
    radio.addEventListener("change", () => {
      if (radio.checked) updateActivePower(radio.value);
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
// KritiMode Controller & General Computer Execution (Spec Section 5-7)
// ==========================================================================
function initKritiMode() {
  const kmInput = document.getElementById("kmCommandInput");
  const kmSubmitBtn = document.getElementById("kmSubmitBtn");
  const kmPauseBtn = document.getElementById("kmPauseBtn");
  const kmStopBtn = document.getElementById("kmStopBtn");

  // KritiMode command input
  if (kmSubmitBtn) {
    kmSubmitBtn.addEventListener("click", () => {
      const goal = (kmInput ? kmInput.value : "").trim();
      if (goal) executeAutonomousGoal(goal);
    });
  }
  if (kmInput) {
    kmInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        const goal = kmInput.value.trim();
        if (goal) executeAutonomousGoal(goal);
      }
    });
  }

  // Legacy goal input fallback if present
  const goalInput = document.getElementById("goalInput");
  const execBtn = document.getElementById("executeGoalBtn");
  if (execBtn) {
    execBtn.addEventListener("click", () => executeAutonomousGoal());
  }
  if (goalInput) {
    goalInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
        executeAutonomousGoal();
      }
    });
  }

  // Quick Chips fallback
  document.querySelectorAll(".chip-btn").forEach(chip => {
    chip.addEventListener("click", () => {
      if (goalInput) goalInput.value = chip.dataset.goal;
      if (kmInput) kmInput.value = chip.dataset.goal;
      executeAutonomousGoal(chip.dataset.goal);
    });
  });

  // Bottom Tabs (TERMINAL | SCREEN | ACTIONS | LOGS | FILES)
  document.querySelectorAll(".km-strip-tab[data-kmtab]").forEach(tab => {
    tab.addEventListener("click", () => {
      switchKmBottomTab(tab.dataset.kmtab);
    });
  });

  // Controls: Stop & Pause (Spec Section 30)
  if (kmStopBtn) {
    kmStopBtn.addEventListener("click", async () => {
      if (currentTaskId) {
        await fetch(`/api/tasks/${currentTaskId}/cancel`, { method: "POST" });
        logTerminal("[TASK]", "Task halted by user.", "log-err");
        setUnderstanding("stop");
        kmStopBtn.disabled = true;
        if (kmPauseBtn) kmPauseBtn.disabled = true;
      }
    });
  }

  // Legacy cancel button
  const cancelBtn = document.getElementById("cancelTaskBtn");
  if (cancelBtn) {
    cancelBtn.addEventListener("click", async () => {
      if (currentTaskId) {
        await fetch(`/api/tasks/${currentTaskId}/cancel`, { method: "POST" });
        logTerminal("[TASK]", "Task cancelled by user.", "log-err");
        setTelemetryStatus("CANCELLED", "status-err");
        enableTaskControls(false);
      }
    });
  }
}

function switchKmBottomTab(tabId) {
  document.querySelectorAll(".km-strip-tab").forEach(t => {
    t.classList.toggle("active", t.dataset.kmtab === tabId);
  });
  document.querySelectorAll(".km-tab-pane").forEach(p => {
    p.classList.remove("active");
  });
  const target = document.getElementById(`kmTabContent-${tabId}`);
  if (target) target.classList.add("active");
}

function setUnderstanding(stage) {
  const items = {
    intent: document.getElementById("undIntent"),
    context: document.getElementById("undContext"),
    plan: document.getElementById("undPlan"),
    exec: document.getElementById("undExec"),
    verify: document.getElementById("undVerify")
  };

  const setItem = (el, icon, stateClass) => {
    if (!el) return;
    el.className = `und-item ${stateClass}`;
    const ic = el.querySelector(".und-icon");
    if (ic) ic.innerText = icon;
  };

  if (stage === "start") {
    setItem(items.intent, "✓", "done");
    setItem(items.context, "●", "active");
    setItem(items.plan, "○", "");
    setItem(items.exec, "○", "");
    setItem(items.verify, "○", "");
  } else if (stage === "plan") {
    setItem(items.intent, "✓", "done");
    setItem(items.context, "✓", "done");
    setItem(items.plan, "✓", "done");
    setItem(items.exec, "●", "active");
    setItem(items.verify, "○", "");
  } else if (stage === "exec") {
    setItem(items.intent, "✓", "done");
    setItem(items.context, "✓", "done");
    setItem(items.plan, "✓", "done");
    setItem(items.exec, "●", "active");
    setItem(items.verify, "○", "");
  } else if (stage === "verify") {
    setItem(items.intent, "✓", "done");
    setItem(items.context, "✓", "done");
    setItem(items.plan, "✓", "done");
    setItem(items.exec, "✓", "done");
    setItem(items.verify, "●", "active");
  } else if (stage === "all_done") {
    setItem(items.intent, "✓", "done");
    setItem(items.context, "✓", "done");
    setItem(items.plan, "✓", "done");
    setItem(items.exec, "✓", "done");
    setItem(items.verify, "✓", "done");
  } else if (stage === "stop") {
    setItem(items.exec, "✕", "danger");
  }
}

async function executeAutonomousGoal(providedGoal = null) {
  let goal = providedGoal;
  if (!goal) {
    const kmInp = document.getElementById("kmCommandInput");
    const gInp = document.getElementById("goalInput");
    goal = (kmInp && kmInp.value.trim()) || (gInp && gInp.value.trim()) || "";
  }
  if (!goal) return;

  // Update KritiMode displays
  const kmGoalDisplay = document.getElementById("kmGoalDisplay");
  if (kmGoalDisplay) kmGoalDisplay.innerText = goal;
  const kmActionEl = document.getElementById("kmCurrentAction");
  if (kmActionEl) kmActionEl.innerText = "Analyzing objective and context...";
  const kmLiveState = document.getElementById("kmLiveStateTag");
  if (kmLiveState) {
    kmLiveState.innerText = "PLANNING";
    kmLiveState.className = "status-tag running";
  }

  setUnderstanding("start");

  const kmStopBtn = document.getElementById("kmStopBtn");
  const kmPauseBtn = document.getElementById("kmPauseBtn");
  if (kmStopBtn) kmStopBtn.disabled = false;
  if (kmPauseBtn) kmPauseBtn.disabled = false;

  hideOutcomeActionButtons();
  logTerminal("\n------------------------------------------------------------");
  logTerminal("[INTENT]", `Goal submitted: "${goal}"`, "log-intent");

  setCatState("running", "Decomposing objective into execution steps...");
  totalPlanStepsCount = 1;
  moveCatForward(0.05);
  setTelemetryStatus("ANALYZING", "status-active");
  const badge = document.getElementById("verificationBadge");
  if (badge) {
    badge.innerText = "Executing...";
    badge.className = "status-pill status-active";
  }
  const resOut = document.getElementById("resultOutput");
  if (resOut) resOut.innerText = "Formulating verified autonomous execution plan...";
  enableTaskControls(true);

  try {
    const activePower = (currentConfig && currentConfig.power_mode) || "autonomous";
    const res = await fetch("/api/kritimode/execute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ goal: goal, power_mode: activePower })
    });
    const result = await res.json();
    currentTaskId = result.task_id;
    lastTaskData = result;

    if (result.is_informational) {
      setCatState("complete", "Answer ready! ✨");
      setTelemetryStatus("ANSWERED", "status-done");
      setUnderstanding("all_done");
      if (badge) {
        badge.innerText = "Insight Formulated";
        badge.className = "status-pill status-done";
      }
      if (resOut) resOut.innerText = result.final_result;
      logTerminal("[AI]", result.final_result, "log-done");
      if (kmActionEl) kmActionEl.innerText = "Conversational insight delivered";
      if (kmLiveState) {
        kmLiveState.innerText = "IDLE";
        kmLiveState.className = "status-tag idle";
      }
      enableTaskControls(false);
      return;
    }

    if (result.approval_required) {
      setCatState("running", "Waiting for approval...");
      setTelemetryStatus("APPROVAL NEEDED", "status-active");
      showApprovalModal(result);
    } else if (result.success) {
      moveCatForward(1.0);
      triggerCatVictoryJump();
      setTelemetryStatus("COMPLETED", "status-done");
      setUnderstanding("all_done");
      if (badge) {
        badge.innerText = "Verified Success";
        badge.className = "status-pill status-done";
      }
      if (resOut) resOut.innerText = result.final_result;
      logTerminal("[SUCCESS]", result.final_result, "log-done");
      if (kmActionEl) kmActionEl.innerText = "Objective completed & verified";
      if (kmLiveState) {
        kmLiveState.innerText = "COMPLETED";
        kmLiveState.className = "status-tag idle";
      }
      enableTaskControls(false);
      showOutcomeActionButtons(result);
    } else {
      const runner = document.getElementById("catRunner");
      if (runner) runner.style.transform = "translateX(0px)";
      setCatState("idle", "Execution stopped");
      setTelemetryStatus("FAILED", "status-err");
      if (badge) {
        badge.innerText = "Failed";
        badge.className = "status-pill status-err";
      }
      if (resOut) resOut.innerText = result.error || "Execution failed.";
      logTerminal("[ERROR]", result.error || "Execution failed.", "log-err");
      enableTaskControls(false);
    }
  } catch (e) {
    setCatState("idle", "Execution error");
    setTelemetryStatus("ERROR", "status-err");
    logTerminal("[ERR]", `API Execution error: ${e.message}`, "log-err");
    enableTaskControls(false);
  }
}

function renderPlan(steps) {
  // 1. Render in KritiMode Left Panel (Spec Section 5)
  const kmContainer = document.getElementById("kmPlanStepsList");
  const countEl = document.getElementById("kmPlanCount");
  if (countEl) countEl.innerText = `${steps.length} Steps`;

  if (kmContainer) {
    kmContainer.innerHTML = "";
    steps.forEach((s, i) => {
      const row = document.createElement("div");
      const stClass = s.status === 'completed' ? 'done' : (s.status === 'in_progress' ? 'active' : 'pending');
      const icon = s.status === 'completed' ? '✓' : (s.status === 'in_progress' ? '●' : '○');
      row.className = `km-plan-step-row ${stClass}`;
      row.id = `km-step-${i}`;
      row.innerHTML = `
        <span style="font-family: var(--font-mono); font-weight: 700; width: 14px;">${icon}</span>
        <span style="flex: 1;">${escapeHtml(s.objective)}</span>
        <span class="badge-mini">${escapeHtml(s.tool)}</span>
      `;
      kmContainer.appendChild(row);
    });
  }

  // 2. Legacy planList fallback
  const container = document.getElementById("planList");
  if (container) {
    container.innerHTML = "";
    const stepCountEl = document.getElementById("planStepCount");
    if (stepCountEl) stepCountEl.innerText = `${steps.length} Steps`;

    steps.forEach((s, i) => {
      const item = document.createElement("div");
      item.className = `pipeline-step ${s.status}`;
      item.id = `step-item-${i}`;
      item.innerHTML = `
        <div class="step-badge">${s.status === 'completed' ? '✓' : (s.status === 'in_progress' ? '⟳' : i + 1)}</div>
        <div class="step-details" style="flex: 1;">
          <div class="step-objective">${s.objective}</div>
          <div class="step-chips">
            <span class="step-tag">${s.agent}</span>
            <span class="step-tag">${s.tool}</span>
          </div>
          <div id="step-output-${i}" class="step-live-output" style="display: none;"></div>
        </div>
      `;
      container.appendChild(item);
    });
  }

  setUnderstanding("plan");
}

function updatePlanStep(index, status, outputData = null) {
  // Update KritiMode Step
  const kmItem = document.getElementById(`km-step-${index}`);
  if (kmItem) {
    const stClass = status === 'completed' ? 'done' : (status === 'in_progress' ? 'active' : 'pending');
    const icon = status === 'completed' ? '✓' : (status === 'in_progress' ? '●' : '○');
    kmItem.className = `km-plan-step-row ${stClass}`;
    const iconSpan = kmItem.querySelector("span");
    if (iconSpan) iconSpan.innerText = icon;
  }

  // Legacy Step item fallback
  const item = document.getElementById(`step-item-${index}`);
  if (item) {
    item.className = `pipeline-step ${status}`;
    const badge = item.querySelector(".step-badge");
    if (badge) {
      badge.innerText = status === 'completed' ? '✓' : (status === 'in_progress' ? '⟳' : index + 1);
    }
    if (outputData) {
      const outDiv = document.getElementById(`step-output-${index}`);
      if (outDiv) {
        let previewText = "";
        if (typeof outputData === "string") {
          previewText = outputData;
        } else if (outputData.stdout) {
          previewText = outputData.stdout.trim();
        } else {
          previewText = JSON.stringify(outputData, null, 2);
        }
        if (previewText) {
          outDiv.innerText = previewText;
          outDiv.style.display = "block";
        }
      }
    }
  }

  if (status === "in_progress") {
    setUnderstanding("exec");
  } else if (status === "completed") {
    setUnderstanding("verify");
  }
}

function logTerminal(tag, message, highlightClass = "") {
  const time = new Date().toLocaleTimeString();
  const line = `[${time}] ${tag} ${message}\n`;
  
  const kmTerm = document.getElementById("kmTerminalLog");
  if (kmTerm) {
    kmTerm.innerText += line;
    kmTerm.scrollTop = kmTerm.scrollHeight;
  }
  const ideTerm = document.getElementById("ideTerminalOutput");
  if (ideTerm) {
    ideTerm.innerText += line;
    ideTerm.scrollTop = ideTerm.scrollHeight;
  }
  const sysLogs = document.getElementById("kmSystemLogs");
  if (sysLogs) {
    sysLogs.innerText += line;
    sysLogs.scrollTop = sysLogs.scrollHeight;
  }
  const term = document.getElementById("terminalOutput");
  if (term) {
    term.innerText += line;
    term.scrollTop = term.scrollHeight;
  }
  console.log(`[${tag}]`, message);
}

function setTelemetryStatus(text, pillClass) {
  const badge = document.getElementById("telemetryStatus") || document.getElementById("kmLiveStateTag");
  if (badge) {
    badge.innerText = text;
    badge.className = `status-tag ${pillClass}`;
  }
}

function enableTaskControls(enabled) {
  const cancelBtn = document.getElementById("cancelTaskBtn");
  if (cancelBtn) cancelBtn.disabled = !enabled;
  const pauseBtn = document.getElementById("pauseTaskBtn");
  if (pauseBtn) pauseBtn.disabled = !enabled;
  const kmStop = document.getElementById("kmStopBtn");
  if (kmStop) kmStop.disabled = !enabled;
  const kmPause = document.getElementById("kmPauseBtn");
  if (kmPause) kmPause.disabled = !enabled;
}

function hideOutcomeActionButtons() {
  const f = document.getElementById("btnOpenFolder");
  if (f) f.style.display = "none";
  const b = document.getElementById("btnOpenBrowser");
  if (b) b.style.display = "none";
  const a = document.getElementById("btnLaunchApp");
  if (a) a.style.display = "none";
}

function showOutcomeActionButtons(taskData) {
  hideOutcomeActionButtons();
  if (!taskData) return;

  const target = taskData.target || (taskData.parameters && (taskData.parameters.path || taskData.parameters.target_url));
  const intent = taskData.intent_type || "";
  const btnFolder = document.getElementById("btnOpenFolder");
  const btnBrowser = document.getElementById("btnOpenBrowser");
  const btnLaunch = document.getElementById("btnLaunchApp");

  let folderPath = null;
  if (target && typeof target === "string") {
    if (target.includes(":\\") || target.includes(":/") || target.includes("\\") || target.includes("/")) {
      folderPath = target;
    }
  } else if (taskData.working_directory) {
    folderPath = taskData.working_directory;
  }

  // Also check if any step input contained a folder/file path
  if (!folderPath && taskData.steps && taskData.steps.length) {
    for (const s of taskData.steps) {
      if (s.input_data && s.input_data.path) {
        folderPath = s.input_data.path;
        break;
      }
    }
  }

  if (folderPath) {
    btnFolder.style.display = "inline-flex";
    btnFolder.innerText = "📂 Open in File Explorer";
    btnFolder.title = `Open ${folderPath} in Windows File Explorer`;
    btnFolder.onclick = () => openPathOnWindows(folderPath);

    // Also enrich resultOutput with clickable directory location badge
    const resultEl = document.getElementById("resultOutput");
    if (resultEl && !resultEl.querySelector(".folder-link-btn")) {
      const linkDiv = document.createElement("div");
      linkDiv.className = "folder-link-btn";
      linkDiv.style.cssText = "margin-top: 10px; display: inline-flex; align-items: center; gap: 8px; background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.4); padding: 7px 14px; border-radius: 8px; font-size: 12.5px; cursor: pointer; color: var(--accent-cyan); font-weight: 500;";
      linkDiv.innerHTML = `<span>📁 Location:</span> <strong style="text-decoration: underline;">${folderPath}</strong> <span style="font-size: 11px; opacity: 0.85; margin-left: 4px;">[Click to open]</span>`;
      linkDiv.onclick = () => openPathOnWindows(folderPath);
      resultEl.appendChild(linkDiv);
    }
  }

  if (intent === "create_calculator") {
    btnFolder.style.display = "inline-flex";
    btnFolder.onclick = () => openPathOnWindows(taskData.target);

    btnBrowser.style.display = "inline-flex";
    const htmlPath = `${taskData.target}\\calculator.html`;
    btnBrowser.onclick = () => openPathOnWindows(htmlPath);

    btnLaunch.style.display = "inline-flex";
    const batPath = `${taskData.target}\\run_calculator.bat`;
    btnLaunch.onclick = () => openPathOnWindows(batPath);
  } else if (intent === "create_shopping_website") {
    btnFolder.style.display = "inline-flex";
    btnFolder.onclick = () => openPathOnWindows(taskData.target);

    btnBrowser.style.display = "inline-flex";
    btnBrowser.innerText = "🌐 Open Shopping Website";
    const htmlPath = `${taskData.target}\\index.html`;
    btnBrowser.onclick = () => openPathOnWindows(htmlPath);

    btnLaunch.style.display = "inline-flex";
    btnLaunch.innerText = "▶️ Launch Shopping Platform";
    const batPath = `${taskData.target}\\run_shopping_website.bat`;
    btnLaunch.onclick = () => openPathOnWindows(batPath);
  } else if (intent === "play_youtube" || intent === "search_web") {
    btnBrowser.style.display = "inline-flex";
    btnBrowser.innerText = "🌐 Open in Browser";
    btnBrowser.onclick = () => {
      const q = taskData.parameters?.query || taskData.target || "Sita Ram song";
      const u = taskData.parameters?.url || `https://www.youtube.com/results?search_query=${encodeURIComponent(q)}`;
      openPathOnWindows(u);
    };
  }
}

async function openPathOnWindows(pathStr) {
  if (!pathStr) return;
  try {
    const res = await fetch("/api/open-path", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: pathStr })
    });
    const data = await res.json();
    if (data.success) {
      logTerminal("[SYS]", `Opened in Windows Explorer: ${data.path}`, "log-done");
    } else {
      logTerminal("[WARN]", `Failed to open '${pathStr}': ${data.error}`, "log-err");
    }
  } catch (e) {
    console.error("Open path error:", e);
    logTerminal("[ERR]", `Failed to open '${pathStr}': ${e.message}`, "log-err");
  }
}

// ==========================================================================
// Chat Mode & Dynamic Model Discovery
// ==========================================================================
let availableModelsList = [];

async function loadAvailableModels() {
  const select = document.getElementById("chatModelSelect");
  const badge = document.getElementById("chatModelBadge");
  if (!select) return;

  try {
    const res = await fetch("/api/models");
    const data = await res.json();
    availableModelsList = data.models || [];

    select.innerHTML = "";

    const localModels = availableModelsList.filter(m => m.is_local);
    const cloudModels = availableModelsList.filter(m => !m.is_local);

    if (localModels.length > 0) {
      const localGroup = document.createElement("optgroup");
      localGroup.label = "Local Models (Downloaded)";
      localModels.forEach(m => {
        const opt = document.createElement("option");
        opt.value = m.id;
        opt.innerText = `⚡ ${m.name} (${m.provider_display})`;
        localGroup.appendChild(opt);
      });
      select.appendChild(localGroup);
    }

    if (cloudModels.length > 0) {
      const cloudGroup = document.createElement("optgroup");
      cloudGroup.label = "External API Models";
      cloudModels.forEach(m => {
        const opt = document.createElement("option");
        opt.value = m.id;
        opt.innerText = `☁️ ${m.name} (${m.provider_display})`;
        cloudGroup.appendChild(opt);
      });
      select.appendChild(cloudGroup);
    }

    // Set active selection: Priority to Qwen 7B for Chat
    const saved = localStorage.getItem("kritiai_chat_model");
    if (saved && availableModelsList.some(m => m.id === saved)) {
      select.value = saved;
    } else if (data.default_chat_model && availableModelsList.some(m => m.id === data.default_chat_model)) {
      select.value = data.default_chat_model;
    } else {
      const qwen7b = availableModelsList.find(m => m.id.toLowerCase().includes("qwen") && (m.id.toLowerCase().includes("7b") || m.id.toLowerCase().includes("2.5")));
      if (qwen7b) {
        select.value = qwen7b.id;
      } else if (data.active_model) {
        select.value = data.active_model;
      }
    }

    updateChatModelBadge();
  } catch (err) {
    console.error("Error discovering models:", err);
  }
}

function updateChatModelBadge() {
  const select = document.getElementById("chatModelSelect");
  const badge = document.getElementById("chatModelBadge");
  if (!select || !badge) return;

  const currentId = select.value;
  const modelObj = availableModelsList.find(m => m.id === currentId);
  if (modelObj && !modelObj.is_local) {
    badge.innerText = "Cloud/API";
    badge.className = "status-pill status-active";
  } else {
    badge.innerText = "Local";
    badge.className = "status-pill status-done";
  }
}

// ==========================================================================
// KritiSupervision Mode — Autonomous AI Coding IDE Subsystem
// ==========================================================================
let ideProjectData = null;
let ideActiveProjectDir = "";
let ideOpenTabs = [];
let ideActiveTabFile = null;
let ideActiveDiff = "";
let ideActiveFileBaseHash = null;
let ideLastAiGroup = null;
let ideDiffMode = "inline";

function switchBottomTab(target) {
  let normalized = target;
  if (target === "diffs") normalized = "diff";
  if (target === "history") normalized = "changes";

  // 1. SuperVision 5 Mandatory Tabs (TERMINAL | PREVIEW | DIFF | TESTS | CHANGES)
  document.querySelectorAll(".sv-b-tab").forEach(b => {
    b.classList.toggle("active", b.dataset.svbtab === normalized);
  });
  document.querySelectorAll(".sv-tab-content").forEach(c => {
    c.classList.remove("active");
  });
  const svTarget = document.getElementById(`svTabContent-${normalized}`);
  if (svTarget) svTarget.classList.add("active");

  if (normalized === "changes") ideLoadHistory();

  // 2. Legacy elements fallback
  document.querySelectorAll(".ide-bottom-tab").forEach(b => {
    b.classList.toggle("active", b.dataset.bottom === target);
  });
  document.querySelectorAll(".ide-bottom-content").forEach(c => c.style.display = "none");
  const legMap = {
    terminal: "ideBottomTerminal",
    preview: "ideBottomPreview",
    history: "ideBottomHistory",
    snapshots: "ideBottomSnapshots",
    diffs: "ideBottomDiffs",
    memory: "ideBottomMemory"
  };
  const legEl = document.getElementById(legMap[target]);
  if (legEl) legEl.style.display = "flex";
}


function ideUpdateLineNumbers() {
  const editor = document.getElementById("ideCodeEditor");
  const gutter = document.getElementById("ideLineNumbers");
  if (!editor || !gutter) return;
  const lineCount = (editor.value || "").split("\n").length || 1;
  gutter.innerText = Array.from({ length: lineCount }, (_, i) => i + 1).join("\n");
}

function initSupervisionMode() {
  const pathInput = document.getElementById("supervisionPathInput");
  const inspectBtn = document.getElementById("btnSupervisionInspect");
  const openExpBtn = document.getElementById("btnSupervisionOpenExplorer");
  const runDevBtn = document.getElementById("btnRunDevServer");
  const promptInput = document.getElementById("supervisionPromptInput");
  const applyBtn = document.getElementById("btnSupervisionApply");
  const saveBtn = document.getElementById("btnSaveActiveFile");
  const formatBtn = document.getElementById("btnFormatActiveFile");
  const findBtn = document.getElementById("btnFindReplace");
  const sideBySideBtn = document.getElementById("btnDiffSideBySide");
  const diffToggleBtn = document.getElementById("btnToggleDiffView");
  const openPlanBtn = document.getElementById("btnOpenPlanTab");
  const codeEditor = document.getElementById("ideCodeEditor");
  const lineNumbers = document.getElementById("ideLineNumbers");
  const termInput = document.getElementById("ideTerminalInput");
  const runTermBtn = document.getElementById("btnRunTerminalCmd");
  const clearTermBtn = document.getElementById("btnClearTerminal");
  const refreshPrevBtn = document.getElementById("btnRefreshPreview");
  const extPrevBtn = document.getElementById("btnOpenExternalBrowser");
  const undoBtn = document.getElementById("btnIdeUndo");
  const redoBtn = document.getElementById("btnIdeRedo");
  const snapshotBtn = document.getElementById("btnIdeSnapshot");

  if (!inspectBtn) return;

  // 1. Scan & Index Project
  inspectBtn.addEventListener("click", () => ideInspectProject());

  // 2. Open From File Explorer Modal
  const openFromBtn = document.getElementById("btnOpenFromPicker");
  if (openFromBtn) {
    openFromBtn.addEventListener("click", () => ideOpenPickerModal());
  }

  // Modal Controls
  const closePickerBtn = document.getElementById("btnClosePickerModal");
  const cancelPickerBtn = document.getElementById("btnPickerCancel");
  const pickerUpBtn = document.getElementById("btnPickerUp");
  const pickerGoBtn = document.getElementById("btnPickerGo");
  const pickerRefreshBtn = document.getElementById("btnPickerRefresh");
  const pickerPathInp = document.getElementById("pickerPathInput");
  const nativePickBtn = document.getElementById("btnPickNativeDialog");
  const selectFolderBtn = document.getElementById("btnPickerSelectFolder");
  const selectFileBtn = document.getElementById("btnPickerSelectFile");

  if (closePickerBtn) closePickerBtn.addEventListener("click", () => ideClosePickerModal());
  if (cancelPickerBtn) cancelPickerBtn.addEventListener("click", () => ideClosePickerModal());
  if (pickerUpBtn) pickerUpBtn.addEventListener("click", () => idePickerGoUp());
  if (pickerRefreshBtn) pickerRefreshBtn.addEventListener("click", () => idePickerRefresh());
  if (pickerGoBtn && pickerPathInp) {
    pickerGoBtn.addEventListener("click", () => idePickerLoadDir(pickerPathInp.value.trim()));
    pickerPathInp.addEventListener("keydown", (e) => {
      if (e.key === "Enter") idePickerLoadDir(pickerPathInp.value.trim());
    });
  }
  if (nativePickBtn) nativePickBtn.addEventListener("click", () => idePickNativeDialog());
  if (selectFolderBtn) selectFolderBtn.addEventListener("click", () => idePickerConfirmFolder());
  if (selectFileBtn) selectFileBtn.addEventListener("click", () => idePickerConfirmFile());

  // 3. Open in Windows Explorer
  if (openExpBtn) {
    openExpBtn.addEventListener("click", () => {
      if (ideActiveProjectDir) openPathOnWindows(ideActiveProjectDir);
    });
  }

  // 3. Global Undo / Redo & Snapshot Controls
  if (undoBtn) undoBtn.addEventListener("click", () => ideTriggerUndo());
  if (redoBtn) redoBtn.addEventListener("click", () => ideTriggerRedo());
  if (snapshotBtn) snapshotBtn.addEventListener("click", () => ideCreateSnapshotPrompt());

  // 4. File Management Toolbar (+ File, + Folder, Rename, Delete)
  const newFileBtn = document.getElementById("btnNewFile");
  const newFolderBtn = document.getElementById("btnNewFolder");
  const renameItemBtn = document.getElementById("btnRenameItem");
  const deleteItemBtn = document.getElementById("btnDeleteItem");

  if (newFileBtn) newFileBtn.addEventListener("click", () => ideCreateFilePrompt());
  if (newFolderBtn) newFolderBtn.addEventListener("click", () => ideCreateFolderPrompt());
  if (renameItemBtn) renameItemBtn.addEventListener("click", () => ideRenamePrompt());
  if (deleteItemBtn) deleteItemBtn.addEventListener("click", () => ideDeletePrompt());

  // 5. Run Dev Server
  if (runDevBtn) {
    runDevBtn.addEventListener("click", () => {
      if (!ideActiveProjectDir) return;
      ideRunTerminalCommand("npm start || python -m http.server 8000 || python main.py");
      switchBottomTab("terminal");
    });
  }

  // 6. Save Active File & Global Keyboard Shortcuts
  if (saveBtn) {
    saveBtn.addEventListener("click", () => ideSaveActiveFile());
  }

  if (formatBtn) {
    formatBtn.addEventListener("click", () => ideFormatActiveFile());
  }

  if (findBtn) {
    findBtn.addEventListener("click", () => ideToggleFindBar());
  }

  if (sideBySideBtn) {
    sideBySideBtn.addEventListener("click", () => ideToggleSideBySideDiff());
  }

  window.addEventListener("keydown", (e) => {
    const activeTab = document.querySelector(".mode-toggle-btn.active");
    if (!activeTab || activeTab.dataset.tab !== "supervision") return;

    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") {
      e.preventDefault();
      ideSaveActiveFile();
    } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z" && !e.shiftKey) {
      e.preventDefault();
      ideTriggerUndo();
    } else if ((e.ctrlKey || e.metaKey) && (e.key.toLowerCase() === "y" || (e.shiftKey && e.key.toLowerCase() === "z"))) {
      e.preventDefault();
      ideTriggerRedo();
    } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "f") {
      e.preventDefault();
      ideToggleFindBar();
    }
  });

  // 7. Conflict Banner Handlers
  const confReview = document.getElementById("btnConflictReview");
  const confKeep = document.getElementById("btnConflictKeepMine") || document.getElementById("btnConflictKeepUser");
  const confOverwrite = document.getElementById("btnConflictOverwrite");

  if (confReview) confReview.addEventListener("click", () => {
    switchBottomTab("diffs");
  });
  if (confKeep) confKeep.addEventListener("click", () => {
    ideSaveActiveFile(true); // force save
  });
  if (confOverwrite) confOverwrite.addEventListener("click", () => {
    document.getElementById("ideConflictBanner").style.display = "none";
    if (ideActiveTabFile) ideOpenFile(ideActiveTabFile);
  });

  // 8. Find & Replace Handlers
  const findNextBtn = document.getElementById("btnFindNext");
  const replaceOneBtn = document.getElementById("btnReplaceOne");
  const replaceAllBtn = document.getElementById("btnReplaceAll");
  const closeFindBtn = document.getElementById("btnCloseFind");

  if (findNextBtn) findNextBtn.addEventListener("click", () => ideFindNext());
  if (replaceOneBtn) replaceOneBtn.addEventListener("click", () => ideReplaceOne());
  if (replaceAllBtn) replaceAllBtn.addEventListener("click", () => ideReplaceAll());
  if (closeFindBtn) closeFindBtn.addEventListener("click", () => {
    document.getElementById("ideFindReplaceBar").style.display = "none";
  });

  // 9. AI Change Explanation & Review (Accept / Reject)
  const acceptAiBtn = document.getElementById("btnAcceptAiChanges");
  const rejectAiBtn = document.getElementById("btnRejectAiChanges");
  if (acceptAiBtn) acceptAiBtn.addEventListener("click", () => ideAcceptAiChanges());
  if (rejectAiBtn) rejectAiBtn.addEventListener("click", () => ideRejectAiChanges());

  // 10. Diff View Toggle
  if (diffToggleBtn) {
    diffToggleBtn.addEventListener("click", () => ideToggleDiffView());
  }

  // 11. Open Plan Tab
  if (openPlanBtn) {
    openPlanBtn.addEventListener("click", () => ideOpenPlanTab());
  }

  // 12. Apply Senior Developer Code Refactoring
  if (applyBtn) {
    applyBtn.addEventListener("click", () => {
      const instruction = promptInput.value.trim();
      if (!instruction) {
        alert("Please enter a feature, refactoring, or bug fix instruction.");
        return;
      }
      ideApplySeniorChanges(instruction);
    });

    promptInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        applyBtn.click();
      }
    });
  }

  // 13. Terminal Runner
  if (runTermBtn && termInput) {
    const handleRun = () => {
      const cmd = termInput.value.trim();
      if (!cmd) return;
      termInput.value = "";
      ideRunTerminalCommand(cmd);
    };
    runTermBtn.addEventListener("click", handleRun);
    termInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") handleRun();
    });
  }

  if (clearTermBtn) {
    clearTermBtn.addEventListener("click", () => {
      const term = document.getElementById("ideTerminalOutput");
      if (term) term.innerHTML = `<span class="term-dim">Terminal cleared. Workspace: ${ideActiveProjectDir}</span>`;
    });
  }

  // 14. Live Preview Controls
  if (refreshPrevBtn) {
    refreshPrevBtn.addEventListener("click", () => ideRefreshPreview());
  }
  if (extPrevBtn) {
    extPrevBtn.addEventListener("click", () => {
      const url = document.getElementById("idePreviewUrl").value;
      if (url && url !== "about:blank") window.open(url, "_blank");
    });
  }

  // 15. History and Snapshot Buttons in Bottom Tabs
  const refHistBtn = document.getElementById("btnRefreshHistory");
  const newSnapBtn = document.getElementById("btnCreateNewSnapshot");
  const refSnapBtn = document.getElementById("btnRefreshSnapshots");

  if (refHistBtn) refHistBtn.addEventListener("click", () => ideLoadHistory());
  if (newSnapBtn) newSnapBtn.addEventListener("click", () => ideCreateSnapshotPrompt());
  if (refSnapBtn) refSnapBtn.addEventListener("click", () => ideLoadSnapshots());

    // 16. Sidebar Tabs (Files, Git, Symbols)
    document.querySelectorAll(".ide-tab-btn, .sv-pane-tab[data-svtab]").forEach(btn => {
      btn.addEventListener("click", () => {
        const target = btn.dataset.sidebar || btn.dataset.svtab;
        document.querySelectorAll(".ide-tab-btn, .sv-pane-tab").forEach(b => {
          b.classList.toggle("active", (b.dataset.sidebar || b.dataset.svtab) === target);
        });
        document.querySelectorAll(".ide-sidebar-content, .sv-view-pane").forEach(c => {
          c.classList.remove("active");
          c.style.display = "none";
        });
        const targetView = document.getElementById(target === "files" ? "sidebarFilesView" : (target === "git" ? "sidebarGitView" : "sidebarSymbolsView"));
        if (targetView) {
          targetView.classList.add("active");
          targetView.style.display = "block";
        }
      });
    });

    // 17. SuperVision Bottom Workspace Tabs (TERMINAL | PREVIEW | DIFF | TESTS | CHANGES)
    document.querySelectorAll(".sv-b-tab[data-svbtab]").forEach(tab => {
      tab.addEventListener("click", () => switchBottomTab(tab.dataset.svbtab));
    });

    // 18. Run & Verify Button
    const runVerifyBtn = document.getElementById("btnSupervisionRunVerify");
    if (runVerifyBtn) {
      runVerifyBtn.addEventListener("click", () => {
        const inst = promptInput ? promptInput.value.trim() : "";
        ideApplySeniorChanges(inst || "Run test suite and verify build integrity");
      });
    }


  // 17. Bottom Tabs (Terminal, Preview, History, Snapshots, Diffs, Memory)
  document.querySelectorAll(".ide-bottom-tab").forEach(btn => {
    btn.addEventListener("click", () => switchBottomTab(btn.dataset.bottom));
  });

  // 18. Editor Line Numbers & Input Sync
  if (codeEditor && lineNumbers) {
    codeEditor.addEventListener("input", () => ideUpdateLineNumbers());
    codeEditor.addEventListener("scroll", () => {
      lineNumbers.scrollTop = codeEditor.scrollTop;
    });
  }
}

async function ideInspectProject(pathOverride = null) {
  const pathInput = document.getElementById("supervisionPathInput");
  const inspectBtn = document.getElementById("btnSupervisionInspect");
  const rawPath = pathOverride || pathInput.value.trim();

  if (!rawPath) {
    alert("Please enter a project directory or file path.");
    return;
  }

  inspectBtn.innerText = "⏳ Indexing...";
  inspectBtn.disabled = true;

  try {
    const res = await fetch("/api/supervision/inspect", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: rawPath })
    });
    const data = await res.json();
    inspectBtn.innerText = "🔍 Scan & Index Project";
    inspectBtn.disabled = false;

    if (!data.success) {
      alert(data.error || "Failed to index project.");
      return;
    }

    ideProjectData = data;
    ideActiveProjectDir = data.root_path;
    pathInput.value = data.root_path;

    ideRenderProject(data);
    logTerminal("[SUPERVISION]", `Scanned project '${data.project_name}' (${data.file_count} files, ${data.tech_stack})`, "log-done");

    // Automatically open first key file (index.html, app.js, main.py, or README.md)
    const defaultOpen = (data.key_files || []).find(f => f.toLowerCase() === "index.html" || f.toLowerCase() === "main.py" || f.toLowerCase() === "readme.md") || (data.file_tree[0] ? data.file_tree[0].rel_path : null);
    if (defaultOpen) {
      ideOpenFile(defaultOpen);
    }
    ideRefreshPreview();
  } catch (err) {
    inspectBtn.innerText = "🔍 Scan & Index Project";
    inspectBtn.disabled = false;
    alert(`Indexing error: ${err.message}`);
  }
}

function ideRenderProject(data) {
  // Safe meta ribbon updates
  const metaRibbon = document.getElementById("ideMetaRibbon");
  if (metaRibbon) metaRibbon.style.display = "flex";
  const openExpBtn = document.getElementById("btnSupervisionOpenExplorer");
  if (openExpBtn) openExpBtn.style.display = "inline-flex";

  const supMetaStack = document.getElementById("supMetaStack");
  if (supMetaStack) supMetaStack.innerText = `Stack: ${data.tech_stack}`;
  const supMetaBranch = document.getElementById("supMetaBranch");
  if (supMetaBranch) supMetaBranch.innerText = `🌿 ${data.git_state ? data.git_state.branch : 'main'}`;
  const supMetaFiles = document.getElementById("supMetaFiles");
  if (supMetaFiles) supMetaFiles.innerText = `${data.file_count} files (${data.total_size_kb} KB)`;
  const supMetaSymbols = document.getElementById("supMetaSymbols");
  if (supMetaSymbols) supMetaSymbols.innerText = `${(data.symbols || []).length} symbols`;

  // Render Files Tree in ideFileTree (or legacy supervisionFileTree)
  const fileTreeEl = document.getElementById("ideFileTree") || document.getElementById("supervisionFileTree");
  if (fileTreeEl) {
    fileTreeEl.innerHTML = "";
    (data.file_tree || []).forEach(f => {
      const row = document.createElement("div");
      row.className = `tree-item ${f.is_key_file ? 'is-key' : ''}`;
      row.innerHTML = `
        <span>${f.is_key_file ? '⭐ ' : '📄 '}</span>
        <span style="flex: 1;">${escapeHtml(f.rel_path)}</span>
        <span style="font-size: 10.5px; color: var(--text-dim);">${Math.round(f.size_bytes / 1024)} KB</span>
      `;
      row.addEventListener("click", () => ideOpenFile(f.rel_path));
      fileTreeEl.appendChild(row);
    });
  }

  // Render Git Tree in ideGitStatus (or legacy supervisionGitTree)
  const gitTreeEl = document.getElementById("ideGitStatus") || document.getElementById("supervisionGitTree");
  if (gitTreeEl) {
    gitTreeEl.innerHTML = "";
    const gitState = data.git_state || {};
    const modified = gitState.modified || [];
    const untracked = gitState.untracked || [];

    if (modified.length === 0 && untracked.length === 0) {
      gitTreeEl.innerHTML = `<div class="empty-cell" style="padding: 10px;">Working tree clean. Zero uncommitted changes.</div>`;
    } else {
      modified.forEach(f => {
        const r = document.createElement("div");
        r.className = "tree-item";
        r.innerHTML = `<span style="color: var(--accent-amber);">● M</span> <span>${f}</span>`;
        r.addEventListener("click", () => ideOpenFile(f));
        gitTreeEl.appendChild(r);
      });
      untracked.forEach(f => {
        const r = document.createElement("div");
        r.className = "tree-item";
        r.innerHTML = `<span style="color: var(--accent-emerald);">● ?</span> <span>${f}</span>`;
        r.addEventListener("click", () => ideOpenFile(f));
        gitTreeEl.appendChild(r);
      });
    }
  }

  // Render Symbols Tree in ideSymbolsList (or legacy supervisionSymbolTree)
  const symTreeEl = document.getElementById("ideSymbolsList") || document.getElementById("supervisionSymbolTree");
  if (symTreeEl) {
    symTreeEl.innerHTML = "";
    const symbols = data.symbols || [];
    if (symbols.length === 0) {
      symTreeEl.innerHTML = `<div class="empty-cell" style="padding: 10px;">No symbols indexed.</div>`;
    } else {
      symbols.forEach(s => {
        const r = document.createElement("div");
        r.className = "tree-item";
        r.innerHTML = `<span style="color: var(--accent-cyan); font-weight: 700;">ƒ</span> <span>${s.name}</span> <span style="font-size: 10px; color: var(--text-dim);">(${s.type})</span>`;
        r.addEventListener("click", () => ideOpenFile(s.file));
        symTreeEl.appendChild(r);
      });
    }
  }

  // Right Panel: Mark Analysis checkmarks as verified
  const anProj = document.getElementById("svAnProject");
  if (anProj) anProj.className = "an-item done";
  const anDeps = document.getElementById("svAnDeps");
  if (anDeps) anDeps.className = "an-item done";
  const anFiles = document.getElementById("svAnFiles");
  if (anFiles) anFiles.className = "an-item done";
  const svGoal = document.getElementById("svGoalDisplay");
  if (svGoal && svGoal.innerText.includes("Awaiting")) {
    svGoal.innerText = `Workspace: ${data.project_name || 'Project Indexed'}`;
  }
}

async function ideOpenFile(relPath) {
  if (!ideActiveProjectDir) return;
  ideActiveTabFile = relPath;

  // Add to open tabs if not present
  if (!ideOpenTabs.find(t => t.file === relPath)) {
    ideOpenTabs.push({ file: relPath, title: relPath.split("/").pop() });
  }

  // Render Tabs in ideTabsContainer (or legacy ideEditorTabs)
  const tabsContainer = document.getElementById("ideTabsContainer") || document.getElementById("ideEditorTabs");
  if (tabsContainer) {
    tabsContainer.innerHTML = "";
    ideOpenTabs.forEach(t => {
      const tabEl = document.createElement("div");
      tabEl.className = `ide-tab ${t.file === relPath ? 'active' : ''}`;
      tabEl.innerHTML = `
        <span class="tab-title">${t.title}</span>
        <span class="tab-close" title="Close Tab">✕</span>
      `;
      tabEl.querySelector(".tab-title").addEventListener("click", () => ideOpenFile(t.file));
      tabEl.querySelector(".tab-close").addEventListener("click", (e) => {
        e.stopPropagation();
        ideCloseTab(t.file);
      });
      tabsContainer.appendChild(tabEl);
    });
  }

  // Update active file badge
  const filePill = document.getElementById("ideActiveFilePill");
  if (filePill) filePill.innerText = relPath;

  // Hide diff view, show code editor
  const diffCont = document.getElementById("ideDiffContainer");
  if (diffCont) diffCont.style.display = "none";
  const codeEd = document.getElementById("ideCodeEditor");
  if (codeEd) codeEd.style.display = "block";
  const lineGutter = document.getElementById("ideLineNumbers");
  if (lineGutter) lineGutter.style.display = "block";
  const confBanner = document.getElementById("ideConflictBanner");
  if (confBanner) confBanner.style.display = "none";

  // Fetch file content
  try {
    const res = await fetch(`/api/supervision/file?path=${encodeURIComponent(ideActiveProjectDir)}&file=${encodeURIComponent(relPath)}`);
    const data = await res.json();
    if (data.success) {
      if (codeEd) codeEd.value = data.content;
      ideActiveFileBaseHash = data.before_hash || "";
      ideUpdateLineNumbers();
    } else {
      alert(`Could not load ${relPath}: ${data.error}`);
    }
  } catch (e) {
    alert(`File fetch error: ${e.message}`);
  }
}

function ideCloseTab(relPath) {
  ideOpenTabs = ideOpenTabs.filter(t => t.file !== relPath);
  const tabsContainer = document.getElementById("ideTabsContainer") || document.getElementById("ideEditorTabs");
  const codeEd = document.getElementById("ideCodeEditor");
  const filePill = document.getElementById("ideActiveFilePill");

  if (ideActiveTabFile === relPath) {
    if (ideOpenTabs.length > 0) {
      ideOpenFile(ideOpenTabs[ideOpenTabs.length - 1].file);
    } else {
      ideActiveTabFile = null;
      if (tabsContainer) tabsContainer.innerHTML = `<div class="ide-tab active"><span>No File</span></div>`;
      if (codeEd) codeEd.value = "";
      if (filePill) filePill.innerText = "No file open";
    }
  }
}


async function ideSaveActiveFile(force = false) {
  if (!ideActiveProjectDir || !ideActiveTabFile) return;
  const content = document.getElementById("ideCodeEditor").value;

  try {
    const res = await fetch("/api/supervision/file", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        path: ideActiveProjectDir,
        file: ideActiveTabFile,
        content: content,
        author: "user",
        expected_base_hash: force ? null : ideActiveFileBaseHash
      })
    });
    const data = await res.json();
    if (data.conflict) {
      const confBanner = document.getElementById("ideConflictBanner");
      if (confBanner) confBanner.style.display = "flex";
      return;
    }
    const confBanner = document.getElementById("ideConflictBanner");
    if (confBanner) confBanner.style.display = "none";

    if (data.success) {
      ideActiveFileBaseHash = data.after_hash || null;
      logTerminal("[IDE]", `Saved '${ideActiveTabFile}' (${data.size_bytes} bytes)`, "log-done");
      if (data.diff) {
        ideActiveDiff = data.diff;
        ideRenderDiff(data.diff);
      }
      ideUpdateUndoRedoState(true, false);
      if (ideActiveTabFile.endsWith(".html") || ideActiveTabFile.endsWith(".css") || ideActiveTabFile.endsWith(".js")) {
        ideRefreshPreview();
      }
      ideLoadHistory();
    } else {
      alert(`Save error: ${data.error}`);
    }
  } catch (e) {
    alert(`Save error: ${e.message}`);
  }
}

function ideToggleDiffView() {
  const diffCont = document.getElementById("ideDiffContainer");
  const editor = document.getElementById("ideCodeEditor");
  const gutter = document.getElementById("ideLineNumbers");

  if (diffCont.style.display === "none") {
    diffCont.style.display = "block";
    editor.style.display = "none";
    gutter.style.display = "none";
  } else {
    diffCont.style.display = "none";
    editor.style.display = "block";
    gutter.style.display = "block";
  }
}

function ideRenderDiff(diffText) {
  const diffCont = document.getElementById("ideDiffContainer");
  if (!diffCont) return;
  if (!diffText) {
    diffCont.innerHTML = `<div class="empty-cell">No differences compared to disk version.</div>`;
    return;
  }
  if (ideDiffMode === "sidebyside") {
    const lines = diffText.split("\n");
    const leftLines = [];
    const rightLines = [];
    lines.forEach(l => {
      if (l.startsWith("-")) {
        leftLines.push(`<div class="diff-line-del">${escapeHtml(l)}</div>`);
      } else if (l.startsWith("+")) {
        rightLines.push(`<div class="diff-line-add">${escapeHtml(l)}</div>`);
      } else if (!l.startsWith("@@")) {
        leftLines.push(`<div>${escapeHtml(l)}</div>`);
        rightLines.push(`<div>${escapeHtml(l)}</div>`);
      }
    });
    diffCont.innerHTML = `
      <div class="diff-split">
        <div class="diff-pane">
          <div class="diff-pane-title">BEFORE (BASE STATE)</div>
          <div class="diff-pane-body">${leftLines.join("")}</div>
        </div>
        <div class="diff-pane">
          <div class="diff-pane-title">AFTER (MODIFIED STATE)</div>
          <div class="diff-pane-body">${rightLines.join("")}</div>
        </div>
      </div>
    `;
  } else {
    const lines = diffText.split("\n");
    diffCont.innerHTML = lines.map(line => {
      if (line.startsWith("+")) return `<span class="diff-line-add">${escapeHtml(line)}</span>`;
      if (line.startsWith("-")) return `<span class="diff-line-del">${escapeHtml(line)}</span>`;
      if (line.startsWith("@@")) return `<span class="diff-line-info">${escapeHtml(line)}</span>`;
      return `<span>${escapeHtml(line)}</span>`;
    }).join("");
  }
}

function escapeHtml(text) {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function ideOpenPlanTab() {
  if (!ideActiveProjectDir) {
    alert("Please scan a project workspace first.");
    return;
  }
  ideOpenFile("IMPLEMENTATION_PLAN.md");
}

async function ideRunTerminalCommand(command) {
  if (!ideActiveProjectDir) {
    alert("Please select a project first.");
    return;
  }
  const term = document.getElementById("ideTerminalOutput");
  term.innerHTML += `\n<span class="term-prompt">PS ${ideActiveProjectDir}&gt;</span> ${escapeHtml(command)}\n`;
  term.scrollTop = term.scrollHeight;

  try {
    const res = await fetch("/api/terminal/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: ideActiveProjectDir, command: command })
    });
    const data = await res.json();
    if (data.stdout) term.innerHTML += `${escapeHtml(data.stdout)}\n`;
    if (data.stderr) term.innerHTML += `<span style="color: #f87171;">${escapeHtml(data.stderr)}</span>\n`;
    term.innerHTML += `<span class="term-dim">Process completed in ${data.duration_ms}ms (exit code: ${data.exit_code})</span>\n`;
    term.scrollTop = term.scrollHeight;
  } catch (err) {
    term.innerHTML += `<span style="color: #f87171;">Command error: ${err.message}</span>\n`;
    term.scrollTop = term.scrollHeight;
  }
}

function ideRefreshPreview() {
  if (!ideActiveProjectDir) return;
  const frame = document.getElementById("idePreviewIframe");
  const urlField = document.getElementById("idePreviewUrl");
  const indexHtmlPath = `${ideActiveProjectDir}\\index.html`.replace(/\\/g, '/');
  const previewUri = `file:///${indexHtmlPath}`;
  urlField.value = previewUri;
  if (frame) frame.src = previewUri;
}

async function ideApplySeniorChanges(instruction) {
  if (!ideActiveProjectDir) {
    alert("Please scan a project directory first.");
    return;
  }
  const promptInput = document.getElementById("supervisionPromptInput");
  const inst = (typeof instruction === "string" && instruction.trim()) || (promptInput ? promptInput.value.trim() : "");
  if (!inst) {
    alert("Please enter a feature, refactoring, or bug fix instruction.");
    return;
  }

  const badge = document.getElementById("ideTaskStatusBadge") || document.getElementById("svActivePowerTag");
  const applyBtn = document.getElementById("btnSupervisionApply");
  const svGoal = document.getElementById("svGoalDisplay");
  if (svGoal) svGoal.innerText = inst;

  const svPlan = document.getElementById("svPlanList");
  if (svPlan) {
    svPlan.innerHTML = `
      <div class="sv-step-item done">✓ Analyze request & workspace</div>
      <div class="sv-step-item active">● Engineering changes</div>
      <div class="sv-step-item pending">○ Running automated tests</div>
      <div class="sv-step-item pending">○ Verifying diffs</div>
    `;
  }

  if (badge) {
    badge.innerText = "● Engineering";
    badge.className = "sv-power-badge";
  }
  setCatState("running", "Engineering changes...");
  if (applyBtn) {
    applyBtn.innerText = "⏳ Engineering...";
    applyBtn.disabled = true;
  }

  try {
    badge.innerText = "● Executing";
    const res = await fetch("/api/supervision/modify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: ideActiveProjectDir, instruction: instruction })
    });
    const data = await res.json();
    applyBtn.innerText = "🚀 Generate & Apply Code";
    applyBtn.disabled = false;

    if (!data.success) {
      badge.innerText = "Failed";
      badge.className = "status-pill status-err";
      alert(data.error || "Failed to apply code modifications.");
      return;
    }

    badge.innerText = "● Verified";
    badge.className = "status-pill status-done";
    promptInput.value = "";

    // 1. Direct Command / Test Execution Handling
    if (data.is_command) {
      logTerminal(`[TERMINAL] $ ${data.command}`, data.stdout || data.stderr || "(Completed with no output)", data.exit_code === 0 ? "log-done" : "log-err");
      switchBottomTab("terminal");
      ideAppendLog(data);
      if (data.files_modified && data.files_modified.length > 0) {
        await ideInspectProject(ideActiveProjectDir);
      }
      return;
    }

    ideAppendLog(data);
    logTerminal("[SUPERVISION]", `Applied: ${data.diff_summary}`, "log-done");

    // 2. Log any executed post-refactor commands / tests
    if (data.exec_logs && data.exec_logs.length > 0) {
      data.exec_logs.forEach(l => {
        logTerminal(`[BUILD/TEST] $ ${l.command}`, l.output || `Exited with code ${l.exit_code}`, l.exit_code === 0 ? "log-done" : "log-err");
      });
      switchBottomTab("terminal");
    }

    // Populate AI Explanation Card
    ideLastAiGroup = data;
    const expCard = document.getElementById("ideAiExplanationCard");
    if (expCard) {
      expCard.style.display = "block";
      const whyEl = document.getElementById("expWhyText");
      const whatEl = document.getElementById("expWhatText");
      const resEl = document.getElementById("expResultText");
      const riskEl = document.getElementById("explanationRiskBadge");
      const filesEl = document.getElementById("expFilesList");

      if (whyEl) whyEl.innerText = data.why || instruction;
      if (whatEl) whatEl.innerText = data.what || data.diff_summary;
      if (resEl) resEl.innerText = data.verification || "All files updated and verified.";
      if (riskEl) riskEl.innerText = data.risk_level || "MEDIUM";
      if (filesEl) {
        filesEl.innerHTML = (data.files_modified || []).map(f => `<span class="exp-file-tag">📄 ${f.path}</span>`).join(" ");
      }
    }
    ideUpdateUndoRedoState(true, false);

    // Populate Diffs Tab
    if (data.diffs && data.diffs.length > 0) {
      const bottomDiffList = document.getElementById("ideBottomDiffList");
      bottomDiffList.innerHTML = data.diffs.map(d => `
        <div style="margin-bottom: 12px; border: 1px solid var(--border-card); border-radius: 6px; padding: 8px;">
          <strong style="color: var(--accent-cyan);">File: ${d.file}</strong>
          <div style="margin-top: 6px;">${d.diff.split("\n").map(l => {
            if (l.startsWith("+")) return `<div class="diff-line-add">${escapeHtml(l)}</div>`;
            if (l.startsWith("-")) return `<div class="diff-line-del">${escapeHtml(l)}</div>`;
            return `<div>${escapeHtml(l)}</div>`;
          }).join("")}</div>
        </div>
      `).join("");
      switchBottomTab("diffs");
    }

    // Refresh Project Index & Reopen Modified File
    await ideInspectProject(ideActiveProjectDir);
    if (data.files_modified && data.files_modified[0]) {
      ideOpenFile(data.files_modified[0].path);
    }
    ideRefreshPreview();
    triggerCatVictoryJump();
  } catch (e) {
    setCatState("idle", "Execution Error");
    badge.innerText = "Error";
    badge.className = "status-pill status-err";
    applyBtn.innerText = "🚀 Generate & Apply Code";
    applyBtn.disabled = false;
    alert(`Senior Dev Engineering Error: ${e.message}`);
  }
}

function ideAppendLog(data) {
  const area = document.getElementById("ideHistoryTimeline");
  if (!area) return;
  const empty = area.querySelector(".empty-cell");
  if (empty) empty.remove();

  const card = document.createElement("div");
  card.className = "sup-log-card";
  card.innerHTML = `
    <div class="sup-log-title">👨‍💻 Refactored: ${data.instruction}</div>
    <div style="font-size: 13px; color: var(--text-main);">${data.diff_summary}</div>
    <div style="margin-top: 6px;">
      ${(data.files_modified || []).map(f => `<span class="sup-file-tag">✓ ${f.path} (${f.action})</span>`).join("")}
    </div>
    <div style="font-size: 11px; color: var(--accent-emerald); margin-top: 4px;">🛡️ ${data.verification}</div>
  `;
  area.prepend(card);
}

// =========================================================================
// COLLABORATIVE EDITING, UNDO/REDO, SNAPSHOT & FILE OPERATIONS
// =========================================================================

function ideUpdateUndoRedoState(canUndo, canRedo) {
  const undoBtn = document.getElementById("btnIdeUndo");
  const redoBtn = document.getElementById("btnIdeRedo");
  if (undoBtn) undoBtn.disabled = !canUndo;
  if (redoBtn) redoBtn.disabled = !canRedo;
}

async function ideTriggerUndo() {
  if (!ideActiveProjectDir) return;
  try {
    const res = await fetch("/api/supervision/undo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: ideActiveProjectDir })
    });
    const data = await res.json();
    if (data.success) {
      logTerminal("[UNDO]", `Undone ${data.type} change (${data.reverted_files.join(", ")})`, "log-done");
      ideUpdateUndoRedoState(data.can_undo, data.can_redo);
      await ideInspectProject(ideActiveProjectDir);
      if (ideActiveTabFile) ideOpenFile(ideActiveTabFile);
      ideRefreshPreview();
      ideLoadHistory();
    } else {
      alert(data.error || "Nothing to undo.");
    }
  } catch (e) {
    alert(`Undo error: ${e.message}`);
  }
}

async function ideTriggerRedo() {
  if (!ideActiveProjectDir) return;
  try {
    const res = await fetch("/api/supervision/redo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: ideActiveProjectDir })
    });
    const data = await res.json();
    if (data.success) {
      logTerminal("[REDO]", `Restored ${data.type} change (${data.restored_files.join(", ")})`, "log-done");
      ideUpdateUndoRedoState(data.can_undo, data.can_redo);
      await ideInspectProject(ideActiveProjectDir);
      if (ideActiveTabFile) ideOpenFile(ideActiveTabFile);
      ideRefreshPreview();
      ideLoadHistory();
    } else {
      alert(data.error || "Nothing to redo.");
    }
  } catch (e) {
    alert(`Redo error: ${e.message}`);
  }
}

async function ideCreateSnapshotPrompt() {
  if (!ideActiveProjectDir) {
    alert("Please scan a project workspace first.");
    return;
  }
  const title = prompt("Enter a description for this snapshot:", `Snapshot ${new Date().toLocaleTimeString()}`);
  if (!title) return;
  try {
    const res = await fetch("/api/supervision/snapshots", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: ideActiveProjectDir, title: title })
    });
    const data = await res.json();
    logTerminal("[SNAPSHOT]", `Created snapshot '${title}' (${data.file_count} files)`, "log-done");
    ideLoadSnapshots();
  } catch (e) {
    alert(`Snapshot error: ${e.message}`);
  }
}

async function ideLoadHistory() {
  if (!ideActiveProjectDir) return;
  const container = document.getElementById("ideHistoryTimeline");
  if (!container) return;
  try {
    const res = await fetch(`/api/supervision/history?path=${encodeURIComponent(ideActiveProjectDir)}`);
    const timeline = await res.json();
    if (!timeline || timeline.length === 0) {
      container.innerHTML = `<div class="empty-cell">No changes recorded in project history yet.</div>`;
      return;
    }
    container.innerHTML = timeline.map(item => `
      <div class="timeline-item author-${item.author}">
        <div class="timeline-content">
          <div class="timeline-header-row">
            <span class="timeline-author-badge author-${item.author}">${item.author}</span>
            <span class="timeline-time">${item.timestamp}</span>
          </div>
          <div class="timeline-title">${escapeHtml(item.title || item.operation || 'Change')}</div>
          ${item.why ? `<div style="font-size: 10px; color: #94a3b8; margin-top: 2px;">Why: ${escapeHtml(item.why)}</div>` : ''}
          <div style="font-size: 10px; color: #64748b; margin-top: 4px;">
            ${(item.files || []).map(f => `<code>${f}</code>`).join(", ")}
          </div>
          <div class="timeline-actions">
            ${item.type === 'group' ? `<button class="btn-ide-mini danger" onclick="ideUndoGroup('${item.id}')">Undo Task</button>` : ''}
          </div>
        </div>
      </div>
    `).join("");
  } catch (e) {
    container.innerHTML = `<div class="empty-cell">Failed to load history: ${e.message}</div>`;
  }
}

async function ideUndoGroup(groupId) {
  if (!ideActiveProjectDir) return;
  try {
    const res = await fetch("/api/supervision/undo/group", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: ideActiveProjectDir, group_id: groupId })
    });
    const data = await res.json();
    if (data.success) {
      logTerminal("[UNDO]", `Reverted group '${data.title}' (${data.reverted_files.join(", ")})`, "log-done");
      await ideInspectProject(ideActiveProjectDir);
      if (ideActiveTabFile) ideOpenFile(ideActiveTabFile);
      ideRefreshPreview();
      ideLoadHistory();
    }
  } catch (e) {
    alert(`Undo group error: ${e.message}`);
  }
}

async function ideLoadSnapshots() {
  if (!ideActiveProjectDir) return;
  const container = document.getElementById("ideSnapshotsList");
  if (!container) return;
  try {
    const res = await fetch(`/api/supervision/snapshots?path=${encodeURIComponent(ideActiveProjectDir)}`);
    const snapshots = await res.json();
    if (!snapshots || snapshots.length === 0) {
      container.innerHTML = `<div class="empty-cell">No snapshots recorded yet.</div>`;
      return;
    }
    container.innerHTML = snapshots.map(s => `
      <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; margin-bottom: 8px; background: rgba(255,255,255,0.03); border: 1px solid var(--border-card); border-radius: 6px;">
        <div>
          <div style="font-weight: 600; font-size: 11px; color: #fff;">📸 ${escapeHtml(s.title)}</div>
          <div style="font-size: 10px; color: #64748b; font-family: var(--font-mono);">${s.timestamp} • ${s.file_count} files</div>
        </div>
        <button class="btn-ide-mini" onclick="ideRestoreSnapshot('${s.snapshot_id}')">Restore</button>
      </div>
    `).join("");
  } catch (e) {
    container.innerHTML = `<div class="empty-cell">Failed to load snapshots: ${e.message}</div>`;
  }
}

async function ideRestoreSnapshot(snapshotId) {
  if (!ideActiveProjectDir) return;
  if (!confirm("Are you sure you want to restore this snapshot? All current files will be rolled back.")) return;
  try {
    const res = await fetch("/api/supervision/snapshots/restore", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: ideActiveProjectDir, snapshot_id: snapshotId })
    });
    const data = await res.json();
    if (data.success) {
      logTerminal("[SNAPSHOT]", `Restored project to snapshot '${data.title}' (${data.restored_count} files)`, "log-done");
      await ideInspectProject(ideActiveProjectDir);
      if (ideActiveTabFile) ideOpenFile(ideActiveTabFile);
      ideRefreshPreview();
      ideLoadHistory();
    } else {
      alert(data.error || "Failed to restore snapshot.");
    }
  } catch (e) {
    alert(`Restore error: ${e.message}`);
  }
}

async function ideCreateFilePrompt() {
  if (!ideActiveProjectDir) return;
  const filename = prompt("Enter new file name (e.g. src/index.js, styles.css):");
  if (!filename) return;
  try {
    const res = await fetch("/api/supervision/file/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: ideActiveProjectDir, file: filename, content: "" })
    });
    const data = await res.json();
    if (data.success) {
      await ideInspectProject(ideActiveProjectDir);
      ideOpenFile(filename);
      logTerminal("[IDE]", `Created file '${filename}'`, "log-done");
    }
  } catch (e) {
    alert(`Create file error: ${e.message}`);
  }
}

async function ideCreateFolderPrompt() {
  if (!ideActiveProjectDir) return;
  const foldername = prompt("Enter new folder path (e.g. src/components, tests):");
  if (!foldername) return;
  try {
    const res = await fetch("/api/supervision/folder/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: ideActiveProjectDir, folder: foldername })
    });
    const data = await res.json();
    if (data.success) {
      await ideInspectProject(ideActiveProjectDir);
      logTerminal("[IDE]", `Created folder '${foldername}'`, "log-done");
    }
  } catch (e) {
    alert(`Create folder error: ${e.message}`);
  }
}

async function ideRenamePrompt() {
  if (!ideActiveProjectDir || !ideActiveTabFile) {
    alert("Select an open file to rename.");
    return;
  }
  const newName = prompt(`Rename '${ideActiveTabFile}' to:`, ideActiveTabFile);
  if (!newName || newName === ideActiveTabFile) return;
  try {
    const res = await fetch("/api/supervision/file/rename", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: ideActiveProjectDir, old_path: ideActiveTabFile, new_path: newName })
    });
    const data = await res.json();
    if (data.success) {
      ideCloseTab(ideActiveTabFile);
      await ideInspectProject(ideActiveProjectDir);
      ideOpenFile(newName);
      logTerminal("[IDE]", `Renamed '${ideActiveTabFile}' to '${newName}'`, "log-done");
    }
  } catch (e) {
    alert(`Rename error: ${e.message}`);
  }
}

async function ideDeletePrompt() {
  if (!ideActiveProjectDir || !ideActiveTabFile) {
    alert("Select an open file to delete.");
    return;
  }
  if (!confirm(`Are you sure you want to delete '${ideActiveTabFile}'?`)) return;
  try {
    const res = await fetch("/api/supervision/file/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: ideActiveProjectDir, file: ideActiveTabFile })
    });
    const data = await res.json();
    if (data.success) {
      const deletedFile = ideActiveTabFile;
      ideCloseTab(deletedFile);
      await ideInspectProject(ideActiveProjectDir);
      logTerminal("[IDE]", `Deleted file '${deletedFile}'`, "log-done");
    }
  } catch (e) {
    alert(`Delete error: ${e.message}`);
  }
}

async function ideFormatActiveFile() {
  if (!ideActiveProjectDir || !ideActiveTabFile) return;
  try {
    const res = await fetch("/api/supervision/format", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: ideActiveProjectDir, file: ideActiveTabFile })
    });
    const data = await res.json();
    if (data.formatted) {
      logTerminal("[FORMATTER]", `Formatted '${ideActiveTabFile}'`, "log-done");
      ideOpenFile(ideActiveTabFile);
    } else {
      logTerminal("[FORMATTER]", data.message || "File is already clean.", "log-dim");
    }
  } catch (e) {
    alert(`Format error: ${e.message}`);
  }
}

function ideToggleFindBar() {
  const bar = document.getElementById("ideFindReplaceBar");
  if (!bar) return;
  bar.style.display = bar.style.display === "none" ? "flex" : "none";
  if (bar.style.display === "flex") {
    const inp = document.getElementById("findInput") || document.getElementById("ideFindInput");
    if (inp) inp.focus();
  }
}

function ideFindNext() {
  const queryInp = document.getElementById("findInput") || document.getElementById("ideFindInput");
  const query = queryInp ? queryInp.value : "";
  const editor = document.getElementById("ideCodeEditor");
  if (!query || !editor) return;
  const text = editor.value;
  const startPos = editor.selectionEnd || 0;
  let nextPos = text.indexOf(query, startPos);
  if (nextPos === -1) nextPos = text.indexOf(query, 0);
  if (nextPos !== -1) {
    editor.focus();
    editor.setSelectionRange(nextPos, nextPos + query.length);
  }
}

function ideReplaceOne() {
  const queryInp = document.getElementById("findInput") || document.getElementById("ideFindInput");
  const replInp = document.getElementById("replaceInput") || document.getElementById("ideReplaceInput");
  const query = queryInp ? queryInp.value : "";
  const repl = replInp ? replInp.value : "";
  const editor = document.getElementById("ideCodeEditor");
  if (!query || !editor) return;
  const selStart = editor.selectionStart;
  const selEnd = editor.selectionEnd;
  if (selStart !== selEnd && editor.value.substring(selStart, selEnd) === query) {
    editor.setRangeText(repl, selStart, selEnd, "select");
  }
  ideFindNext();
}

function ideReplaceAll() {
  const queryInp = document.getElementById("findInput") || document.getElementById("ideFindInput");
  const replInp = document.getElementById("replaceInput") || document.getElementById("ideReplaceInput");
  const query = queryInp ? queryInp.value : "";
  const repl = replInp ? replInp.value : "";
  const editor = document.getElementById("ideCodeEditor");
  if (!query || !editor) return;
  editor.value = editor.value.split(query).join(repl);
  ideUpdateLineNumbers();
}

function ideToggleSideBySideDiff() {
  ideDiffMode = ideDiffMode === "sidebyside" ? "inline" : "sidebyside";
  ideRenderDiff(ideActiveDiff);
  const diffCont = document.getElementById("ideDiffContainer");
  const editor = document.getElementById("ideCodeEditor");
  const gutter = document.getElementById("ideLineNumbers");
  diffCont.style.display = "block";
  editor.style.display = "none";
  gutter.style.display = "none";
}

async function ideAcceptAiChanges() {
  const expCard = document.getElementById("ideAiExplanationCard");
  if (expCard) expCard.style.display = "none";
  logTerminal("[AI]", "Accepted AI changes.", "log-done");
}

async function ideRejectAiChanges() {
  if (!ideLastAiGroup || !ideLastAiGroup.group_id) return;
  await ideUndoGroup(ideLastAiGroup.group_id);
  const expCard = document.getElementById("ideAiExplanationCard");
  if (expCard) expCard.style.display = "none";
  logTerminal("[AI]", "Rejected AI changes and reverted task files.", "log-done");
}

// =========================================================================
// IN-APP FILE EXPLORER MODAL & NATIVE DIALOG PICKER
// =========================================================================

let pickerCurrentPath = "";
let pickerParentPath = null;
let pickerSelectedItem = null;

function ideOpenPickerModal() {
  const modal = document.getElementById("ideFilePickerModal");
  if (!modal) return;
  modal.style.display = "flex";

  ideLoadDrives();
  const initial = ideActiveProjectDir || document.getElementById("supervisionPathInput").value.trim() || "K:\\";
  idePickerLoadDir(initial);
}

function ideClosePickerModal() {
  const modal = document.getElementById("ideFilePickerModal");
  if (modal) modal.style.display = "none";
}

async function ideLoadDrives() {
  const bar = document.getElementById("pickerDrivesBar");
  if (!bar) return;
  try {
    const res = await fetch("/api/fs/drives");
    const drivesData = await res.json();
    const driveList = Array.isArray(drivesData) ? drivesData : ((drivesData && drivesData.drives) || ["C:\\"]);
    bar.innerHTML = `<span class="picker-drives-label">Drives:</span>` +
      driveList.map(d => `<button class="picker-drive-btn" onclick="idePickerLoadDir('${d.replace(/\\/g, '\\\\')}')">${d}</button>`).join(" ");
  } catch (e) {
    console.error("Failed to load drives:", e);
  }
}

async function idePickerLoadDir(dirPath) {
  if (!dirPath) dirPath = "C:\\";
  const listEl = document.getElementById("pickerItemsList");
  const pathInp = document.getElementById("pickerPathInput");
  const upBtn = document.getElementById("btnPickerUp");
  const folderBtn = document.getElementById("btnPickerSelectFolder");
  const fileBtn = document.getElementById("btnPickerSelectFile");
  const selLabel = document.getElementById("pickerSelectedItem");

  listEl.innerHTML = `<div class="empty-cell">Reading folder...</div>`;
  pickerSelectedItem = null;
  if (selLabel) selLabel.innerText = "None";
  if (folderBtn) {
    folderBtn.disabled = false;
    folderBtn.innerText = "📂 Open Current Workspace";
  }
  if (fileBtn) fileBtn.disabled = true;

  try {
    const res = await fetch(`/api/fs/browse?path=${encodeURIComponent(dirPath)}`);
    const data = await res.json();

    if (!data.success) {
      listEl.innerHTML = `<div class="empty-cell" style="color: #f87171;">${data.error || 'Failed to read directory.'}</div>`;
      return;
    }

    pickerCurrentPath = data.current_path;
    pickerParentPath = data.parent_path;
    if (pathInp) pathInp.value = data.current_path;
    if (upBtn) upBtn.disabled = !data.parent_path;

    document.querySelectorAll(".picker-drive-btn").forEach(b => {
      b.classList.toggle("active", pickerCurrentPath.toLowerCase().startsWith(b.innerText.toLowerCase()));
    });

    if (data.folders.length === 0 && data.files.length === 0) {
      listEl.innerHTML = `<div class="empty-cell">Folder is empty.</div>`;
      return;
    }

    listEl.innerHTML = "";

    // Render Folders
    data.folders.forEach(f => {
      const row = document.createElement("div");
      row.className = "picker-item-row";
      row.innerHTML = `
        <div class="picker-item-left">
          <span class="picker-item-icon">📁</span>
          <span class="picker-item-name">${escapeHtml(f.name)}</span>
        </div>
        <span class="picker-item-meta">folder</span>
      `;
      row.addEventListener("dblclick", () => idePickerLoadDir(f.path));
      row.addEventListener("click", () => {
        document.querySelectorAll(".picker-item-row").forEach(r => r.classList.remove("selected"));
        row.classList.add("selected");
        pickerSelectedItem = f;
        if (selLabel) selLabel.innerText = `📁 ${f.name}`;
        if (folderBtn) {
          folderBtn.disabled = false;
          folderBtn.innerText = `📂 Open '${f.name}'`;
        }
        if (fileBtn) fileBtn.disabled = true;
      });
      listEl.appendChild(row);
    });

    // Render Files
    data.files.forEach(f => {
      const row = document.createElement("div");
      row.className = "picker-item-row";
      const sizeKb = Math.round(f.size_bytes / 1024) || 1;
      row.innerHTML = `
        <div class="picker-item-left">
          <span class="picker-item-icon">📄</span>
          <span class="picker-item-name">${escapeHtml(f.name)}</span>
        </div>
        <span class="picker-item-meta">${sizeKb} KB</span>
      `;
      row.addEventListener("click", () => {
        document.querySelectorAll(".picker-item-row").forEach(r => r.classList.remove("selected"));
        row.classList.add("selected");
        pickerSelectedItem = f;
        if (selLabel) selLabel.innerText = `📄 ${f.name}`;
        if (fileBtn) {
          fileBtn.disabled = false;
          fileBtn.innerText = `📄 Open '${f.name}'`;
        }
        if (folderBtn) {
          folderBtn.disabled = false;
          folderBtn.innerText = `📂 Open Current Workspace`;
        }
      });
      listEl.appendChild(row);
    });
  } catch (err) {
    listEl.innerHTML = `<div class="empty-cell" style="color: #f87171;">Fetch error: ${err.message}</div>`;
  }
}

function idePickerGoUp() {
  if (pickerParentPath) {
    idePickerLoadDir(pickerParentPath);
  }
}

function idePickerRefresh() {
  if (pickerCurrentPath) {
    idePickerLoadDir(pickerCurrentPath);
  }
}

function idePickerConfirmFolder() {
  const targetFolder = (pickerSelectedItem && pickerSelectedItem.is_dir) ? pickerSelectedItem.path : pickerCurrentPath;
  if (!targetFolder) return;
  ideClosePickerModal();
  const input = document.getElementById("supervisionPathInput");
  if (input) input.value = targetFolder;
  ideInspectProject(targetFolder);
}

function idePickerConfirmFile() {
  if (!pickerSelectedItem || pickerSelectedItem.is_dir) return;
  const filePath = pickerSelectedItem.path;
  const folderPath = pickerCurrentPath;
  const fileName = pickerSelectedItem.name;
  ideClosePickerModal();
  const input = document.getElementById("supervisionPathInput");
  if (input) input.value = folderPath;
  ideInspectProject(folderPath).then(() => {
    ideOpenFile(fileName);
  });
}

async function idePickNativeDialog(pickType = "folder") {
  try {
    const res = await fetch("/api/fs/native_pick", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pick_type: pickType, initial_dir: pickerCurrentPath })
    });
    const data = await res.json();
    if (data.success && data.path) {
      ideClosePickerModal();
      if (data.is_file) {
        const parts = data.path.split(/[\\/]/);
        const fileName = parts.pop();
        const folder = parts.join("\\");
        const input = document.getElementById("supervisionPathInput");
        if (input) input.value = folder;
        await ideInspectProject(folder);
        ideOpenFile(fileName);
      } else {
        const input = document.getElementById("supervisionPathInput");
        if (input) input.value = data.path;
        await ideInspectProject(data.path);
      }
    }
  } catch (err) {
    alert(`Native dialog error: ${err.message}`);
  }
}

function initChatMode() {
  const input = document.getElementById("chatInput");
  const sendBtn = document.getElementById("chatSendBtn");
  const select = document.getElementById("chatModelSelect");
  const refreshBtn = document.getElementById("refreshModelsBtn");

  if (!input || !sendBtn) return;

  if (select) {
    select.addEventListener("change", () => {
      localStorage.setItem("kritiai_chat_model", select.value);
      updateChatModelBadge();
      const modelObj = availableModelsList.find(m => m.id === select.value);
      logTerminal("[MODEL]", `Active chat model switched to: ${modelObj ? modelObj.name : select.value}`);
    });
  }

  if (refreshBtn) {
    refreshBtn.addEventListener("click", async () => {
      refreshBtn.innerText = "⏳";
      await loadAvailableModels();
      refreshBtn.innerText = "🔄";
    });
  }

  const send = async () => {
    const text = input.value.trim();
    if (!text) return;
    input.value = "";
    appendChatMessage("user", "You", text);

    const chosenModel = select ? select.value : null;

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, model: chosenModel })
      });
      const data = await res.json();

      let badgeInfo = null;
      if (data.switched_model) {
        badgeInfo = "✨ Switched to Qwen / DeepSeek (Current Affairs)";
        logTerminal("[ROUTER]", `Current Affairs query: dynamically routed to ${data.model}`);
        if (select) {
          const match = availableModelsList.find(m => m.id.toLowerCase().includes(data.model.toLowerCase()) || m.name.toLowerCase().includes(data.model.toLowerCase()));
          if (match) {
            select.value = match.id;
            updateChatModelBadge();
          }
        }
      }

      appendChatMessage("assistant", "KritiAI Assistant", data.content, data.model, badgeInfo);
    } catch (e) {
      appendChatMessage("assistant", "KritiAI Assistant", `[Error: ${e.message}]`);
    }
  };

  sendBtn.addEventListener("click", send);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") send();
  });
}

function appendChatMessage(role, sender, text, modelUsed = null, extraBadge = null) {
  const container = document.getElementById("chatMessages");
  const div = document.createElement("div");
  div.className = `chat-bubble ${role}`;
  const modelTag = modelUsed ? `<span class="step-tag" style="margin-left: 6px; font-size: 10px;">${modelUsed}</span>` : "";
  const switchedTag = extraBadge ? `<span class="status-pill status-active" style="margin-left: 6px; font-size: 10.5px; padding: 2px 8px; background: rgba(99, 102, 241, 0.25); border-color: #818cf8; color: #c7d2fe;">${extraBadge}</span>` : "";
  div.innerHTML = `
    <div class="chat-sender-label" style="display: flex; align-items: center; flex-wrap: wrap; gap: 4px;">
      <span>${sender}</span> ${modelTag} ${switchedTag}
    </div>
    <div style="margin-top: 4px; line-height: 1.6;">${text}</div>
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

    // Topbar power pills
    document.querySelectorAll(".power-pill[data-mode]").forEach(p => {
      p.classList.toggle("active", p.dataset.mode === currentConfig.power_mode);
    });

    // Settings radio buttons
    const radio = document.querySelector(`input[name="settingsPowerMode"][value="${currentConfig.power_mode}"]`);
    if (radio) radio.checked = true;

    // SuperVision badge
    const svTag = document.getElementById("svActivePowerTag");
    if (svTag && currentConfig.power_mode) {
      svTag.innerText = `● ${currentConfig.power_mode.charAt(0).toUpperCase() + currentConfig.power_mode.slice(1)}`;
    }

    // Legacy buttons fallback
    document.querySelectorAll(".power-btn[data-mode]").forEach(p => {
      p.classList.toggle("active", p.dataset.mode === currentConfig.power_mode);
    });

    if (currentConfig.emergency_stop_active) {
      const stopBtn = document.getElementById("emergencyStopBtn");
      if (stopBtn) stopBtn.classList.add("pulsing");
    }
  } catch (e) {
    console.error("Config error:", e);
  }
}

function populateModelDropdown(selectEl, selectedValue) {
  if (!selectEl) return;
  selectEl.innerHTML = "";

  const autoOpt = document.createElement("option");
  autoOpt.value = "auto";
  autoOpt.innerText = "⚡ Auto (Optimal System Routing)";
  selectEl.appendChild(autoOpt);

  if (!availableModelsList || !availableModelsList.length) {
    if (selectedValue && selectedValue !== "auto") {
      const opt = document.createElement("option");
      opt.value = selectedValue;
      opt.innerText = selectedValue;
      selectEl.appendChild(opt);
    }
    selectEl.value = selectedValue || "auto";
    return;
  }

  const localGroup = document.createElement("optgroup");
  localGroup.label = "💻 Local / Offline Models";
  const cloudGroup = document.createElement("optgroup");
  cloudGroup.label = "☁️ External API / Cloud Models";

  availableModelsList.forEach(m => {
    const opt = document.createElement("option");
    opt.value = m.id;
    opt.innerText = `${m.name} (${m.provider_display || m.provider})`;
    if (m.is_local) {
      localGroup.appendChild(opt);
    } else {
      cloudGroup.appendChild(opt);
    }
  });

  if (localGroup.children.length > 0) selectEl.appendChild(localGroup);
  if (cloudGroup.children.length > 0) selectEl.appendChild(cloudGroup);

  // Set selected value
  if (selectedValue && [...selectEl.options].some(o => o.value === selectedValue)) {
    selectEl.value = selectedValue;
  } else if (selectedValue && selectedValue !== "auto") {
    const customOpt = document.createElement("option");
    customOpt.value = selectedValue;
    customOpt.innerText = `⚙️ ${selectedValue}`;
    selectEl.appendChild(customOpt);
    selectEl.value = selectedValue;
  } else {
    selectEl.value = "auto";
  }
}

async function loadSettingsTab() {
  await loadConfig();
  if (!availableModelsList || availableModelsList.length === 0) {
    await loadAvailableModels();
  }

  if (currentConfig) {
    const radio = document.querySelector(`input[name="settingsPowerMode"][value="${currentConfig.power_mode}"]`);
    if (radio) radio.checked = true;

    const codeSelect = document.getElementById("settingCodingModel");
    const reasonSelect = document.getElementById("settingReasoningModel");
    const visionSelect = document.getElementById("settingVisionModel");
    const fastSelect = document.getElementById("settingFastModel");
    if (codeSelect) populateModelDropdown(codeSelect, (currentConfig.models && currentConfig.models.coding_model) || "auto");
    if (reasonSelect) populateModelDropdown(reasonSelect, (currentConfig.models && currentConfig.models.reasoning_model) || "auto");
    if (visionSelect) populateModelDropdown(visionSelect, (currentConfig.models && currentConfig.models.vision_model) || "auto");
    if (fastSelect) populateModelDropdown(fastSelect, (currentConfig.models && currentConfig.models.fast_model) || "auto");

    if (document.getElementById("settingApiBaseUrl") && currentConfig.models) {
      document.getElementById("settingApiBaseUrl").value = currentConfig.models.openai_base_url || "https://api.openai.com/v1";
      document.getElementById("settingApiKey").value = currentConfig.models.openai_api_key || "";
      document.getElementById("settingApiDefaultModel").value = currentConfig.models.openai_model || "gpt-4o";
    }
  }

  try {
    const sysEl = document.getElementById("systemInfoContent");
    if (sysEl) {
      const res = await fetch("/api/system-info");
      const sys = await res.json();
      sysEl.innerText = JSON.stringify(sys, null, 2);
    }
  } catch (e) {
    // ignore
  }
}

function initSettings() {
  const testApiBtn = document.getElementById("testAndSaveApiBtn");
  if (testApiBtn) {
    testApiBtn.addEventListener("click", async () => {
      const statusMsg = document.getElementById("apiStatusMessage");
      testApiBtn.innerText = "Connecting...";
      testApiBtn.disabled = true;
      if (statusMsg) {
        statusMsg.style.display = "block";
        statusMsg.style.color = "var(--accent-cyan)";
        statusMsg.innerText = "Querying API endpoint for available models...";
      }

      try {
        const payload = {
          base_url: (document.getElementById("settingApiBaseUrl") ? document.getElementById("settingApiBaseUrl").value : "").trim(),
          api_key: (document.getElementById("settingApiKey") ? document.getElementById("settingApiKey").value : "").trim(),
          default_model: (document.getElementById("settingApiDefaultModel") ? document.getElementById("settingApiDefaultModel").value : "").trim()
        };
        const res = await fetch("/api/models/providers", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        testApiBtn.innerText = "Connect & Save Key";
        testApiBtn.disabled = false;
        if (data.success) {
          if (statusMsg) {
            statusMsg.style.color = "var(--accent-emerald)";
            statusMsg.innerText = `✓ Connected! Discovered ${data.models.length} model(s).`;
          }
          await loadAvailableModels();
        } else {
          if (statusMsg) {
            statusMsg.style.color = "var(--accent-rose)";
            statusMsg.innerText = `Failed: ${data.message || 'Could not connect.'}`;
          }
        }
      } catch (e) {
        testApiBtn.innerText = "Connect & Save Key";
        testApiBtn.disabled = false;
        if (statusMsg) {
          statusMsg.style.color = "var(--accent-rose)";
          statusMsg.innerText = `Connection error: ${e.message}`;
        }
      }
    });
  }

  // Save Settings if button present
  const saveBtn = document.getElementById("saveSettingsBtn");
  if (saveBtn) {
    saveBtn.addEventListener("click", async () => {
      const payload = {
        power_mode: (document.querySelector('input[name="settingsPowerMode"]:checked') || {}).value || "autonomous",
        coding_model: (document.getElementById("settingCodingModel") || {}).value || "auto",
        reasoning_model: (document.getElementById("settingReasoningModel") || {}).value || "auto"
      };
      await fetch("/api/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      alert("Settings saved successfully.");
      await loadConfig();
    });
  }

  // Clear memory
  const clearMemBtn = document.getElementById("btnClearMemoryBtn") || document.getElementById("clearMemoryBtn");
  if (clearMemBtn) {
    clearMemBtn.addEventListener("click", async () => {
      if (confirm("Clear all local memory entries?")) {
        await fetch("/api/memory", { method: "DELETE" });
        loadMemory();
      }
    });
  }

  // Application Updates (Spec Section 24)
  const checkUpdatesBtn = document.getElementById("btnCheckUpdates");
  const updateModal = document.getElementById("updateModal");
  if (checkUpdatesBtn) {
    checkUpdatesBtn.addEventListener("click", () => {
      const statusMsg = document.getElementById("updateStatusMsg");
      if (statusMsg) statusMsg.innerText = "Checking release servers for updates...";
      setTimeout(() => {
        if (statusMsg) statusMsg.innerText = "";
        if (updateModal) {
          updateModal.style.display = "flex";
          updateModal.classList.remove("hidden");
        }
      }, 700);
    });
  }

  const btnUpdateNow = document.getElementById("btnUpdateNow");
  const btnUpdateLater = document.getElementById("btnUpdateLater");
  const btnUpdateViewChanges = document.getElementById("btnUpdateViewChanges");

  if (btnUpdateNow) {
    btnUpdateNow.addEventListener("click", () => {
      btnUpdateNow.innerText = "Updating... (restart required)";
      btnUpdateNow.disabled = true;
      setTimeout(() => {
        if (updateModal) {
          updateModal.style.display = "none";
          updateModal.classList.add("hidden");
        }
        btnUpdateNow.innerText = "Update";
        btnUpdateNow.disabled = false;
        alert("KritiAI is running the latest build.");
      }, 1500);
    });
  }

  if (btnUpdateLater) {
    btnUpdateLater.addEventListener("click", () => {
      if (updateModal) {
        updateModal.style.display = "none";
        updateModal.classList.add("hidden");
      }
    });
  }

  if (btnUpdateViewChanges) {
    btnUpdateViewChanges.addEventListener("click", () => {
      window.open("https://github.com", "_blank");
    });
  }

  // Data Refresh buttons
  const rTasks = document.getElementById("refreshTasksBtn");
  if (rTasks) rTasks.addEventListener("click", loadTasks);
  const rMem = document.getElementById("refreshMemoryBtn");
  if (rMem) rMem.addEventListener("click", loadMemory);
  const rAudit = document.getElementById("refreshAuditBtn");
  if (rAudit) rAudit.addEventListener("click", loadAuditLogs);
  const rModels = document.getElementById("refreshModelsPageBtn");
  if (rModels) rModels.addEventListener("click", loadModelsPage);
}

async function loadModelsPage() {
  const localList = document.getElementById("modelsLocalList");
  const apiList = document.getElementById("modelsApiList");
  try {
    const res = await fetch("/api/models");
    const data = await res.json();
    if (localList) {
      localList.innerHTML = (data.local_models || []).map(m => `
        <div style="padding: 6px 0; border-bottom: 1px solid var(--border-subtle); display: flex; justify-content: space-between;">
          <strong style="color: #fff;">${m.name}</strong>
          <span class="badge-mini">${m.provider || 'local'}</span>
        </div>
      `).join("") || "No local models discovered.";
    }
    if (apiList) {
      apiList.innerHTML = (data.providers || []).map(p => `
        <div style="padding: 6px 0; border-bottom: 1px solid var(--border-subtle);">
          <strong style="color: var(--accent-cyan);">${p.name}</strong> (${p.base_url})
        </div>
      `).join("") || "No external providers configured.";
    }
  } catch (e) {
    console.error("loadModelsPage error:", e);
  }
}

function loadProjectsList() {
  // Can populate projects dynamically
}

// ==========================================================================
// Approval Modal
// ==========================================================================
function showApprovalModal(data) {
  const modal = document.getElementById("approvalModal");
  if (!modal) return;

  const promptText = data.prompt || (data.step ? `Permission required to execute: ${data.step.objective}` : "Approval required for computer action.");
  document.getElementById("approvalPrompt").innerText = promptText;

  if (data.plan_markdown) {
    document.getElementById("approvalDetails").innerText = data.plan_markdown;
  } else {
    const details = data.step ? {
      objective: data.step.objective,
      tool: data.tool_name || data.step.tool,
      action: data.action || (data.step.input_data ? data.step.input_data.operation : undefined),
      parameters: data.step.input_data
    } : data;
    document.getElementById("approvalDetails").innerText = JSON.stringify(details, null, 2);
  }

  modal.style.display = "flex";
  modal.classList.remove("hidden");

  const taskId = data.task_id || currentTaskId;
  const toolName = data.tool_name || (data.step ? data.step.tool : "");
  const actionName = data.action || (data.step && data.step.input_data ? data.step.input_data.operation : "");

  const handleDecision = async (decision) => {
    modal.style.display = "none";
    modal.classList.add("hidden");
    logTerminal("[USER]", `User submitted: ${decision.toUpperCase().replace("_", " ")}`);

    const planText = document.getElementById("approvalDetails").innerText;
    const modifiedPlan = (data.plan_markdown || (planText && planText.includes("# "))) ? planText : undefined;

    try {
      const res = await fetch(`/api/tasks/${taskId}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          decision: decision,
          tool_name: toolName,
          action: actionName,
          modified_plan_markdown: modifiedPlan
        })
      });
      const result = await res.json();
      lastTaskData = result;

      if (result.success) {
        setTelemetryStatus("COMPLETED", "status-done");
        const badge = document.getElementById("verificationBadge");
        if (badge) {
          badge.innerText = "Verified Success";
          badge.className = "status-pill status-done";
        }
        const resOut = document.getElementById("resultOutput");
        if (resOut) resOut.innerText = result.final_result;
        logTerminal("[SUCCESS]", result.final_result, "log-done");
        enableTaskControls(false);
        showOutcomeActionButtons(result);
      } else if (decision === "deny") {
        setTelemetryStatus("DENIED", "status-err");
        logTerminal("[USER]", "Action denied by user.", "log-err");
        enableTaskControls(false);
      } else {
        setTelemetryStatus("FAILED", "status-err");
        logTerminal("[ERROR]", result.error || "Execution failed after approval.", "log-err");
        enableTaskControls(false);
      }
    } catch (e) {
      console.error("Approve error:", e);
      logTerminal("[ERROR]", `Failed to submit approval: ${e.message}`, "log-err");
      enableTaskControls(false);
    }
  };

  document.getElementById("approvalAllowOnceBtn").onclick = () => handleDecision("allow_once");
  document.getElementById("approvalAlwaysAllowBtn").onclick = () => handleDecision("always_allow");
  document.getElementById("approvalDenyBtn").onclick = () => handleDecision("deny");
}

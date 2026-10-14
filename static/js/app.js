/**
 * IBM z/OS JCL Generator Studio — Frontend Controller (100% Local Offline)
 */

const state = {
  utilities: {},
  selectedUtility: "IEFBR14",
  dds: [],
  stepQueue: [],
  lastGeneratedJcl: "",
  generatedJclBaseline: "",
  lastFileName: "jclgen01.jcl",
};

const SYSIN_SNIPPETS = {
  DUMMY: "DUMMY",
  SORT_ASC: "  SORT FIELDS=(1,10,CH,A)\n  SUM FIELDS=NONE",
  SORT_DEDUP: "  SORT FIELDS=(1,15,CH,A)\n  SUM FIELDS=NONE",
  SORT_INCLUDE:
    "  INCLUDE COND=(1,3,CH,EQ,C'ACT',AND,20,1,CH,NE,C'X')\n  SORT FIELDS=(4,8,ZD,A)\n  OUTREC FIELDS=(1,80)",
  IDCAMS_DEL_DEF:
    "  DELETE PROD.VSAM.KSDS.CLUSTER CLUSTER PURGE\n" +
    "  IF LASTCC = 8 THEN SET MAXCC = 0\n" +
    "  DEFINE CLUSTER (NAME(PROD.VSAM.KSDS.CLUSTER) -\n" +
    "         INDEXED -\n" +
    "         CYLINDERS(10 5) -\n" +
    "         KEYS(10 0) -\n" +
    "         RECORDSIZE(80 80) -\n" +
    "         SHAREOPTIONS(2 3)) -\n" +
    "    DATA (NAME(PROD.VSAM.KSDS.CLUSTER.DATA)) -\n" +
    "    INDEX (NAME(PROD.VSAM.KSDS.CLUSTER.INDEX))",
  IDCAMS_REPRO: "  REPRO INFILE(INDD) OUTFILE(OUTDD) REPLACE",
  IDCAMS_GDG:
    "  DEFINE GDG (NAME(PROD.BATCH.TRANS.GDG) -\n" +
    "         LIMIT(30) -\n" +
    "         NOEMPTY -\n" +
    "         SCRATCH)",
  IEBCOPY_ALL: "  COPY OUTDD=SYSUT2,INDD=SYSUT1",
  IEBCOPY_SEL: "  COPY OUTDD=SYSUT2,INDD=SYSUT1\n  SELECT MEMBER=(MEM01,MEM02,MEM03)",
  IKJEFT01_DB2:
    "  DSN SYSTEM(DB2P)\n" +
    "  RUN PROGRAM(MYDB2PGM) PLAN(PRODPLAN) -\n" +
    "      LIB('PROD.APPL.LOADLIB')\n" +
    "  END",
};

// Utility helper to get DOM element by ID
function el(id) {
  return document.getElementById(id);
}

// Escape HTML for safe syntax-highlighted preview
function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

// Initialize app by loading utility metadata from the local Python backend
async function initApp() {
  try {
    const res = await fetch("/api/utilities");
    const data = await res.json();
    state.utilities = data.utilities || {};
    renderUtilityRadioButtons();
    selectUtility("IEFBR14");
    bindGlobalEvents();
  } catch (err) {
    console.error("Failed to initialize from backend:", err);
  }
}

// Render all utility radio buttons
function renderUtilityRadioButtons() {
  const container = el("utilityRadioGrid");
  container.innerHTML = "";

  Object.keys(state.utilities).forEach((key) => {
    const u = state.utilities[key];
    const label = document.createElement("label");
    label.className = `utility-radio-item ${state.selectedUtility === key ? "active" : ""}`;
    label.dataset.utility = key;

    label.innerHTML = `
      <input type="radio" name="utilityRadio" value="${key}" ${
      state.selectedUtility === key ? "checked" : ""
    } />
      <div class="utility-radio-meta">
        <span class="utility-radio-name">${u.name}</span>
        <span class="utility-radio-title">${u.title.split("—")[1] || u.title}</span>
      </div>
    `;

    label.addEventListener("click", () => {
      if (state.selectedUtility !== key) {
        selectUtility(key);
      }
    });

    container.appendChild(label);
  });
}

// Handle selecting a utility radio button
function selectUtility(utilityKey) {
  state.selectedUtility = utilityKey;
  const meta = state.utilities[utilityKey];
  if (!meta) return;

  // Highlight active radio card
  document.querySelectorAll(".utility-radio-item").forEach((item) => {
    const isMatch = item.dataset.utility === utilityKey;
    item.classList.toggle("active", isMatch);
    const radio = item.querySelector('input[type="radio"]');
    if (radio) radio.checked = isMatch;
  });

  el("activeUtilityBadge").textContent = meta.name;
  el("utilityDescriptionBox").innerHTML = `<strong>${meta.title}</strong> (${meta.category}): ${meta.description}`;

  // Populate step defaults for this utility
  el("stepName").value = meta.default_step_name || "STEP010";
  el("sysinCards").value = meta.default_sysin || "";
  el("sysinDd").value = utilityKey === "IKJEFT01" ? "SYSTSIN" : "SYSIN";

  // Show/hide Custom Program or IEBUPDTE specific inputs
  el("customPgmRow").classList.toggle("hidden", utilityKey !== "CUSTOM");
  el("iebupdteRow").classList.toggle("hidden", utilityKey !== "IEBUPDTE");

  // Deep clone default DD statements
  state.dds = JSON.parse(JSON.stringify(meta.default_dds || []));
  renderDdList();
  triggerGenerateJcl();
}

// Render dynamic DD statement builder cards
function renderDdList() {
  const container = el("ddListContainer");
  container.innerHTML = "";

  if (state.dds.length === 0) {
    container.innerHTML = `<p class="help-hint">No DD statements configured for this step. Click "+ Add DD Statement" to add one.</p>`;
    return;
  }

  state.dds.forEach((dd, idx) => {
    const card = document.createElement("div");
    card.className = "dd-item";

    card.innerHTML = `
      <div class="dd-item-header">
        <span class="dd-item-title">//${escapeHtml(dd.dd_name || "DD" + (idx + 1))} DD Statement #${idx + 1}</span>
        <div class="dd-quick-toggles">
          <label class="switch-label">
            <input type="checkbox" data-idx="${idx}" data-field="dummy" ${dd.dummy ? "checked" : ""} />
            <span class="switch-slider"></span>
            <span class="toggle-title">DUMMY</span>
          </label>
          <label class="switch-label">
            <input type="checkbox" data-idx="${idx}" data-field="include_space" ${dd.include_space ? "checked" : ""} />
            <span class="switch-slider"></span>
            <span class="toggle-title">SPACE=</span>
          </label>
          <label class="switch-label">
            <input type="checkbox" data-idx="${idx}" data-field="include_dcb" ${dd.include_dcb ? "checked" : ""} />
            <span class="switch-slider"></span>
            <span class="toggle-title">DCB=</span>
          </label>
          <button type="button" class="btn btn-sm btn-danger" data-remove-dd="${idx}">Remove</button>
        </div>
      </div>

      <div class="form-row four-col">
        <div class="form-group">
          <label>DD Name / Label</label>
          <input type="text" maxlength="8" class="mono-input" data-idx="${idx}" data-field="dd_name" value="${escapeHtml(dd.dd_name || "")}" />
        </div>
        <div class="form-group" style="grid-column: span 2;">
          <label>Dataset Name (DSN=)</label>
          <input type="text" class="mono-input" data-idx="${idx}" data-field="dsn" value="${escapeHtml(dd.dsn || "")}" placeholder="PROD.DATA.FILE or &&TEMP" ${dd.dummy ? "disabled" : ""} />
        </div>
        <div class="form-group">
          <label>Or SYSOUT= (Optional)</label>
          <input type="text" maxlength="4" class="mono-input" data-idx="${idx}" data-field="sysout" value="${escapeHtml(dd.sysout || "")}" placeholder="e.g. * or A" ${dd.dummy ? "disabled" : ""} />
        </div>
      </div>

      <div class="form-row four-col ${dd.dummy || dd.sysout ? "hidden" : ""}">
        <div class="form-group">
          <label>DISP Status</label>
          <select class="mono-input" data-idx="${idx}" data-field="disp_status">
            <option value="SHR" ${dd.disp_status === "SHR" ? "selected" : ""}>SHR (Share Existing)</option>
            <option value="NEW" ${dd.disp_status === "NEW" ? "selected" : ""}>NEW (Allocate New)</option>
            <option value="OLD" ${dd.disp_status === "OLD" ? "selected" : ""}>OLD (Exclusive)</option>
            <option value="MOD" ${dd.disp_status === "MOD" ? "selected" : ""}>MOD (Append/Create)</option>
          </select>
        </div>
        <div class="form-group">
          <label>DISP Normal</label>
          <select class="mono-input" data-idx="${idx}" data-field="disp_normal">
            <option value="" ${dd.disp_normal === "" ? "selected" : ""}>(Omit)</option>
            <option value="CATLG" ${dd.disp_normal === "CATLG" ? "selected" : ""}>CATLG</option>
            <option value="KEEP" ${dd.disp_normal === "KEEP" ? "selected" : ""}>KEEP</option>
            <option value="DELETE" ${dd.disp_normal === "DELETE" ? "selected" : ""}>DELETE</option>
            <option value="PASS" ${dd.disp_normal === "PASS" ? "selected" : ""}>PASS</option>
            <option value="UNCATLG" ${dd.disp_normal === "UNCATLG" ? "selected" : ""}>UNCATLG</option>
          </select>
        </div>
        <div class="form-group">
          <label>DISP Abnormal</label>
          <select class="mono-input" data-idx="${idx}" data-field="disp_abnormal">
            <option value="" ${dd.disp_abnormal === "" ? "selected" : ""}>(Omit)</option>
            <option value="DELETE" ${dd.disp_abnormal === "DELETE" ? "selected" : ""}>DELETE</option>
            <option value="CATLG" ${dd.disp_abnormal === "CATLG" ? "selected" : ""}>CATLG</option>
            <option value="KEEP" ${dd.disp_abnormal === "KEEP" ? "selected" : ""}>KEEP</option>
          </select>
        </div>
        <div class="form-group">
          <label>UNIT / VOL=SER</label>
          <div style="display:flex; gap:6px;">
            <input type="text" class="mono-input" style="width:55%;" data-idx="${idx}" data-field="unit" value="${escapeHtml(dd.unit || "SYSDA")}" placeholder="SYSDA" />
            <input type="text" class="mono-input" style="width:45%;" data-idx="${idx}" data-field="vol_ser" value="${escapeHtml(dd.vol_ser || "")}" placeholder="VOLSER" />
          </div>
        </div>
      </div>

      <!-- SPACE Subpanel -->
      <div class="dd-subpanel ${dd.include_space && !dd.dummy ? "" : "hidden"}">
        <div class="form-row four-col">
          <div class="form-group">
            <label>SPACE Unit</label>
            <select class="mono-input" data-idx="${idx}" data-field="space_unit">
              <option value="CYL" ${dd.space_unit === "CYL" ? "selected" : ""}>CYL (Cylinders)</option>
              <option value="TRK" ${dd.space_unit === "TRK" ? "selected" : ""}>TRK (Tracks)</option>
              <option value="BLK" ${dd.space_unit === "BLK" ? "selected" : ""}>BLK (Blocks)</option>
            </select>
          </div>
          <div class="form-group">
            <label>Primary Qty</label>
            <input type="number" min="1" class="mono-input" data-idx="${idx}" data-field="space_pri" value="${escapeHtml(dd.space_pri || "10")}" />
          </div>
          <div class="form-group">
            <label>Secondary Qty</label>
            <input type="number" min="0" class="mono-input" data-idx="${idx}" data-field="space_sec" value="${escapeHtml(dd.space_sec || "5")}" />
          </div>
          <div class="form-group">
            <label>PDS Dir Blocks (0=Seq)</label>
            <input type="number" min="0" class="mono-input" data-idx="${idx}" data-field="space_dir" value="${escapeHtml(dd.space_dir || "0")}" />
          </div>
        </div>
      </div>

      <!-- DCB Subpanel -->
      <div class="dd-subpanel ${dd.include_dcb && !dd.dummy ? "" : "hidden"}">
        <div class="form-row four-col">
          <div class="form-group">
            <label>RECFM=</label>
            <select class="mono-input" data-idx="${idx}" data-field="recfm">
              <option value="FB" ${dd.recfm === "FB" ? "selected" : ""}>FB (Fixed Blocked)</option>
              <option value="VB" ${dd.recfm === "VB" ? "selected" : ""}>VB (Variable Blocked)</option>
              <option value="FBA" ${dd.recfm === "FBA" ? "selected" : ""}>FBA (Fixed ANSI Print)</option>
              <option value="VBA" ${dd.recfm === "VBA" ? "selected" : ""}>VBA (Var ANSI Print)</option>
              <option value="F" ${dd.recfm === "F" ? "selected" : ""}>F (Fixed Unblocked)</option>
              <option value="U" ${dd.recfm === "U" ? "selected" : ""}>U (Undefined / Loadlib)</option>
            </select>
          </div>
          <div class="form-group">
            <label>LRECL=</label>
            <input type="number" min="1" class="mono-input" data-idx="${idx}" data-field="lrecl" value="${escapeHtml(dd.lrecl || "80")}" />
          </div>
          <div class="form-group">
            <label>BLKSIZE= (0=System Opt)</label>
            <input type="number" min="0" class="mono-input" data-idx="${idx}" data-field="blksize" value="${escapeHtml(dd.blksize || "0")}" />
          </div>
          <div class="form-group">
            <label>DSNTYPE= (Optional)</label>
            <select class="mono-input" data-idx="${idx}" data-field="dsntype">
              <option value="" ${!dd.dsntype ? "selected" : ""}>(Default)</option>
              <option value="PDS" ${dd.dsntype === "PDS" ? "selected" : ""}>PDS</option>
              <option value="LIBRARY" ${dd.dsntype === "LIBRARY" ? "selected" : ""}>LIBRARY (PDSE)</option>
              <option value="LARGE" ${dd.dsntype === "LARGE" ? "selected" : ""}>LARGE</option>
            </select>
          </div>
        </div>
      </div>
    `;

    container.appendChild(card);
  });

  // Attach listeners to DD inputs
  container.querySelectorAll("[data-idx]").forEach((input) => {
    const idx = parseInt(input.dataset.idx, 10);
    const field = input.dataset.field;

    input.addEventListener("input", () => {
      if (input.type === "checkbox") {
        state.dds[idx][field] = input.checked;
        renderDdList();
      } else {
        state.dds[idx][field] = input.value;
        // If disp_status changed to NEW, auto-populate CATLG/DELETE if empty
        if (field === "disp_status" && input.value === "NEW") {
          if (!state.dds[idx].disp_normal) state.dds[idx].disp_normal = "CATLG";
          if (!state.dds[idx].disp_abnormal) state.dds[idx].disp_abnormal = "DELETE";
          state.dds[idx].include_space = true;
          state.dds[idx].include_dcb = true;
          renderDdList();
        } else if (field === "disp_status" && input.value === "SHR") {
          state.dds[idx].disp_normal = "";
          state.dds[idx].disp_abnormal = "";
          renderDdList();
        }
      }
      triggerGenerateJcl();
    });
  });

  container.querySelectorAll("[data-remove-dd]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const idx = parseInt(btn.dataset.removeDd, 10);
      state.dds.splice(idx, 1);
      renderDdList();
      triggerGenerateJcl();
    });
  });
}

// Gather current Job Card configuration from UI controls
function collectJobConfig() {
  return {
    job_name: el("jobName").value,
    file_name: el("fileName").value,
    job_desc: el("jobDesc").value,
    use_acct: el("useAcct").checked,
    acct_info: el("acctInfo").value,
    use_pgmr: el("usePgmr").checked,
    pgmr_name: el("pgmrName").value,
    use_class: el("useClass").checked,
    job_class: el("jobClass").value,
    use_msgclass: el("useMsgclass").checked,
    msgclass: el("msgclass").value,
    use_msglevel: el("useMsglevel").checked,
    msglevel: el("msglevel").value,
    use_notify: el("useNotify").checked,
    notify: el("notify").value,
    use_region: el("useRegion").checked,
    region: el("region").value,
    use_time: el("useTime").checked,
    time_val: el("timeVal").value,
    use_typrun: el("useTyprun").checked,
    typrun: el("typrun").value,
    use_restart: el("useRestart").checked,
    restart: el("restart").value,
    use_jcllib: el("useJcllib").checked,
    jcllib_dsn: el("jcllibDsn").value,
  };
}

// Gather current active step configuration
function collectCurrentStep() {
  return {
    utility: state.selectedUtility,
    step_name: el("stepName").value,
    sysprint_dd: el("sysprintDd").value,
    sysin_dd: el("sysinDd").value,
    sysout_class: el("sysoutClass").value,
    program_name: el("programName").value,
    parm: el("parmVal").value,
    steplib_dsn: el("steplibDsn").value,
    updte_parm: el("updteParm").value,
    use_cond: el("useCond").checked,
    cond_type: el("condType").value,
    cond_rc: el("condRc").value,
    cond_op: el("condOp").value,
    cond_step: el("condStep").value,
    use_if_else: el("useIfElse").checked,
    if_label: el("ifLabel").value,
    if_condition: el("ifCondition").value,
    include_else: el("includeElse").checked,
    else_step_name: el("elseStepName").value,
    else_pgm: el("elsePgm").value,
    else_dd_dsn: el("elseDdDsn").value,
    else_comment: el("elseComment").value,
    dds: JSON.parse(JSON.stringify(state.dds)),
    sysin_cards: el("sysinCards").value,
  };
}

// Request JCL generation from Python backend and update live preview
async function triggerGenerateJcl() {
  const jobConfig = collectJobConfig();
  const currentStep = collectCurrentStep();

  const stepsToRender =
    state.stepQueue.length > 0 ? state.stepQueue : [currentStep];

  try {
    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        job_config: jobConfig,
        steps: stepsToRender,
      }),
    });
    const data = await res.json();
    if (!res.ok) {
      state.lastGeneratedJcl = "";
      renderJclPreview({ jcl: "", file_name: "job.jcl", warnings: [data.error || "Unable to generate JCL."] });
      return;
    }
    state.lastGeneratedJcl = data.jcl || "";
    state.lastFileName = data.file_name || "job.jcl";
    renderJclPreview(data);
  } catch (err) {
    console.error("Failed to generate JCL:", err);
    const status = el("validationStatus");
    if (status) {
      status.className = "validation-warn";
      status.textContent = "Unable to generate JCL. Check the input values and try again.";
    }
  }
}

// Syntax-highlight and render JCL lines with line numbers
function renderJclPreview(data) {
  const rawJcl = data.jcl || "";
  const output = el("jclPreviewOutput");
  output.value = rawJcl;
  state.lastGeneratedJcl = rawJcl;
  state.generatedJclBaseline = rawJcl;
  state.lastFileName = data.file_name || state.lastFileName || "job.jcl";
  updateEditorMeta(data);
  const valEl = el("validationStatus");
  if (data.warnings && data.warnings.length > 0) {
    valEl.className = "validation-warn";
    valEl.textContent = "Warning: " + data.warnings[0];
  } else {
    valEl.className = "validation-ok";
    valEl.textContent = "Generated JCL — edit as needed before download";
  }
}

function updateEditorMeta(data = {}) {
  const value = el("jclPreviewOutput").value;
  const lines = value.split("\n");
  const longest = lines.reduce((max, line) => Math.max(max, line.length), 0);
  const edited = value !== (state.generatedJclBaseline || "");
  el("previewMeta").textContent = lines.length + " lines • " + Math.max(1, state.stepQueue.length + 1) + " step(s) • " + (edited ? "Edited locally" : "Ready to edit") + " • " + state.lastFileName;
  const valEl = el("validationStatus");
  if (longest > 71) { valEl.className = "validation-warn"; valEl.textContent = "Warning: longest line is " + longest + " columns; review before submitting"; }
  else if (edited) { valEl.className = "validation-warn"; valEl.textContent = "Local edits detected — review JCL syntax before submitting"; }
  else if (!data.warnings || !data.warnings.length) { valEl.className = "validation-ok"; valEl.textContent = "JCL generated — ready for review"; }
}
// Render multi-step queue items
function renderStepQueue() {
  const container = el("stepQueueContainer");
  container.innerHTML = "";
  if (state.stepQueue.length === 0) {
    container.innerHTML = `<div class="help-hint">Queue is empty (Live Preview is rendering your active step above).</div>`;
    return;
  }

  state.stepQueue.forEach((st, i) => {
    const row = document.createElement("div");
    row.className = "queue-item";
    const condBadge = st.use_if_else
      ? `[IF ${st.if_condition}]`
      : st.use_cond
      ? `[COND]`
      : "";
    row.innerHTML = `
      <div class="queue-item-info">
        <span class="badge">#${i + 1}</span>
        <strong>//${escapeHtml(st.step_name)}</strong>
        <span>EXEC PGM=${escapeHtml(st.utility === "CUSTOM" ? st.program_name : st.utility)}</span>
        <span style="color:#facc15;">${escapeHtml(condBadge)}</span>
        <span style="color:#94a3b8;">(${st.dds.length} DDs)</span>
      </div>
      <div>
        <button type="button" class="btn btn-sm btn-danger" data-del-step="${i}">Remove</button>
      </div>
    `;
    container.appendChild(row);
  });

  container.querySelectorAll("[data-del-step]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const idx = parseInt(btn.dataset.delStep, 10);
      state.stepQueue.splice(idx, 1);
      renderStepQueue();
      triggerGenerateJcl();
    });
  });
}

// Bind all UI event listeners
function bindGlobalEvents() {
  // Sync Job Name to default output filename if filename wasn't manually customized
  el("jobName").addEventListener("input", () => {
    const clean = el("jobName").value.trim().toLowerCase() || "job";
    el("fileName").value = `${clean}.jcl`;
    triggerGenerateJcl();
  });

  // Enable/disable paired inputs when Job Card toggles change
  const togglePairs = [
    ["useAcct", "acctInfo"],
    ["usePgmr", "pgmrName"],
    ["useClass", "jobClass"],
    ["useMsgclass", "msgclass"],
    ["useMsglevel", "msglevel"],
    ["useNotify", "notify"],
    ["useRegion", "region"],
    ["useTime", "timeVal"],
    ["useTyprun", "typrun"],
    ["useRestart", "restart"],
    ["useJcllib", "jcllibDsn"],
  ];

  togglePairs.forEach(([chkId, inputId]) => {
    const chk = el(chkId);
    const inp = el(inputId);
    if (!chk || !inp) return;
    inp.disabled = !chk.checked;
    chk.addEventListener("change", () => {
      inp.disabled = !chk.checked;
      triggerGenerateJcl();
    });
    inp.addEventListener("input", triggerGenerateJcl);
    inp.addEventListener("change", triggerGenerateJcl);
  });

  // Conditional execution toggles
  el("useCond").addEventListener("change", (e) => {
    el("condConfigBody").classList.toggle("hidden", !e.target.checked);
    triggerGenerateJcl();
  });

  el("condType").addEventListener("change", (e) => {
    const isCode = e.target.value === "CODE";
    el("condRcGroup").classList.toggle("hidden", !isCode);
    el("condOpGroup").classList.toggle("hidden", !isCode);
    el("condStepGroup").classList.toggle("hidden", !isCode);
    triggerGenerateJcl();
  });

  el("useIfElse").addEventListener("change", (e) => {
    el("ifElseConfigBody").classList.toggle("hidden", !e.target.checked);
    triggerGenerateJcl();
  });

  el("ifPreset").addEventListener("change", (e) => {
    el("ifCondition").value = e.target.value;
    triggerGenerateJcl();
  });

  el("includeElse").addEventListener("change", (e) => {
    el("elseBranchFields").classList.toggle("hidden", !e.target.checked);
    triggerGenerateJcl();
  });

  // General step fields
  [
    "fileName",
    "jobDesc",
    "stepName",
    "sysprintDd",
    "sysinDd",
    "sysoutClass",
    "programName",
    "parmVal",
    "steplibDsn",
    "updteParm",
    "condRc",
    "condOp",
    "condStep",
    "ifLabel",
    "ifCondition",
    "elseStepName",
    "elsePgm",
    "elseDdDsn",
    "elseComment",
    "sysinCards",
  ].forEach((id) => {
    const node = el(id);
    if (node) {
      node.addEventListener("input", triggerGenerateJcl);
      node.addEventListener("change", triggerGenerateJcl);
    }
  });

  // Add DD Statement button
  el("addDdBtn").addEventListener("click", () => {
    const nextNum = state.dds.length + 1;
    state.dds.push({
      dd_name: `DD${nextNum}`,
      dsn: `PROD.USER.DATASET.FILE0${nextNum}`,
      disp_status: "SHR",
      disp_normal: "",
      disp_abnormal: "",
      include_space: false,
      space_unit: "CYL",
      space_pri: "10",
      space_sec: "5",
      space_dir: "0",
      include_dcb: false,
      recfm: "FB",
      lrecl: "80",
      blksize: "0",
      unit: "SYSDA",
      vol_ser: "",
      dsntype: "",
      dummy: false,
      sysout: "",
    });
    renderDdList();
    triggerGenerateJcl();
  });

  // SYSIN Control Card Snippet selector
  el("sysinSnippetSelect").addEventListener("change", (e) => {
    const key = e.target.value;
    if (key && SYSIN_SNIPPETS[key] !== undefined) {
      el("sysinCards").value = SYSIN_SNIPPETS[key];
      triggerGenerateJcl();
    }
    e.target.value = "";
  });

  // Multi-step queue buttons
  el("addStepToQueueBtn").addEventListener("click", () => {
    const stepCopy = collectCurrentStep();
    state.stepQueue.push(stepCopy);
    // Auto-increment step name for convenience
    const nextIdx = (state.stepQueue.length + 1) * 10;
    el("stepName").value = `STEP${String(nextIdx).padStart(3, "0")}`;
    renderStepQueue();
    triggerGenerateJcl();
  });

  el("clearQueueBtn").addEventListener("click", () => {
    state.stepQueue = [];
    renderStepQueue();
    triggerGenerateJcl();
  });

  // Browser-only editing: manual changes are used by copy and download.
  el("jclPreviewOutput").addEventListener("input", () => {
    state.lastGeneratedJcl = el("jclPreviewOutput").value;
    updateEditorMeta();
  });
  el("revertJclBtn").addEventListener("click", () => {
    el("jclPreviewOutput").value = state.generatedJclBaseline || "";
    state.lastGeneratedJcl = el("jclPreviewOutput").value;
    updateEditorMeta();
    showToast("Reverted to generated JCL.");
  });

  // Copy JCL button
  el("copyJclBtn").addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(el("jclPreviewOutput").value);
      showToast("Copied JCL to clipboard!");
    } catch {
      showToast("Clipboard access is unavailable in this browser.");
    }
  });

  // Download .JCL file directly in browser
  el("downloadJclBtn").addEventListener("click", () => {
    const editedJcl = el("jclPreviewOutput").value;
    if (!editedJcl.trim()) { showToast("There is no JCL to download. Generate a job first."); return; }
    const blob = new Blob([editedJcl], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = state.lastFileName || "job.jcl";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast(`Downloaded ${state.lastFileName}`);
  });

  // Reset all button
  el("resetAllBtn").addEventListener("click", () => {
    state.stepQueue = [];
    renderStepQueue();
    selectUtility("IEFBR14");
  });

  // Dark mode toggle
  const dmBtn = el("darkModeToggle");
  if (dmBtn) {
    const root = document.documentElement;
    const updateIcon = () => {
      const isDark = root.getAttribute("data-theme") === "dark";
      const label = el("themeToggleLabel");
      const icon = dmBtn.querySelector(".theme-icon");
      if (label) label.textContent = isDark ? "Light mode" : "Dark mode";
      if (icon) icon.textContent = isDark ? "☀" : "◐";
      dmBtn.setAttribute("aria-label", isDark ? "Switch to light mode" : "Switch to dark mode");
      dmBtn.title = isDark ? "Switch to light mode" : "Switch to dark mode";
    };
    updateIcon();
    dmBtn.addEventListener("click", () => {
      const isDark = root.getAttribute("data-theme") === "dark";
      const next = isDark ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("jcl-theme", next); } catch (_) {}
      updateIcon();
    });
  }
}

function showToast(msg) {
  const node = el("saveNotification");
  node.textContent = msg;
  setTimeout(() => {
    node.textContent = "";
  }, 3500);
}

document.addEventListener("DOMContentLoaded", initApp);

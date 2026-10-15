-- @description creaper chat: talk to Claude from a dockable panel inside REAPER
-- @author nickcapron
-- @version 0.19.1
-- @link https://github.com/nickcapron/creaper
-- @about
--   A chat panel for creaper. Messages go to your own Claude Code (your Claude
--   plan), which can only use the creaper tools: it works in this REAPER
--   project and nothing else on your computer. Needs ReaImGui, Claude Code and
--   `creaper install-bridge`.

if not reaper.ImGui_GetBuiltinPath then
  reaper.ShowMessageBox(
    "The creaper chat panel needs the ReaImGui extension (version 0.9 or newer).\n\n"
      .. "1. Install ReaPack from reapack.com (if you don't have it).\n"
      .. "2. Extensions > ReaPack > Browse packages, search for ReaImGui, install it.\n"
      .. "3. Restart REAPER and run this script again.",
    "creaper chat", 0)
  return
end
package.path = reaper.ImGui_GetBuiltinPath() .. "/?.lua"
local ImGui = require "imgui" "0.9"

local SEP = package.config:sub(1, 1)
local SCRIPT_DIR = debug.getinfo(1, "S").source:match("^@(.*[\\/])") or ""
local json = dofile(SCRIPT_DIR .. "creaper_json.lua")

local function join(...) return table.concat({ ... }, SEP) end
math.randomseed(os.time())
local BRIDGE_DIR = join(reaper.GetResourcePath(), "creaper")
local CHAT_DIR = join(BRIDGE_DIR, "chat")
local CONFIG_PATH = join(BRIDGE_DIR, "chat_config.json")
local STATE_PATH = join(BRIDGE_DIR, "chat_state.json")
local BRIDGE_SCRIPT = SCRIPT_DIR .. "creaper_bridge.lua"
reaper.RecursiveCreateDirectory(CHAT_DIR, 0)

local COLOR = {
  user = 0x2EE6C5FF,
  error = 0xFF7B72FF,
  info = 0xD8B65CFF,
  ok = 0x7EE787FF,
  muted = 0x8B949EFF,
}
local MAX_MESSAGES = 300

------------------------------------------------------------------- files

local function read_file(path)
  local f = io.open(path, "rb")
  if not f then return nil end
  local data = f:read("a")
  f:close()
  return data
end

-- Atomic replace that tolerates Windows briefly locking a file another program
-- is reading (see the bridge's write_file). Returns false rather than raising.
local function write_file(path, text)
  local tmp = path .. ".panel.tmp"
  local f = io.open(tmp, "wb")
  if not f then return false end
  f:write(text)
  f:close()
  for _ = 1, 5 do
    os.remove(path)
    if os.rename(tmp, path) then return true end
  end
  os.remove(tmp)
  local direct = io.open(path, "wb")
  if not direct then return false end
  direct:write(text)
  direct:close()
  return true
end

local function read_json(path)
  local data = read_file(path)
  if not data or data == "" then return nil end
  local ok, value = pcall(json.decode, data)
  return ok and value or nil
end

------------------------------------------------------------------- state

local config = read_json(CONFIG_PATH)
local state = read_json(STATE_PATH) or {}
state.messages = state.messages or {}
local turn = state.turn -- the turn in progress, kept so reopening the panel picks it up
local input = ""
local scroll_to_bottom = true
local focus_input = true
local dock_request -- nil, or the dock id to apply next frame

local function save_state()
  while #state.messages > MAX_MESSAGES do table.remove(state.messages, 1) end
  state.turn = turn
  local ok, encoded = pcall(json.encode, state)
  if ok then write_file(STATE_PATH, encoded) end
end

local function add_message(role, text, extra)
  local m = extra or {}
  m.role, m.text = role, text
  state.messages[#state.messages + 1] = m
  scroll_to_bottom = true
  return m
end

------------------------------------------------------------------ bridge

-- The bridge pauses while REAPER is busy (renders, heavy plugins), so a late
-- heartbeat isn't proof it stopped; only start another after a long silence.
local function bridge_age()
  local beat = tonumber(reaper.GetExtState("creaper", "heartbeat"))
  return beat and reaper.time_precise() - beat or math.huge
end

local function bridge_running() return bridge_age() < 3 end

local function start_bridge()
  if bridge_age() < 15 or not reaper.file_exists(BRIDGE_SCRIPT) then return end
  local command = reaper.AddRemoveReaScript(true, 0, BRIDGE_SCRIPT, true)
  if command and command > 0 then reaper.Main_OnCommand(command, 0) end
end

------------------------------------------------------------------- turns

local function answer_path(confirm_path) return (confirm_path:gsub("%.json$", ".answer")) end

local function cleanup_turn(t)
  for _, path in ipairs({ t.request, t.events, t.cancel }) do os.remove(path) end
  if t.confirm then
    os.remove(t.confirm)
    os.remove(answer_path(t.confirm))
  end
end

local function start_turn(prompt)
  if not config or not config.python then
    add_message("error", "creaper isn't set up for chat yet. Run `creaper install-bridge` in a terminal, then reopen this panel.")
    return
  end
  local id = string.format("%d_%04d", os.time(), math.random(0, 9999))
  local t = {
    request = join(CHAT_DIR, "turn_" .. id .. ".json"),
    events = join(CHAT_DIR, "turn_" .. id .. ".jsonl"),
    cancel = join(CHAT_DIR, "turn_" .. id .. ".cancel"),
    confirm = join(CHAT_DIR, "turn_" .. id .. ".confirm.json"),
    offset = 0,
    started = os.time(),
    got_event = false,
  }
  local written = write_file(t.request, json.encode({
    prompt = prompt,
    session_id = state.session_id,
    events = t.events,
    cancel = t.cancel,
    confirm = t.confirm,
    resource_path = reaper.GetResourcePath(),
    claude = config.claude,
    model = config.model,
  }))
  if not written then
    add_message("error", "Couldn't write to " .. CHAT_DIR .. ", so the message wasn't sent.")
    return
  end
  reaper.ExecProcess(string.format('"%s" -m creaper chat-turn "%s"', config.python, t.request), -1)
  turn = t
  save_state()
end

local function find_tool_message(id)
  for i = #state.messages, 1, -1 do
    local m = state.messages[i]
    if m.role == "tool" and m.id == id then return m end
  end
end

local function current_reply()
  local last = state.messages[#state.messages]
  if last and last.role == "assistant" and last.turn == turn.started then return last end
  return add_message("assistant", "", { turn = turn.started })
end

local function handle_event(ev)
  turn.got_event = true
  if ev.t == "session" then
    state.session_id = ev.id
  elseif ev.t == "text_start" then
    local last = state.messages[#state.messages]
    if not (last and last.role == "assistant" and last.text == "") then
      add_message("assistant", "", { turn = turn.started })
    end
  elseif ev.t == "text" then
    local reply = current_reply()
    reply.text = reply.text .. (ev.text or "")
    scroll_to_bottom = true
  elseif ev.t == "tool" then
    add_message("tool", ev.summary or "?", { id = ev.id })
  elseif ev.t == "tool_error" then
    local m = find_tool_message(ev.id)
    if m then m.error = ev.message else add_message("error", ev.message or "a tool failed") end
  elseif ev.t == "usage" then
    state.usage = { five_hour = ev.five_hour, seven_day = ev.seven_day }
  elseif ev.t == "info" then
    add_message("info", ev.message or "")
  elseif ev.t == "error" then
    add_message("error", ev.message or "something went wrong")
  elseif ev.t == "done" then
    if ev.cancelled then add_message("info", "Stopped.") end
    -- Drop reply blocks that stayed empty (e.g. a tool call with no text).
    for i = #state.messages, 1, -1 do
      local m = state.messages[i]
      if m.role == "assistant" and m.text:match("^%s*$") then table.remove(state.messages, i) end
    end
    cleanup_turn(turn)
    turn = nil
    save_state()
  end
end

local function poll_turn()
  if not turn then return end
  local f = io.open(turn.events, "rb")
  if f then
    f:seek("set", turn.offset)
    local chunk = f:read("a") or ""
    f:close()
    local last_newline = chunk:match(".*()\n")
    if last_newline then
      turn.offset = turn.offset + last_newline
      for line in chunk:sub(1, last_newline):gmatch("[^\n]+") do
        local ok, ev = pcall(json.decode, line)
        if ok and type(ev) == "table" then
          handle_event(ev)
          if not turn then return end
        end
      end
    end
  end
  if not turn.got_event and os.time() - turn.started > 45 then
    add_message("error", "The chat helper didn't start. Check that creaper is installed for "
      .. tostring(config and config.python) .. " (run `creaper install-bridge` again).")
    cleanup_turn(turn)
    turn = nil
    save_state()
  end
end

local function stop_turn()
  if turn then write_file(turn.cancel, "stop") end
end

-- A risky tool (running an arbitrary action, deleting a track) waiting for the user.
local function pending_confirmation()
  if not turn or not turn.confirm then return nil end
  local request = read_json(turn.confirm)
  if request and request.id ~= turn.answered then return request end
  return nil
end

local function answer_confirmation(request, allow)
  write_file(answer_path(turn.confirm), json.encode({ id = request.id, allow = allow }))
  turn.answered = request.id
  add_message("info", (allow and "Allowed: " or "Declined: ") .. request.action)
end

local function new_chat()
  if turn then return end
  state.session_id = nil
  state.messages = {}
  save_state()
end

-------------------------------------------------------------------- brand

-- The creaper mark (as in assets/make_brand.py): waveform bars sweeping around
-- a "c", with a playhead dot in its opening. Drawn live so it's sharp at any size.
local TEAL, VIOLET, PINK = { 46, 230, 197 }, { 139, 92, 246 }, { 244, 114, 182 }

local function rgba(c, alpha)
  return (math.floor(c[1] + 0.5) << 24) | (math.floor(c[2] + 0.5) << 16)
    | (math.floor(c[3] + 0.5) << 8) | math.floor((alpha or 1) * 255 + 0.5)
end

local function mix(a, b, t)
  return { a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t, a[3] + (b[3] - a[3]) * t }
end

-- Bars in the icon's units (ring radius 150), plus the mark's bounding box.
local MARK = { radius = 150, dot = 15, bars = {} }
do
  local start, stop = math.rad(42), math.rad(318)
  local x0, x1, y0, y1 = 0, MARK.radius + MARK.dot, 0, 0
  for i = 0, 29 do
    local t = i / 29
    local angle = start + (stop - start) * t
    local wave = 0.55 + 0.45 * math.abs(math.sin(i * 0.9) * 0.7 + math.sin(i * 0.37 + 1.0) * 0.3)
    local taper = math.sin(math.pi * (0.15 + 0.85 * t)) ^ 0.6
    local bar = {
      dx = math.cos(angle), dy = -math.sin(angle), half = 16 + 46 * wave * taper,
      color = rgba(t < 0.5 and mix(TEAL, VIOLET, t * 2) or mix(VIOLET, PINK, (t - 0.5) * 2)),
    }
    local outer = MARK.radius + bar.half + 5.5
    x0, x1 = math.min(x0, bar.dx * outer), math.max(x1, bar.dx * outer)
    y0, y1 = math.min(y0, bar.dy * outer), math.max(y1, bar.dy * outer)
    MARK.bars[#MARK.bars + 1] = bar
  end
  MARK.left, MARK.top, MARK.width, MARK.height = x0, y0, x1 - x0, y1 - y0
end

-- Draws the mark with its top-left at (x, y), `height` pixels tall; returns its width.
-- `glow` (0 to 1) sets how brightly the playhead shines.
local function draw_mark(dl, x, y, height, glow)
  local s = height / MARK.height
  local cx, cy = x - MARK.left * s, y - MARK.top * s
  local width = math.max(1.2, 11 * s)
  for _, bar in ipairs(MARK.bars) do
    local inner, outer = (MARK.radius - bar.half) * s, (MARK.radius + bar.half) * s
    local ax, ay, bx, by = cx + bar.dx * inner, cy + bar.dy * inner, cx + bar.dx * outer, cy + bar.dy * outer
    ImGui.DrawList_AddLine(dl, ax, ay, bx, by, bar.color, width)
    if width >= 3 then -- round caps, visible only at larger sizes
      ImGui.DrawList_AddCircleFilled(dl, ax, ay, width / 2, bar.color)
      ImGui.DrawList_AddCircleFilled(dl, bx, by, width / 2, bar.color)
    end
  end
  local px, r = cx + MARK.radius * s, math.max(1.5, MARK.dot * s)
  for k = 4, 1, -1 do
    ImGui.DrawList_AddCircleFilled(dl, px, cy, r * (1 + 0.5 * k), rgba(TEAL, 0.08 * (glow or 1)))
  end
  ImGui.DrawList_AddCircleFilled(dl, px, cy, r, rgba(TEAL))
  return MARK.width * s
end

-- The playhead pulses while Claude is working.
local function glow()
  if not turn then return 1 end
  return 0.6 + 0.9 * (0.5 + 0.5 * math.sin(reaper.time_precise() * 4))
end

-- Brand colours for the window, pushed around Begin/End.
local THEME = {
  { ImGui.Col_WindowBg, 0x0E1117FF },
  { ImGui.Col_ChildBg, 0x00000000 },
  { ImGui.Col_TitleBg, 0x0E1117FF },
  { ImGui.Col_TitleBgActive, 0x181E2AFF },
  { ImGui.Col_FrameBg, 0x181E2AFF },
  { ImGui.Col_FrameBgHovered, 0x1F2736FF },
  { ImGui.Col_FrameBgActive, 0x222B3CFF },
  { ImGui.Col_Button, rgba(VIOLET, 0.55) },
  { ImGui.Col_ButtonHovered, rgba(VIOLET, 0.8) },
  { ImGui.Col_ButtonActive, rgba(VIOLET, 1) },
  { ImGui.Col_Header, rgba(VIOLET, 0.3) },
  { ImGui.Col_HeaderHovered, rgba(VIOLET, 0.35) },
  { ImGui.Col_HeaderActive, rgba(VIOLET, 0.55) },
  { ImGui.Col_Separator, rgba(VIOLET, 0.35) },
  { ImGui.Col_TextSelectedBg, rgba(TEAL, 0.3) },
  { ImGui.Col_ScrollbarGrab, rgba(VIOLET, 0.35) },
  { ImGui.Col_ScrollbarGrabHovered, rgba(VIOLET, 0.55) },
  { ImGui.Col_ScrollbarGrabActive, rgba(VIOLET, 0.75) },
}

local function push_theme(ctx)
  for _, c in ipairs(THEME) do ImGui.PushStyleColor(ctx, c[1], c[2]) end
  ImGui.PushStyleVar(ctx, ImGui.StyleVar_FrameRounding, 5)
  ImGui.PushStyleVar(ctx, ImGui.StyleVar_ScrollbarRounding, 5)
end

local function pop_theme(ctx)
  ImGui.PopStyleVar(ctx, 2)
  ImGui.PopStyleColor(ctx, #THEME)
end

----------------------------------------------------------------------- UI

local ctx = ImGui.CreateContext("creaper", ImGui.ConfigFlags_DockingEnable)
local FONT_TITLE = ImGui.CreateFont("sans-serif", 30, ImGui.FontFlags_Bold)
local FONT_NAME = ImGui.CreateFont("sans-serif", 16, ImGui.FontFlags_Bold)
ImGui.Attach(ctx, FONT_TITLE)
ImGui.Attach(ctx, FONT_NAME)

-- Claude's replies are markdown; the panel shows plain text.
local function plain(text)
  return (text:gsub("%*%*(.-)%*%*", "%1"):gsub("`([^`\n]+)`", "%1"):gsub("\n#+%s*", "\n"):gsub("^#+%s*", ""))
end

local function wrapped(ctx, color, text)
  if color then ImGui.PushStyleColor(ctx, ImGui.Col_Text, color) end
  ImGui.TextWrapped(ctx, text)
  if color then ImGui.PopStyleColor(ctx) end
end

local function centered(ctx, text, color)
  local avail = ImGui.GetContentRegionAvail(ctx)
  local w = ImGui.CalcTextSize(ctx, text)
  ImGui.SetCursorPosX(ctx, ImGui.GetCursorPosX(ctx) + math.max(0, (avail - w) / 2))
  ImGui.TextColored(ctx, color, text)
end

local function draw_welcome(ctx)
  local avail = ImGui.GetContentRegionAvail(ctx)
  local height = math.max(48, math.min(110, avail * 0.3))
  local x, y = ImGui.GetCursorScreenPos(ctx)
  local width = MARK.width * height / MARK.height
  draw_mark(ImGui.GetWindowDrawList(ctx), x + (avail - width) / 2, y + 18, height, glow())
  ImGui.Dummy(ctx, avail, height + 30)
  ImGui.PushFont(ctx, FONT_TITLE)
  centered(ctx, "creaper", 0xECF0F6FF)
  ImGui.PopFont(ctx)
  centered(ctx, "An AI producer that lives inside REAPER", COLOR.muted)
  ImGui.Dummy(ctx, 0, 14)
end

local function draw_messages(ctx)
  if #state.messages == 0 then
    draw_welcome(ctx)
    wrapped(ctx, COLOR.muted, "Ask Claude to do something in this project, for example:")
    for _, example in ipairs({
      "What's in this project?",
      "Make a track with an Arturia synth and write an 8-bar progression in A minor.",
      "Add a drum beat with swung hats on the selected track.",
      "Measure the mix: is it too loud for streaming?",
    }) do
      if ImGui.Selectable(ctx, "  " .. example) then input = example focus_input = true end
    end
    return
  end
  for i, m in ipairs(state.messages) do
    if m.role == "user" then
      if i > 1 then ImGui.Spacing(ctx) end
      wrapped(ctx, COLOR.user, m.text)
    elseif m.role == "assistant" then
      wrapped(ctx, nil, plain(m.text))
    elseif m.role == "tool" then
      wrapped(ctx, m.error and COLOR.error or COLOR.muted, "  > " .. m.text .. (m.error and ("  [" .. m.error .. "]") or ""))
    elseif m.role == "error" then
      wrapped(ctx, COLOR.error, m.text)
    else
      wrapped(ctx, COLOR.info, m.text)
    end
  end
  local confirmation = pending_confirmation()
  if confirmation then
    ImGui.Spacing(ctx)
    wrapped(ctx, COLOR.info, "Claude wants to " .. confirmation.action .. ". Allow it?")
    if ImGui.Button(ctx, "Allow") then answer_confirmation(confirmation, true) end
    ImGui.SameLine(ctx)
    if ImGui.Button(ctx, "Deny") then answer_confirmation(confirmation, false) end
    scroll_to_bottom = true
  elseif turn then
    local dots = string.rep(".", math.floor(reaper.time_precise() * 2) % 4)
    wrapped(ctx, COLOR.muted, "Claude is working" .. dots)
  end
end

local function draw_status(ctx)
  if bridge_running() then
    ImGui.TextColored(ctx, COLOR.ok, "connected")
  else
    ImGui.TextColored(ctx, COLOR.error, "bridge stopped")
    ImGui.SameLine(ctx)
    if ImGui.SmallButton(ctx, "Start bridge") then start_bridge() end
  end
  if state.usage and state.usage.five_hour then
    ImGui.SameLine(ctx)
    ImGui.TextDisabled(ctx, string.format("plan: %d%% of 5h", math.floor(state.usage.five_hour * 100 + 0.5)))
    if ImGui.IsItemHovered(ctx) and state.usage.seven_day then
      ImGui.SetTooltip(ctx, string.format("Claude plan usage: %d%% of the 5-hour limit, %d%% of the weekly limit",
        math.floor(state.usage.five_hour * 100 + 0.5), math.floor(state.usage.seven_day * 100 + 0.5)))
    end
  end
end

-- The mark and name at the top left, lined up with the buttons beside them.
local function draw_header(ctx)
  local x, y = ImGui.GetCursorScreenPos(ctx)
  local h = ImGui.GetFrameHeight(ctx)
  local width = draw_mark(ImGui.GetWindowDrawList(ctx), x, y - 1, h + 2, glow())
  ImGui.Dummy(ctx, width + 2, h)
  ImGui.SameLine(ctx)
  ImGui.AlignTextToFramePadding(ctx)
  ImGui.PushFont(ctx, FONT_NAME)
  ImGui.TextColored(ctx, 0xECF0F6FF, "creaper")
  ImGui.PopFont(ctx)
  ImGui.SameLine(ctx, 0, 14)
end

local function send()
  local prompt = input:gsub("^%s+", ""):gsub("%s+$", "")
  if prompt == "" or turn then return end
  if not bridge_running() then start_bridge() end
  add_message("user", prompt)
  input = ""
  start_turn(prompt)
end

local function frame()
  poll_turn()

  if dock_request then
    ImGui.SetNextWindowDockID(ctx, dock_request)
    dock_request = nil
  end
  ImGui.SetNextWindowSize(ctx, 420, 640, ImGui.Cond_FirstUseEver)
  push_theme(ctx)
  local visible, open = ImGui.Begin(ctx, "creaper", true)
  if visible then
    draw_header(ctx)
    if ImGui.Button(ctx, "New chat") then new_chat() end
    if ImGui.IsItemHovered(ctx) then ImGui.SetTooltip(ctx, "Start a fresh conversation") end
    ImGui.SameLine(ctx)
    local docked = ImGui.IsWindowDocked(ctx)
    if ImGui.Button(ctx, docked and "Undock" or "Dock") then dock_request = docked and 0 or -1 end
    ImGui.SameLine(ctx)
    draw_status(ctx)
    ImGui.Separator(ctx)

    local input_height = ImGui.GetTextLineHeight(ctx) * 4 + 8
    local _, avail_h = ImGui.GetContentRegionAvail(ctx)
    local history_h = avail_h - input_height - ImGui.GetFrameHeightWithSpacing(ctx) - 8
    if ImGui.BeginChild(ctx, "history", 0, math.max(60, history_h)) then
      draw_messages(ctx)
      if scroll_to_bottom then
        ImGui.SetScrollHereY(ctx, 1.0)
        scroll_to_bottom = false
      end
      ImGui.EndChild(ctx)
    end

    if focus_input then
      ImGui.SetKeyboardFocusHere(ctx)
      focus_input = false
    end
    -- Without EnterReturnsTrue, ImGui hands back the text on every keystroke, so
    -- `input` always matches what's on screen. Enter (without Ctrl) ends the edit;
    -- that's when we send.
    local _
    _, input = ImGui.InputTextMultiline(ctx, "##message", input, -1, input_height,
      ImGui.InputTextFlags_CtrlEnterForNewLine)
    local submitted = ImGui.IsItemDeactivated(ctx) and not ImGui.IsKeyDown(ctx, ImGui.Mod_Ctrl)
      and (ImGui.IsKeyPressed(ctx, ImGui.Key_Enter) or ImGui.IsKeyPressed(ctx, ImGui.Key_KeypadEnter))
    if input == "" then -- placeholder; multiline inputs have no built-in hint
      local hx, hy = ImGui.GetItemRectMin(ctx)
      local px, py = ImGui.GetStyleVar(ctx, ImGui.StyleVar_FramePadding)
      ImGui.DrawList_AddText(ImGui.GetWindowDrawList(ctx), hx + px, hy + py, COLOR.muted,
        turn and "Claude is working..." or "Ask creaper to compose, mix or master...")
    end
    if submitted then
      send()
      focus_input = true
    end
    if turn then
      if ImGui.Button(ctx, "Stop") then stop_turn() end
    else
      if ImGui.Button(ctx, "Send") then send() focus_input = true end
    end
    ImGui.SameLine(ctx)
    ImGui.TextDisabled(ctx, "Enter sends, Ctrl+Enter adds a line. Ctrl+Z undoes Claude's changes.")
    ImGui.End(ctx)
  end
  pop_theme(ctx)

  if open then
    reaper.defer(frame)
  end
end

reaper.atexit(save_state)
if not config then
  add_message("error", "creaper isn't set up for chat yet. Run `creaper install-bridge` in a terminal, then reopen this panel.")
elseif not config.claude then
  add_message("error", "Claude Code wasn't found. Install it, sign in once by running `claude` in a terminal, then run `creaper install-bridge` again.")
end
start_bridge()
reaper.defer(frame)

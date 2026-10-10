-- @description creaper chat: talk to Claude from a dockable panel inside REAPER
-- @author nickcapron
-- @version 0.3.0
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
  user = 0x8AB4F8FF,
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

local function write_file(path, text)
  local tmp = path .. ".tmp"
  local f = assert(io.open(tmp, "wb"))
  f:write(text)
  f:close()
  os.remove(path)
  assert(os.rename(tmp, path))
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

local function bridge_running()
  local beat = tonumber(reaper.GetExtState("creaper", "heartbeat"))
  return beat ~= nil and reaper.time_precise() - beat < 3
end

local function start_bridge()
  if bridge_running() or not reaper.file_exists(BRIDGE_SCRIPT) then return end
  local command = reaper.AddRemoveReaScript(true, 0, BRIDGE_SCRIPT, true)
  if command and command > 0 then reaper.Main_OnCommand(command, 0) end
end

------------------------------------------------------------------- turns

local function cleanup_turn(t)
  for _, path in ipairs({ t.request, t.events, t.cancel }) do os.remove(path) end
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
    offset = 0,
    started = os.time(),
    got_event = false,
  }
  write_file(t.request, json.encode({
    prompt = prompt,
    session_id = state.session_id,
    events = t.events,
    cancel = t.cancel,
    resource_path = reaper.GetResourcePath(),
    claude = config.claude,
    model = config.model,
  }))
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

local function new_chat()
  if turn then return end
  state.session_id = nil
  state.messages = {}
  save_state()
end

----------------------------------------------------------------------- UI

-- Claude's replies are markdown; the panel shows plain text.
local function plain(text)
  return (text:gsub("%*%*(.-)%*%*", "%1"):gsub("`([^`\n]+)`", "%1"):gsub("\n#+%s*", "\n"):gsub("^#+%s*", ""))
end

local function wrapped(ctx, color, text)
  if color then ImGui.PushStyleColor(ctx, ImGui.Col_Text, color) end
  ImGui.TextWrapped(ctx, text)
  if color then ImGui.PopStyleColor(ctx) end
end

local function draw_messages(ctx)
  if #state.messages == 0 then
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
  if turn then
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

local ctx = ImGui.CreateContext("creaper", ImGui.ConfigFlags_DockingEnable)

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
  local visible, open = ImGui.Begin(ctx, "creaper", true)
  if visible then
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
    local flags = ImGui.InputTextFlags_EnterReturnsTrue | ImGui.InputTextFlags_CtrlEnterForNewLine
    local submitted
    submitted, input = ImGui.InputTextMultiline(ctx, "##message", input, -1, input_height, flags)
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

-- @description creaper bridge: lets Claude work in REAPER through the creaper MCP server
-- @author nickcapron
-- @version 0.12.0
-- @link https://github.com/nickcapron/creaper
-- @provides
--   [nomain] creaper_json.lua
--   [main] creaper_chat.lua
-- @about
--   Keep this script running while you use creaper. It watches a folder in
--   REAPER's resource path for requests from the creaper MCP server, runs them
--   with the ReaScript API and writes the answers back.
--
--   Every change it makes is a named undo point ("creaper: ..."), so Ctrl+Z
--   reverts anything Claude did.

local BRIDGE_VERSION = "0.12.0"
local PROTOCOL = 2

----------------------------------------------------------------------- JSON

-- Shared with creaper_chat.lua; lives next to this script.
local SCRIPT_DIR = debug.getinfo(1, "S").source:match("^@(.*[\\/])") or ""
local json = dofile(SCRIPT_DIR .. "creaper_json.lua")

---------------------------------------------------------------------- paths

local SEP = package.config:sub(1, 1)
local function join(...) return table.concat({ ... }, SEP) end

local BRIDGE_DIR = join(reaper.GetResourcePath(), "creaper")
local REQUESTS_DIR = join(BRIDGE_DIR, "requests")   -- protocol 2: <id>.json per request
local RESPONSES_DIR = join(BRIDGE_DIR, "responses") -- protocol 2: <id>.json per answer
local REQUEST_PATH = join(BRIDGE_DIR, "request.json")   -- protocol 1 (older servers)
local RESPONSE_PATH = join(BRIDGE_DIR, "response.json") -- protocol 1
local HEARTBEAT_PATH = join(BRIDGE_DIR, "bridge.json")
local RENDER_DIR = join(BRIDGE_DIR, "renders")

-------------------------------------------------------------------- helpers

-- Errors raised with fail() are shown to the user as-is; anything else is a
-- bug and gets a traceback.
local function fail(msg) error({ message = msg }, 0) end

local function int(x) return math.tointeger(math.floor(x + 0.5)) end
local function round(x, places)
  local m = 10 ^ (places or 3)
  return math.floor(x * m + 0.5) / m
end
local function amp_to_db(a)
  if a < 1e-8 then return -150.0 end
  return round(20 * math.log(a, 10), 2)
end
local function db_to_amp(db) return 10 ^ (db / 20) end

local function with_undo(description, fn)
  reaper.Undo_BeginBlock2(0)
  reaper.PreventUIRefresh(1)
  local ok, result = pcall(fn)
  reaper.PreventUIRefresh(-1)
  reaper.Undo_EndBlock2(0, "creaper: " .. description, -1)
  reaper.TrackList_AdjustWindows(false)
  reaper.UpdateArrange()
  if not ok then error(result, 0) end
  return result
end

------------------------------------------------------------- musical time

local function qn_to_time(qn) return reaper.TimeMap2_QNToTime(0, qn) end
local function time_to_qn(t) return reaper.TimeMap2_timeToQN(0, t) end

local function time_to_pos(t)
  local beat, measures = reaper.TimeMap2_timeToBeats(0, t)
  return {
    seconds = round(t, 3),
    bar = math.tointeger(measures) + 1,
    beat = round(beat + 1, 3),
    qn = round(time_to_qn(t), 3),
  }
end

-- Bars and beats are 1-based like REAPER's ruler. A fractional bar is a
-- fraction of that bar; beats are in time-signature beats (eighths in 6/8).
local function bar_to_qn(bar, beat)
  if bar < 1 then fail("bars start at 1") end
  local whole = math.floor(bar)
  local _, qn_start, qn_end, _, denom = reaper.TimeMap_GetMeasureInfo(0, math.tointeger(whole) - 1)
  local qn = qn_start + (bar - whole) * (qn_end - qn_start)
  if beat then qn = qn + (beat - 1) * 4 / denom end
  return qn
end

-- Reads <prefix>_bar (+ <prefix>_beat), <prefix>_qn or <prefix>_seconds.
local function resolve_qn(p, prefix, default)
  local bar = p[prefix .. "_bar"]
  if bar then return bar_to_qn(bar, p[prefix .. "_beat"]) end
  if p[prefix .. "_qn"] then return p[prefix .. "_qn"] end
  local s = p[prefix .. "_seconds"]
  if s then return time_to_qn(s) end
  return default
end

local function bar_length_qn_at(qn)
  local _, qn_start, qn_end = reaper.TimeMap_QNToMeasures(0, qn)
  return qn_end - qn_start
end

----------------------------------------------------------------- tracks

local function track_name(t)
  if t == reaper.GetMasterTrack(0) then return "MASTER" end
  local _, name = reaper.GetSetMediaTrackInfo_String(t, "P_NAME", "", false)
  return name
end

local function track_number(t)
  local n = reaper.GetMediaTrackInfo_Value(t, "IP_TRACKNUMBER")
  if n == -1 then return "master" end
  return math.tointeger(n)
end

local function track_ref(t)
  if not t then return nil end
  return { number = track_number(t), name = track_name(t) }
end

-- Tracks by number, "master", or name. Names match exactly first, then as a
-- substring, unless `exact` is set (for destructive commands).
local function get_track(ref, exact)
  if ref == nil then fail("a track is required") end
  local n = tonumber(ref)
  if n then
    local t = reaper.GetTrack(0, int(n) - 1)
    if not t then
      fail(string.format("there is no track %d (the project has %d tracks)", int(n), reaper.CountTracks(0)))
    end
    return t
  end
  local wanted = tostring(ref):lower()
  if wanted == "master" then return reaper.GetMasterTrack(0) end
  local partial
  for i = 0, reaper.CountTracks(0) - 1 do
    local t = reaper.GetTrack(0, i)
    local _, name = reaper.GetTrackName(t)
    name = name:lower()
    if name == wanted then return t end
    if not partial and name:find(wanted, 1, true) then partial = t end
  end
  if partial and exact then
    local _, name = reaper.GetTrackName(partial)
    fail("there is no track named exactly '" .. tostring(ref) .. "' (did you mean '" .. name
      .. "'? Use its exact name or number)")
  end
  if partial then return partial end
  fail("there is no track named '" .. tostring(ref) .. "'")
end

local function color_hex(native)
  if native == 0 then return nil end
  local r, g, b = reaper.ColorFromNative(native & 0xFFFFFF)
  return string.format("#%02X%02X%02X", r, g, b)
end

local function set_color(t, hex)
  local r, g, b = tostring(hex):match("^#?(%x%x)(%x%x)(%x%x)$")
  if not r then fail("colors look like #RRGGBB") end
  reaper.SetTrackColor(t, reaper.ColorToNative(tonumber(r, 16), tonumber(g, 16), tonumber(b, 16)))
end

local function fx_name(t, i)
  local _, name = reaper.TrackFX_GetFXName(t, i, "")
  return name
end

local function track_summary(t)
  local master = t == reaper.GetMasterTrack(0)
  local fx = {}
  for i = 0, reaper.TrackFX_GetCount(t) - 1 do
    local name = fx_name(t, i)
    if not reaper.TrackFX_GetEnabled(t, i) then name = name .. " (bypassed)" end
    fx[#fx + 1] = name
  end
  local summary = {
    number = track_number(t),
    name = track_name(t),
    volume_db = amp_to_db(reaper.GetMediaTrackInfo_Value(t, "D_VOL")),
    pan = round(reaper.GetMediaTrackInfo_Value(t, "D_PAN"), 3),
    mute = reaper.GetMediaTrackInfo_Value(t, "B_MUTE") == 1,
    fx = fx,
  }
  if not master then
    summary.solo = reaper.GetMediaTrackInfo_Value(t, "I_SOLO") > 0
    summary.armed = reaper.GetMediaTrackInfo_Value(t, "I_RECARM") == 1
    summary.selected = reaper.IsTrackSelected(t)
    summary.item_count = reaper.CountTrackMediaItems(t)
    summary.color = color_hex(reaper.GetTrackColor(t))
    if reaper.GetMediaTrackInfo_Value(t, "I_FOLDERDEPTH") == 1 then summary.is_folder = true end
    local parent = reaper.GetParentTrack(t)
    if parent then summary.parent = track_number(parent) end
  end
  return summary
end

local SEND_MODES = { [0] = "post-fader", [1] = "pre-fx", [2] = "post-fx", [3] = "post-fx" }
local SEND_MODE_IDS = { ["post-fader"] = 0, ["pre-fx"] = 1, ["post-fx"] = 3 }

local function send_info(t, category, i)
  local other = reaper.GetTrackSendInfo_Value(t, category, i, category == 0 and "P_DESTTRACK" or "P_SRCTRACK")
  return {
    [category == 0 and "destination" or "source"] = track_ref(other),
    volume_db = amp_to_db(reaper.GetTrackSendInfo_Value(t, category, i, "D_VOL")),
    pan = round(reaper.GetTrackSendInfo_Value(t, category, i, "D_PAN"), 3),
    mute = reaper.GetTrackSendInfo_Value(t, category, i, "B_MUTE") == 1,
    mode = SEND_MODES[int(reaper.GetTrackSendInfo_Value(t, category, i, "I_SENDMODE"))] or "other",
  }
end

------------------------------------------------------------------ items

local function item_guid(item)
  local _, guid = reaper.GetSetMediaItemInfo_String(item, "GUID", "", false)
  return guid
end

local function find_item(id)
  if not id then fail("an item_id is required") end
  if id == "selected" then
    return reaper.GetSelectedMediaItem(0, 0) or fail("no item is selected")
  end
  for i = 0, reaper.CountMediaItems(0) - 1 do
    local item = reaper.GetMediaItem(0, i)
    if item_guid(item) == id then return item end
  end
  fail("no item has id " .. tostring(id) .. " (ids come from get_track_details or create_midi_item)")
end

local function midi_take(item)
  local take = reaper.GetActiveTake(item)
  if not take or not reaper.TakeIsMIDI(take) then fail("that item isn't a MIDI item") end
  return take
end

local function item_bounds_qn(item)
  local pos = reaper.GetMediaItemInfo_Value(item, "D_POSITION")
  local len = reaper.GetMediaItemInfo_Value(item, "D_LENGTH")
  return time_to_qn(pos), time_to_qn(pos + len)
end

local function item_info(item)
  local pos = reaper.GetMediaItemInfo_Value(item, "D_POSITION")
  local len = reaper.GetMediaItemInfo_Value(item, "D_LENGTH")
  local start_qn, end_qn = item_bounds_qn(item)
  local info = {
    id = item_guid(item),
    track = track_number(reaper.GetMediaItem_Track(item)),
    start = time_to_pos(pos),
    ["end"] = time_to_pos(pos + len),
    length_qn = round(end_qn - start_qn, 3),
    length_seconds = round(len, 3),
    muted = reaper.GetMediaItemInfo_Value(item, "B_MUTE") == 1,
    selected = reaper.IsMediaItemSelected(item),
  }
  local take = reaper.GetActiveTake(item)
  if not take then
    info.type = "empty"
  else
    local _, name = reaper.GetSetMediaItemTakeInfo_String(take, "P_NAME", "", false)
    info.name = name
    if reaper.TakeIsMIDI(take) then
      info.type = "midi"
      local _, notes = reaper.MIDI_CountEvts(take)
      info.note_count = notes
    else
      info.type = "audio"
      local source = reaper.GetMediaItemTake_Source(take)
      if source then info.file = reaper.GetMediaSourceFileName(source, "") end
    end
  end
  return info
end

-------------------------------------------------------------------- FX

local function get_fx(t, ref)
  local count = reaper.TrackFX_GetCount(t)
  if count == 0 then fail("track '" .. track_name(t) .. "' has no FX") end
  local n = tonumber(ref)
  if n then
    local i = int(n) - 1
    if i < 0 or i >= count then
      fail(string.format("FX %d doesn't exist (the track has %d FX)", int(n), count))
    end
    return i
  end
  local wanted = tostring(ref):lower()
  for i = 0, count - 1 do
    if fx_name(t, i):lower() == wanted then return i end
  end
  for i = 0, count - 1 do
    if fx_name(t, i):lower():find(wanted, 1, true) then return i end
  end
  fail("no FX matching '" .. tostring(ref) .. "' on track '" .. track_name(t) .. "'")
end

-- Many VST3 plugins expose thousands of placeholder parameters for MIDI CC
-- mapping ("MIDI CC helper 85 [1]", "MIDI CC 0|60"). They aren't real
-- controls, so they're hidden from listings and name searches.
-- Plugins (Arturia's among them) also expose host/controller plumbing as
-- parameters: preset browsing, hardware controller hooks, undo/redo, MPE and
-- program-change placeholders. Setting one could save over a preset or undo
-- the user's work inside the plugin, so they're hidden too.
local PLUMBING = {
  "^vst_programchange_", "^mpe_", "^hardwaredisplaycontrol", "^hardwarebackcontrol", "^hw controller",
  "^select preset", "^navigate through", "^add/remove selected filter", "^select multi filter",
  "^clear filters", "^active filter", "^browse back", "^sendvaluestomidicontroller", "^previous preset$",
  "^next preset$", "^select keylab", "^oct minus$", "^oct plus$", "^saves the current preset",
  "^undo the last action", "^redo the last action",
}

local function is_midi_cc_helper(name)
  if name:find("^MIDI CC helper") or name:find("^MIDI CC %d+|%d+$") then return true end
  local lower = name:lower()
  for _, pattern in ipairs(PLUMBING) do
    if lower:find(pattern) then return true end
  end
  return false
end

local function find_param(t, fx, ref)
  local count = reaper.TrackFX_GetNumParams(t, fx)
  local n = tonumber(ref)
  if n then
    local i = int(n) - 1
    if i < 0 or i >= count then fail(string.format("parameter %d doesn't exist (%d parameters)", int(n), count)) end
    return i
  end
  local wanted = tostring(ref):lower()
  local partial
  for i = 0, count - 1 do
    local _, name = reaper.TrackFX_GetParamName(t, fx, i, "")
    if not is_midi_cc_helper(name) then
      name = name:lower()
      if name == wanted then return i end
      if not partial and name:find(wanted, 1, true) then partial = i end
    end
  end
  if partial then return partial end
  fail("no parameter matching '" .. tostring(ref) .. "' (get_fx_parameters lists them)")
end

local function real_param_count(t, fx)
  local n = 0
  for i = 0, reaper.TrackFX_GetNumParams(t, fx) - 1 do
    local _, name = reaper.TrackFX_GetParamName(t, fx, i, "")
    if not is_midi_cc_helper(name) then n = n + 1 end
  end
  return n
end

-- "-18.0 dB" -> -18, "1.2 kHz" -> 1200, "-inf" -> -inf
local function parse_display_number(s)
  if not s or s == "" then return nil end
  local lower = s:lower()
  if lower:find("-inf", 1, true) then return -math.huge end
  if lower:find("inf", 1, true) then return math.huge end
  local num, suffix = lower:match("([-+]?%d*%.?%d+)%s*(%a?)")
  num = tonumber(num)
  if num and suffix == "k" then num = num * 1000 end
  return num
end

-- What the plugin would display for normalized value v. Uses
-- FormatParamValueNormalized when the plugin supports it, otherwise sets the
-- parameter and reads it back (callers restore it on failure).
local function display_string_at(t, fx, param, v)
  local ok, s = reaper.TrackFX_FormatParamValueNormalized(t, fx, param, v, "")
  if not ok or s == "" then
    reaper.TrackFX_SetParamNormalized(t, fx, param, v)
    _, s = reaper.TrackFX_GetFormattedParamValue(t, fx, param, "")
  end
  return s
end

-- Number of positions for stepped parameters (switches, menus), else nil.
local function param_positions(t, fx, param)
  local ok, step, _, _, toggle = reaper.TrackFX_GetParameterStepSizes(t, fx, param)
  if not ok then return nil end
  if toggle then return 2 end
  if step and step > 0 and step <= 0.5 then return math.tointeger(math.floor(1 / step + 0.5)) + 1 end
  return nil
end

local function trim_lower(s) return (s:lower():gsub("^%s+", ""):gsub("%s+$", "")) end

-- Finds the value whose display text is `text` ("Saw", "Low Pass", "On").
local function solve_display_text(t, fx, param, text)
  local wanted = trim_lower(text)
  local n = param_positions(t, fx, param) or 129
  local options, seen, prefix_match, contains_match = {}, {}, nil, nil
  for k = 0, n - 1 do
    local v = k / (n - 1)
    local s = display_string_at(t, fx, param, v)
    if s and s ~= "" then
      local ls = trim_lower(s)
      if ls == wanted then return v end
      if not prefix_match and ls:sub(1, #wanted) == wanted then prefix_match = v end
      if not contains_match and ls:find(wanted, 1, true) then contains_match = v end
      if not seen[s] then
        seen[s] = true
        options[#options + 1] = s
      end
    end
  end
  if prefix_match or contains_match then return prefix_match or contains_match end
  fail("no setting shows '" .. text .. "'. It shows: " .. table.concat(options, ", ", 1, math.min(#options, 40)))
end

-- Finds the normalized value whose displayed value is `target`, assuming the
-- display is monotonic.
local function solve_display_value(t, fx, param, target)
  local function display_at(v) return parse_display_number(display_string_at(t, fx, param, v)) end
  local at_min, at_max = display_at(0), display_at(1)
  if not at_min or not at_max then
    fail("this parameter doesn't show a number; use display_text (e.g. 'Saw') or value (0 to 1)")
  end
  local rising = at_max >= at_min
  if (rising and target <= at_min) or (not rising and target >= at_min) then return 0.0, true end
  if (rising and target >= at_max) or (not rising and target <= at_max) then return 1.0, true end
  local lo, hi = 0.0, 1.0
  for _ = 1, 40 do
    local mid = (lo + hi) / 2
    local d = display_at(mid)
    if d == nil then break end
    if (d < target) == rising then lo = mid else hi = mid end
  end
  -- The display is rounded, so lo and hi straddle the target; keep whichever reads closer.
  local d_lo, d_hi = display_at(lo), display_at(hi)
  if d_lo and d_hi and math.abs(d_lo - target) < math.abs(d_hi - target) then return lo, false end
  return hi, false
end

local function param_info(t, fx, i, with_options)
  local _, name = reaper.TrackFX_GetParamName(t, fx, i, "")
  local _, display = reaper.TrackFX_GetFormattedParamValue(t, fx, i, "")
  local info = {
    index = i + 1,
    name = name,
    value = round(reaper.TrackFX_GetParamNormalized(t, fx, i), 4),
    display = display,
  }
  local positions = param_positions(t, fx, i)
  if positions then
    info.positions = positions
    -- List a menu's choices when the plugin can name them without being changed.
    if with_options and positions <= 24 then
      local options = {}
      for k = 0, positions - 1 do
        local ok, s = reaper.TrackFX_FormatParamValueNormalized(t, fx, i, k / (positions - 1), "")
        if not ok or s == "" then options = nil break end
        options[#options + 1] = s
      end
      info.options = options
    end
  end
  return info
end

-- One parameter change: {parameter, value | display_value | display_text}.
-- Restores the parameter if anything goes wrong.
local function apply_param_change(t, fx, change)
  local param = find_param(t, fx, change.parameter)
  local _, param_name = reaper.TrackFX_GetParamName(t, fx, param, "")
  if is_midi_cc_helper(param_name) then
    fail("'" .. param_name .. "' isn't a sound control (it's preset/controller plumbing), so creaper won't set it")
  end
  local original = reaper.TrackFX_GetParamNormalized(t, fx, param)
  local ok, result = pcall(function()
    local value, clamped = change.value, false
    if value == nil and change.display_text ~= nil then
      value = solve_display_text(t, fx, param, tostring(change.display_text))
    elseif value == nil and change.display_value ~= nil then
      value, clamped = solve_display_value(t, fx, param, change.display_value)
    elseif value == nil then
      fail("give value (0 to 1), display_value or display_text")
    end
    reaper.TrackFX_SetParamNormalized(t, fx, param, math.max(0, math.min(1, value)))
    local info = param_info(t, fx, param)
    if clamped then info.note = "the requested value is outside this parameter's range, so it was set to the limit" end
    return info
  end)
  if not ok then
    reaper.TrackFX_SetParamNormalized(t, fx, param, original)
    error(result, 0)
  end
  return result
end

---------------------------------------------------------- plugin catalog

local FORMAT_RANK = { CLAP = 1, VST3 = 2, VST = 3, AU = 4, LV2 = 5, DX = 6, JS = 7 }

local function named_config(t, fx, key)
  local ok, v = reaper.TrackFX_GetNamedConfigParm(t, fx, key)
  if ok and v ~= "" then return v end
  return nil
end

local function fxtags_key(s) return (s:lower():gsub("[^%w%.]", "_")) end

-- Developer and category tags REAPER keeps in reaper-fxtags.ini, keyed by plugin file.
local function read_fxtags()
  local tags = { developer = {}, category = {} }
  local f = io.open(join(reaper.GetResourcePath(), "reaper-fxtags.ini"), "r")
  if not f then return tags end
  local section
  for line in f:lines() do
    local name = line:match("^%[(.-)%]")
    if name then
      section = tags[name:lower()]
    elseif section then
      local k, v = line:match("^(.-)=(.*)$")
      if k and v ~= "" then section[fxtags_key(k)] = v end
    end
  end
  f:close()
  return tags
end

-- "VST3i: SILA (SILA) (18 out)" -> { format = "VST3", instrument = true,
--   name = "SILA", developer = "SILA", channels = "18 out" }
local function parse_fx_name(full_name)
  local prefix, rest = full_name:match("^(%w+):%s*(.+)$")
  if not prefix then return nil end
  local instrument = prefix:sub(-1) == "i"
  local entry = { full_name = full_name, format = instrument and prefix:sub(1, -2) or prefix, instrument = instrument }
  local base = rest
  while true do
    local head, group = base:match("^(.-)%s*%(([^()]*)%)$")
    if not head or head == "" then break end
    if not entry.channels and not entry.developer
        and (group:match("^%d+%s*out$") or group:match("^%d+%->%d+%s*ch$") or group:match("^%d+%s*ch$")) then
      entry.channels, base = group, head
    else
      entry.developer, base = group, head
      break
    end
  end
  entry.name = base
  return entry
end

-- REAPER's category tags mix real categories with flags, e.g.
-- "Synth|External|OnlyRT|NoOfflineProcess".
local CATEGORY_FLAGS = { external = "hardware", onlyrt = "realtime_only", noofflineprocess = "realtime_only" }

local function split_category(raw)
  if not raw then return nil, {} end
  local categories, flags = {}, {}
  for part in raw:gmatch("[^|]+") do
    local flag = CATEGORY_FLAGS[part:lower()]
    if flag then flags[flag] = true else categories[#categories + 1] = part end
  end
  return #categories > 0 and table.concat(categories, ", ") or nil, flags
end

local function ident_key(ident)
  local file = (ident or ""):gsub("<.*$", ""):gsub("{.*$", "")
  return fxtags_key(file:match("[^\\/]+$") or file), fxtags_key(file)
end

local function plugin_catalog()
  local tags = read_fxtags()
  local catalog, i = {}, 0
  while true do
    local ok, full_name, ident = reaper.EnumInstalledFX(i)
    if not ok then break end
    local entry = parse_fx_name(full_name)
    if entry and entry.format ~= "ReWire" then
      local key, full_key = ident_key(ident)
      entry.developer = tags.developer[key] or entry.developer
      local flags
      entry.category, flags = split_category(tags.category[key] or tags.category[full_key])
      entry.hardware = flags.hardware
      entry.realtime_only = flags.realtime_only
      catalog[#catalog + 1] = entry
    end
    i = i + 1
  end
  return catalog
end

-- FX on these tracks that REAPER says can't be rendered faster than real time
-- (hardware bridges such as Elektron Overbridge). Offline renders miss their audio.
local function realtime_only_fx(tracks)
  local tags = read_fxtags()
  local found, seen = {}, {}
  for _, t in ipairs(tracks) do
    for i = 0, reaper.TrackFX_GetCount(t) - 1 do
      local key, full_key = ident_key(named_config(t, i, "fx_ident"))
      local _, flags = split_category(tags.category[key] or tags.category[full_key])
      local name = fx_name(t, i)
      if flags.realtime_only and reaper.TrackFX_GetEnabled(t, i) and not seen[name] then
        seen[name] = true
        found[#found + 1] = name
      end
    end
  end
  return found
end

local function better_format(a, b)
  return (FORMAT_RANK[a.format] or 9) < (FORMAT_RANK[b.format] or 9)
end

-- Groups the same plugin in several formats; the preferred format represents it.
local function group_catalog(catalog)
  local groups, order = {}, {}
  for _, e in ipairs(catalog) do
    local key = e.name:lower() .. (e.instrument and "|i" or "|")
    local g = groups[key]
    if not g then
      g = { best = e, formats = {} }
      groups[key] = g
      order[#order + 1] = key
    elseif better_format(e, g.best) then
      g.best = e
    end
    g.formats[#g.formats + 1] = e.format
  end
  local list = {}
  for _, key in ipairs(order) do list[#list + 1] = groups[key] end
  return list
end

local function words_of(s)
  local words = {}
  for w in tostring(s or ""):lower():gmatch("%S+") do words[#words + 1] = w end
  return words
end

local function has_all_words(haystack, words)
  for _, w in ipairs(words) do
    if not haystack:find(w, 1, true) then return false end
  end
  return true
end

-- Turns what the user called a plugin into REAPER's exact name, preferring
-- instruments when one is wanted and CLAP/VST3 over VST2 duplicates. Returns
-- nil when nothing in the catalog matches (FX chains, renamed plugins, ...).
local function resolve_plugin(query, want_instrument)
  local q = trim_lower(query)
  local catalog = plugin_catalog()
  for _, e in ipairs(catalog) do
    if e.full_name:lower() == q then return e.full_name end
  end
  local groups = group_catalog(catalog)
  local function choose(candidates)
    if #candidates == 1 then return candidates[1].best.full_name end
    if want_instrument ~= nil then
      local filtered = {}
      for _, g in ipairs(candidates) do
        if g.best.instrument == want_instrument then filtered[#filtered + 1] = g end
      end
      if #filtered == 1 then return filtered[1].best.full_name end
      if #filtered > 1 then candidates = filtered end
    end
    local names = {}
    for k = 1, math.min(#candidates, 12) do names[k] = candidates[k].best.name end
    fail("'" .. query .. "' matches several plugins: " .. table.concat(names, ", ")
      .. (#candidates > 12 and ", ..." or "") .. ". Use a more specific name.")
  end
  local exact = {}
  for _, g in ipairs(groups) do
    if g.best.name:lower() == q then exact[#exact + 1] = g end
  end
  if #exact > 0 then return choose(exact) end
  local words, partial = words_of(q), {}
  for _, g in ipairs(groups) do
    if has_all_words((g.best.name .. " " .. (g.best.developer or "")):lower(), words) then partial[#partial + 1] = g end
  end
  if #partial > 0 then return choose(partial) end
  return nil
end

local function fx_details(t, i)
  local _, preset = reaper.TrackFX_GetPreset(t, i, "")
  local fx_type = named_config(t, i, "fx_type")
  local _, _, outputs = reaper.TrackFX_GetIOSize(t, i)
  return {
    index = i + 1,
    name = fx_name(t, i),
    format = fx_type and fx_type:gsub("i$", "") or nil,
    instrument = fx_type and fx_type:sub(-1) == "i" or nil,
    outputs = outputs and outputs > 2 and outputs or nil,
    enabled = reaper.TrackFX_GetEnabled(t, i),
    offline = reaper.TrackFX_GetOffline(t, i) or nil,
    preset = preset ~= "" and preset or nil,
    parameter_count = real_param_count(t, i),
  }
end

---------------------------------------------------------------- commands

local commands = {}
local stop_at -- playback stops when it passes this time (seconds)
local beat_now -- set to write the heartbeat on the next tick instead of within a second

-- REAPER's "prompt to save/delete/rename new files" when recording stops (on by
-- default). Its window blocks scripts, so the bridge can't answer until the user does.
local function stop_prompt_on()
  local ok, value = reaper.get_config_var_string("promptendrec")
  return ok and (tonumber(value) or 0) & 1 ~= 0
end

function commands.ping()
  return {
    bridge_version = BRIDGE_VERSION,
    protocol = PROTOCOL,
    reaper_version = reaper.GetAppVersion(),
    resource_path = reaper.GetResourcePath(),
  }
end

local function project_sample_rate()
  if reaper.GetSetProjectInfo(0, "PROJECT_SRATE_USE", 0, false) == 1 then
    return int(reaper.GetSetProjectInfo(0, "PROJECT_SRATE", 0, false))
  end
  local _, device_rate = reaper.GetAudioDeviceInfo("SRATE", "")
  return int(tonumber(device_rate) or 44100)
end

function commands.get_project_overview()
  local _, path = reaper.EnumProjects(-1, "")
  local num, denom, bpm = reaper.TimeMap_GetTimeSigAtTime(0, 0)
  local sel_start, sel_end = reaper.GetSet_LoopTimeRange(false, false, 0, 0, false)
  local play_state = reaper.GetPlayState()

  local tracks = {}
  for i = 0, reaper.CountTracks(0) - 1 do tracks[#tracks + 1] = track_summary(reaper.GetTrack(0, i)) end

  local markers, regions = {}, {}
  local _, num_markers, num_regions = reaper.CountProjectMarkers(0)
  for i = 0, num_markers + num_regions - 1 do
    local _, is_region, pos, region_end, name, number = reaper.EnumProjectMarkers3(0, i)
    if is_region then
      regions[#regions + 1] = { number = number, name = name, start = time_to_pos(pos), ["end"] = time_to_pos(region_end) }
    else
      markers[#markers + 1] = { number = number, name = name, position = time_to_pos(pos) }
    end
  end

  local tempo_changes = {}
  for i = 0, reaper.CountTempoTimeSigMarkers(0) - 1 do
    local _, timepos, _, _, marker_bpm, ts_num, ts_denom, linear = reaper.GetTempoTimeSigMarker(0, i)
    tempo_changes[#tempo_changes + 1] = {
      position = time_to_pos(timepos), bpm = round(marker_bpm, 3),
      time_signature = ts_num > 0 and (ts_num .. "/" .. ts_denom) or nil,
      gradual = linear or nil,
    }
  end

  local selected_items = {}
  for i = 0, math.min(reaper.CountSelectedMediaItems(0), 20) - 1 do
    selected_items[#selected_items + 1] = item_info(reaper.GetSelectedMediaItem(0, i))
  end

  local length = reaper.GetProjectLength(0)
  return {
    project = reaper.GetProjectName(0, ""),
    path = path ~= "" and path or "(unsaved)",
    tempo_bpm = round(bpm, 3),
    time_signature = num .. "/" .. denom,
    tempo_changes = #tempo_changes > 1 and tempo_changes or nil,
    sample_rate = project_sample_rate(),
    length = time_to_pos(length),
    edit_cursor = time_to_pos(reaper.GetCursorPosition()),
    time_selection = sel_end > sel_start and { start = time_to_pos(sel_start), ["end"] = time_to_pos(sel_end) } or nil,
    transport = (play_state & 4 ~= 0) and "recording" or (play_state & 2 ~= 0) and "paused"
      or (play_state & 1 ~= 0) and "playing" or "stopped",
    master = track_summary(reaper.GetMasterTrack(0)),
    tracks = tracks,
    markers = markers,
    regions = regions,
    selected_items = selected_items,
  }
end

function commands.get_track_details(p)
  local t = get_track(p.track)
  local info = track_summary(t)
  local fx = {}
  for i = 0, reaper.TrackFX_GetCount(t) - 1 do fx[#fx + 1] = fx_details(t, i) end
  info.fx = fx
  local instrument = reaper.TrackFX_GetInstrument(t)
  if instrument >= 0 then info.instrument_fx = instrument + 1 end
  local sends, receives = {}, {}
  for i = 0, reaper.GetTrackNumSends(t, 0) - 1 do sends[#sends + 1] = send_info(t, 0, i) end
  for i = 0, reaper.GetTrackNumSends(t, -1) - 1 do receives[#receives + 1] = send_info(t, -1, i) end
  info.sends, info.receives = sends, receives
  if t ~= reaper.GetMasterTrack(0) then
    info.sends_to_master = reaper.GetMediaTrackInfo_Value(t, "B_MAINSEND") == 1
    local items = {}
    local count = reaper.CountTrackMediaItems(t)
    for i = 0, math.min(count, 200) - 1 do items[#items + 1] = item_info(reaper.GetTrackMediaItem(t, i)) end
    info.items = items
    if count > 200 then info.items_truncated = count end
  end
  return info
end

function commands.get_fx_parameters(p)
  local t = get_track(p.track)
  local fx = get_fx(t, p.fx)
  local count = reaper.TrackFX_GetNumParams(t, fx)
  local words = words_of(p.search)
  local offset, limit = p.offset or 0, p.limit or 100
  local params, matched, hidden = {}, 0, 0
  for i = 0, count - 1 do
    local _, name = reaper.TrackFX_GetParamName(t, fx, i, "")
    if is_midi_cc_helper(name) and not p.include_midi_cc then
      hidden = hidden + 1
    elseif has_all_words(name:lower(), words) then
      matched = matched + 1
      if matched > offset and #params < limit then params[#params + 1] = param_info(t, fx, i, true) end
    end
  end
  return {
    fx = fx_name(t, fx), fx_index = fx + 1, parameter_count = count - hidden, matched = matched,
    hidden_placeholders = hidden > 0 and hidden or nil, parameters = params,
  }
end

function commands.list_installed_fx(p)
  local words = words_of(p.search)
  local category = p.category and trim_lower(p.category)
  local developer = p.developer and trim_lower(p.developer)
  local limit = p.limit or 50
  local plugins, total, categories = {}, 0, {}
  for _, g in ipairs(group_catalog(plugin_catalog())) do
    local e = g.best
    local haystack = (e.name .. " " .. (e.developer or "") .. " " .. (e.category or "")):lower()
    local hit = has_all_words(haystack, words)
      and (p.kind == nil or (p.kind == "instrument") == e.instrument)
      and (not category or (e.category or ""):lower():find(category, 1, true))
      and (not developer or (e.developer or ""):lower():find(developer, 1, true))
      and (not p.format or #g.formats == 0 or table.concat(g.formats, " "):lower():find(trim_lower(p.format), 1, true))
    if hit then
      total = total + 1
      for cat in (e.category or "Uncategorized"):gmatch("[^,]+") do
        cat = cat:gsub("^%s+", "")
        categories[cat] = (categories[cat] or 0) + 1
      end
      if #plugins < limit then
        plugins[#plugins + 1] = {
          name = e.name,
          load_as = e.full_name,
          kind = e.instrument and "instrument" or "effect",
          format = e.format,
          formats = #g.formats > 1 and g.formats or nil,
          developer = e.developer,
          category = e.category,
          channels = e.channels,
          hardware = e.hardware,
          realtime_only = e.realtime_only,
        }
      end
    end
  end
  return { plugins = plugins, total_matches = total, categories = json.object(categories) }
end

function commands.list_fx_presets(p)
  local t = get_track(p.track)
  local fx = get_fx(t, p.fx)
  local current_index, count = reaper.TrackFX_GetPresetIndex(t, fx)
  local _, current = reaper.TrackFX_GetPreset(t, fx, "")
  local result = { fx = fx_name(t, fx), current = current ~= "" and current or nil, presets = {} }
  local browser_note = "this plugin keeps its presets in its own browser, not in REAPER's list; "
    .. "open its window with update_fx(show=true) to browse them"
  if count == 0 then
    result.note = browser_note
    return result
  end

  -- Stepping through presets changes the plugin, so save its state and put it back.
  local chunk_ok, fx_chunk = reaper.TrackFX_GetNamedConfigParm(t, fx, "vst_chunk")
  local track_chunk
  if not chunk_ok then _, track_chunk = reaper.GetTrackStateChunk(t, "", false) end

  local words, limit = words_of(p.search), p.limit or 200
  local matched, examined, numbered = 0, 0, 0
  reaper.PreventUIRefresh(1)
  local ok, err = pcall(function()
    for k = 0, math.min(count, 5000) - 1 do
      reaper.TrackFX_SetPresetByIndex(t, fx, k)
      local _, name = reaper.TrackFX_GetPreset(t, fx, "")
      examined = examined + 1
      if name:match("^Program %d+$") then numbered = numbered + 1 end
      if examined == 16 and numbered == 16 then break end -- placeholder slots, not real presets
      if has_all_words(name:lower(), words) then
        matched = matched + 1
        if #result.presets < limit then result.presets[#result.presets + 1] = { index = k + 1, name = name } end
      end
    end
  end)
  if chunk_ok then
    reaper.TrackFX_SetNamedConfigParm(t, fx, "vst_chunk", fx_chunk)
  elseif track_chunk then
    reaper.SetTrackStateChunk(t, track_chunk, false)
  end
  reaper.PreventUIRefresh(-1)
  if not ok then error(err, 0) end

  if numbered == examined then
    result.presets = {}
    result.note = "only numbered program slots (Program 1, 2, ...) are visible to REAPER; " .. browser_note
    return result
  end
  result.total_matches = matched
  return result
end

-- The plugin file behind an FX, without REAPER's id suffixes, for matching
-- the same plugin across tracks and sessions.
local function fx_file(t, fx)
  local ident = named_config(t, fx, "fx_ident") or ""
  local file = ident:gsub("<.*$", ""):gsub("{.*$", "")
  return (file:match("[^\\/]+$") or file):lower()
end

-- Everything needed to recreate an FX's current sound: its full state when
-- the plugin shares one (most VST/VST3), and its parameter values as a fallback.
function commands.capture_fx_state(p)
  local t = get_track(p.track)
  local fx
  if p.fx then
    fx = get_fx(t, p.fx)
  else
    local instrument = reaper.TrackFX_GetInstrument(t)
    fx = instrument >= 0 and instrument or get_fx(t, 1)
  end
  local params = {}
  for i = 0, reaper.TrackFX_GetNumParams(t, fx) - 1 do
    local _, name = reaper.TrackFX_GetParamName(t, fx, i, "")
    if not is_midi_cc_helper(name) then
      params[#params + 1] = { index = i, name = name, value = reaper.TrackFX_GetParamNormalized(t, fx, i) }
    end
  end
  local has_chunk, chunk = reaper.TrackFX_GetNamedConfigParm(t, fx, "vst_chunk")
  local _, preset = reaper.TrackFX_GetPreset(t, fx, "")
  local details = fx_details(t, fx)
  return {
    plugin = fx_name(t, fx),
    file = fx_file(t, fx),
    format = details.format,
    instrument = details.instrument or false,
    preset = preset ~= "" and preset or nil,
    chunk = has_chunk and chunk ~= "" and chunk or nil,
    params = params,
    track = track_ref(t),
  }
end

-- Recreates a captured sound on a track: on a matching plugin already there,
-- else on a new instance (an instrument replaces a different instrument).
function commands.apply_fx_state(p)
  local s = p.state or fail("no sound state given")
  local t -- created inside the undo block when new_track_name is given
  if not p.new_track_name then
    t = get_track(p.track)
    if t == reaper.GetMasterTrack(0) and s.instrument then fail("instruments can't go on the master track") end
  end
  return with_undo("load sound " .. (p.sound_name or s.plugin), function()
    if not t then
      local index = reaper.CountTracks(0)
      reaper.InsertTrackAtIndex(index, true)
      t = reaper.GetTrack(0, index)
      reaper.GetSetMediaTrackInfo_String(t, "P_NAME", p.new_track_name, true)
    end
    local fx
    if p.fx then
      fx = get_fx(t, p.fx)
    else
      for i = 0, reaper.TrackFX_GetCount(t) - 1 do
        if (s.file ~= "" and fx_file(t, i) == s.file) or fx_name(t, i) == s.plugin then fx = i break end
      end
    end
    local replaced
    if not fx then
      if s.instrument and p.replace_instrument ~= false then
        local old = reaper.TrackFX_GetInstrument(t)
        if old >= 0 then
          replaced = fx_name(t, old)
          reaper.TrackFX_Delete(t, old)
        end
      end
      fx = reaper.TrackFX_AddByName(t, s.plugin, false, s.instrument and -1000 or -1)
      if fx < 0 then fail(s.plugin .. " isn't installed on this computer, so this sound can't be loaded") end
    end

    local restored
    if s.chunk and reaper.TrackFX_SetNamedConfigParm(t, fx, "vst_chunk", s.chunk) then
      restored = "full plugin state"
    elseif s.params then
      local set, count = 0, reaper.TrackFX_GetNumParams(t, fx)
      for _, prm in ipairs(s.params) do
        local index = int(prm.index)
        if index < count then
          local _, name = reaper.TrackFX_GetParamName(t, fx, index, "")
          if name == prm.name then
            reaper.TrackFX_SetParamNormalized(t, fx, index, prm.value)
            set = set + 1
          end
        end
      end
      restored = set .. " of " .. #s.params .. " parameters"
    end
    return { track = track_ref(t), fx = fx_details(t, fx), restored = restored, replaced = replaced }
  end)
end

-- Splits a multi-output instrument (drum machines, Overbridge, multitimbral
-- synths) onto one track per stereo output. Outputs 1/2 stay on the instrument
-- track; each new track receives one output pair post-FX.
function commands.split_instrument_outputs(p)
  local t = get_track(p.track)
  local fx = p.fx and get_fx(t, p.fx) or reaper.TrackFX_GetInstrument(t)
  if fx < 0 then fail("track '" .. track_name(t) .. "' has no instrument") end
  local _, _, outs = reaper.TrackFX_GetIOSize(t, fx)
  local name = fx_name(t, fx)
  if outs <= 2 then fail(name .. " has only " .. outs .. " outputs") end

  local function pin_name(pin)
    local s = named_config(t, fx, "out_pin_" .. pin) or ("Out " .. (pin + 1))
    return (s:gsub("%s*%([LR]%)$", ""):gsub("%s+[LR]$", ""):gsub("%s+[Ll]eft$", ""):gsub("%s+[Rr]ight$", ""))
  end
  local wanted
  if p.outputs then
    wanted = {}
    for _, o in ipairs(p.outputs) do wanted[trim_lower(tostring(o))] = true end
  end
  local outputs = {}
  for pin = 2, outs - 1, 2 do
    local label = pin_name(pin)
    local number = tostring(pin // 2 + 1)
    if label ~= "(unused)" and (not wanted or wanted[trim_lower(label)] or wanted[number]) then
      outputs[#outputs + 1] = { channel = pin, name = label, mono = pin + 1 >= outs, pair = pin // 2 + 1 }
    end
  end
  if #outputs == 0 then fail("no matching outputs; " .. name .. " has " .. outs .. " output channels") end

  -- Leave pairs that already feed another track alone.
  local taken = {}
  for i = 0, reaper.GetTrackNumSends(t, 0) - 1 do
    taken[int(reaper.GetTrackSendInfo_Value(t, 0, i, "I_SRCCHAN")) & 1023] = true
  end

  return with_undo("split outputs of " .. name, function()
    local nchan = math.min(128, outs + outs % 2)
    if reaper.GetMediaTrackInfo_Value(t, "I_NCHAN") < nchan then
      reaper.SetMediaTrackInfo_Value(t, "I_NCHAN", nchan)
    end
    -- Only the main pair goes to the parent/master; the rest go to the new tracks.
    reaper.SetMediaTrackInfo_Value(t, "C_MAINSEND_NCH", 2)
    local source_name = track_name(t)
    local color = reaper.GetTrackColor(t)
    local insert_at = int(reaper.GetMediaTrackInfo_Value(t, "IP_TRACKNUMBER"))
    local created, skipped = {}, {}
    for _, o in ipairs(outputs) do
      if taken[o.channel] then
        skipped[#skipped + 1] = o.name
      else
        reaper.InsertTrackAtIndex(insert_at, true)
        local dest = reaper.GetTrack(0, insert_at)
        insert_at = insert_at + 1
        reaper.GetSetMediaTrackInfo_String(dest, "P_NAME", source_name .. " - " .. o.name, true)
        if color ~= 0 then reaper.SetTrackColor(dest, color) end
        local send = reaper.CreateTrackSend(t, dest)
        reaper.SetTrackSendInfo_Value(t, 0, send, "I_SRCCHAN", o.channel | (o.mono and 1024 or 0))
        reaper.SetTrackSendInfo_Value(t, 0, send, "I_DSTCHAN", 0)
        reaper.SetTrackSendInfo_Value(t, 0, send, "I_SENDMODE", 3)
        created[#created + 1] = {
          track = track_ref(dest), output = o.name,
          channels = o.mono and tostring(o.channel + 1) or ((o.channel + 1) .. "/" .. (o.channel + 2)),
        }
      end
    end
    return {
      instrument = name,
      created = created,
      already_routed = #skipped > 0 and skipped or nil,
      main_output = pin_name(0) .. " stays on '" .. source_name .. "'",
      note = "sounds only reach these tracks once they're assigned to those outputs inside the plugin",
    }
  end)
end

function commands.get_instrument_notes(p)
  local t = p.item_id and reaper.GetMediaItem_Track(find_item(p.item_id)) or get_track(p.track)
  local instrument = reaper.TrackFX_GetInstrument(t)
  local chan = int((p.channel or 1) - 1)
  local names = {}
  for pitch = 0, 127 do
    local name = reaper.GetTrackMIDINoteNameEx(0, t, pitch, chan)
    if name and name ~= "" then names[#names + 1] = { pitch = pitch, name = name } end
  end
  return {
    track = track_ref(t),
    instrument = instrument >= 0 and fx_name(t, instrument) or nil,
    note_names = names,
  }
end

function commands.set_tempo(p)
  return with_undo("set tempo", function()
    if reaper.CountTempoTimeSigMarkers(0) == 0 and not p.numerator then
      reaper.SetCurrentBPM(0, p.bpm, true)
    else
      local bpm, num, denom, linear, timepos = p.bpm, p.numerator, p.denominator, false, 0
      if reaper.CountTempoTimeSigMarkers(0) > 0 then
        local _, pos, _, _, old_bpm, old_num, old_denom, old_linear = reaper.GetTempoTimeSigMarker(0, 0)
        timepos, linear = pos, old_linear
        bpm = bpm or old_bpm
        num = num or (old_num > 0 and old_num or nil)
        denom = denom or (old_denom > 0 and old_denom or nil)
        if num and not denom then denom = 4 end
        reaper.SetTempoTimeSigMarker(0, 0, timepos, -1, -1, bpm, num or 0, denom or 0, linear)
      else
        local _, _, current_bpm = reaper.TimeMap_GetTimeSigAtTime(0, 0)
        reaper.SetTempoTimeSigMarker(0, -1, 0, -1, -1, bpm or current_bpm, num, denom or 4, false)
      end
    end
    reaper.UpdateTimeline()
    local num, denom, bpm = reaper.TimeMap_GetTimeSigAtTime(0, 0)
    return { tempo_bpm = round(bpm, 3), time_signature = num .. "/" .. denom }
  end)
end

function commands.create_track(p)
  -- Resolve first, so an ambiguous name fails before anything changes.
  local instrument_name = p.instrument and (resolve_plugin(p.instrument, true) or p.instrument)
  return with_undo("create track " .. (p.name or ""), function()
    local count = reaper.CountTracks(0)
    local index = count
    if p.position then index = math.max(0, math.min(int(p.position) - 1, count)) end
    reaper.InsertTrackAtIndex(index, true)
    local t = reaper.GetTrack(0, index)
    if p.name then reaper.GetSetMediaTrackInfo_String(t, "P_NAME", p.name, true) end
    if p.color then set_color(t, p.color) end
    local result = {}
    if p.instrument then
      local fx = reaper.TrackFX_AddByName(t, instrument_name, false, -1)
      if fx < 0 then
        result.warning = "couldn't find an instrument named '" .. p.instrument
          .. "'; the track was created without one (list_installed_fx can search)"
      else
        result.instrument = fx_details(t, fx)
        if p.show_instrument then reaper.TrackFX_Show(t, fx, 3) end
      end
    end
    result.track = track_summary(t)
    return result
  end)
end

function commands.set_track_properties(p)
  local t = get_track(p.track)
  return with_undo("edit track " .. track_name(t), function()
    if p.name then reaper.GetSetMediaTrackInfo_String(t, "P_NAME", p.name, true) end
    if p.volume_db then reaper.SetMediaTrackInfo_Value(t, "D_VOL", db_to_amp(p.volume_db)) end
    if p.pan then reaper.SetMediaTrackInfo_Value(t, "D_PAN", math.max(-1, math.min(1, p.pan))) end
    if p.mute ~= nil then reaper.SetMediaTrackInfo_Value(t, "B_MUTE", p.mute and 1 or 0) end
    if p.solo ~= nil then reaper.SetMediaTrackInfo_Value(t, "I_SOLO", p.solo and 2 or 0) end
    if p.color then set_color(t, p.color) end
    if p.selected ~= nil then reaper.SetTrackSelected(t, p.selected) end
    if p.main_send ~= nil then reaper.SetMediaTrackInfo_Value(t, "B_MAINSEND", p.main_send and 1 or 0) end
    return track_summary(t)
  end)
end

-- What a destructive command would affect, so it can be confirmed first.
function commands.describe_track(p)
  local t = get_track(p.track, true)
  local summary = track_summary(t)
  return { number = summary.number, name = summary.name, item_count = summary.item_count, fx = summary.fx,
           volume_db = summary.volume_db }
end

function commands.delete_track(p)
  local t = get_track(p.track, true)
  if t == reaper.GetMasterTrack(0) then fail("the master track can't be deleted") end
  local name = track_name(t)
  with_undo("delete track " .. name, function() reaper.DeleteTrack(t) end)
  return { deleted = name }
end

function commands.set_send(p)
  local src, dest = get_track(p.source), get_track(p.destination)
  if src == dest then fail("a track can't send to itself") end
  local dest_guid = reaper.GetTrackGUID(dest)
  local index
  for i = 0, reaper.GetTrackNumSends(src, 0) - 1 do
    local other = reaper.GetTrackSendInfo_Value(src, 0, i, "P_DESTTRACK")
    if other and reaper.GetTrackGUID(other) == dest_guid then index = i break end
  end
  return with_undo("send " .. track_name(src) .. " -> " .. track_name(dest), function()
    if p.remove then
      if not index then fail("there's no send from '" .. track_name(src) .. "' to '" .. track_name(dest) .. "'") end
      reaper.RemoveTrackSend(src, 0, index)
      return { removed = true }
    end
    if not index then index = reaper.CreateTrackSend(src, dest) end
    if p.volume_db then reaper.SetTrackSendInfo_Value(src, 0, index, "D_VOL", db_to_amp(p.volume_db)) end
    if p.pan then reaper.SetTrackSendInfo_Value(src, 0, index, "D_PAN", p.pan) end
    if p.mute ~= nil then reaper.SetTrackSendInfo_Value(src, 0, index, "B_MUTE", p.mute and 1 or 0) end
    if p.mode then
      local mode = SEND_MODE_IDS[p.mode] or fail("send mode must be post-fader, pre-fx or post-fx")
      reaper.SetTrackSendInfo_Value(src, 0, index, "I_SENDMODE", mode)
    end
    return send_info(src, 0, index)
  end)
end

function commands.add_fx(p)
  local t = get_track(p.track)
  local name = resolve_plugin(p.name) or p.name
  local index = with_undo("add " .. p.name .. " to " .. track_name(t), function()
    local instantiate = -1
    if p.position then instantiate = -1000 - math.max(0, int(p.position) - 1) end
    local i = reaper.TrackFX_AddByName(t, name, false, instantiate)
    if i < 0 then
      fail("couldn't find an installed FX named '" .. p.name .. "' (list_installed_fx can search)")
    end
    if p.show then reaper.TrackFX_Show(t, i, 3) end
    return i
  end)
  local result = fx_details(t, index)
  result.track = track_ref(t)
  return result
end

function commands.set_fx_parameter(p)
  local t = get_track(p.track)
  local fx = get_fx(t, p.fx)
  return with_undo("set " .. fx_name(t, fx) .. " parameter", function()
    local info = apply_param_change(t, fx, p)
    info.fx = fx_name(t, fx)
    return info
  end)
end

-- Several changes as one undo step; each one succeeds or reports its own error.
function commands.set_fx_parameters(p)
  local t = get_track(p.track)
  local fx = get_fx(t, p.fx)
  return with_undo("set " .. fx_name(t, fx) .. " parameters", function()
    local results = {}
    for i, change in ipairs(p.changes or {}) do
      local ok, info = pcall(apply_param_change, t, fx, change)
      if ok then
        results[i] = info
      else
        results[i] = { parameter = change.parameter, error = type(info) == "table" and info.message or tostring(info) }
      end
    end
    return { fx = fx_name(t, fx), results = results }
  end)
end

function commands.update_fx(p)
  local t = get_track(p.track)
  local fx = get_fx(t, p.fx)
  return with_undo("update " .. fx_name(t, fx), function()
    local result = {}
    if p.enabled ~= nil then reaper.TrackFX_SetEnabled(t, fx, p.enabled) end
    if p.preset then
      if not reaper.TrackFX_SetPreset(t, fx, p.preset) then
        result.warning = "no preset named '" .. p.preset .. "' was found (list_fx_presets lists them)"
      end
    end
    if p.preset_index then
      local _, count = reaper.TrackFX_GetPresetIndex(t, fx)
      if p.preset_index < 1 or p.preset_index > count then fail("preset_index must be 1 to " .. count) end
      reaper.TrackFX_SetPresetByIndex(t, fx, int(p.preset_index) - 1)
    end
    if p.show ~= nil then reaper.TrackFX_Show(t, fx, p.show and 3 or 2) end
    local _, preset = reaper.TrackFX_GetPreset(t, fx, "")
    result.fx = { index = fx + 1, name = fx_name(t, fx), enabled = reaper.TrackFX_GetEnabled(t, fx),
                  preset = preset ~= "" and preset or nil }
    return result
  end)
end

function commands.remove_fx(p)
  local t = get_track(p.track)
  local fx = get_fx(t, p.fx)
  local name = fx_name(t, fx)
  with_undo("remove " .. name, function() reaper.TrackFX_Delete(t, fx) end)
  return { removed = name, track = track_ref(t) }
end

function commands.create_midi_item(p)
  local t = get_track(p.track)
  if t == reaper.GetMasterTrack(0) then fail("items can't go on the master track") end
  local start_qn = resolve_qn(p, "start", time_to_qn(reaper.GetCursorPosition()))
  local end_qn
  if p.length_bars then
    if p.start_bar then
      end_qn = bar_to_qn(p.start_bar + p.length_bars, p.start_beat)
    else
      end_qn = start_qn + p.length_bars * bar_length_qn_at(start_qn)
    end
  elseif p.length_qn then
    end_qn = start_qn + p.length_qn
  else
    end_qn = start_qn + 4 * bar_length_qn_at(start_qn)
  end
  if end_qn <= start_qn then fail("the item length must be positive") end
  return with_undo("create MIDI item", function()
    local item = reaper.CreateNewMIDIItemInProj(t, start_qn, end_qn, true)
    if not item then fail("REAPER couldn't create the item") end
    if p.name then reaper.GetSetMediaItemTakeInfo_String(reaper.GetActiveTake(item), "P_NAME", p.name, true) end
    return item_info(item)
  end)
end

local function delete_notes(take, base_qn, p)
  local _, count = reaper.MIDI_CountEvts(take)
  local deleted = 0
  for i = count - 1, 0, -1 do
    local _, _, _, start_ppq, _, chan, pitch = reaper.MIDI_GetNote(take, i)
    local start = reaper.MIDI_GetProjQNFromPPQPos(take, start_ppq) - base_qn
    local hit = true
    if p.start and start < p.start - 1e-6 then hit = false end
    if p["end"] and start >= p["end"] - 1e-6 then hit = false end
    if p.pitch and pitch ~= p.pitch then hit = false end
    if p.channel and chan ~= p.channel - 1 then hit = false end
    if hit then
      reaper.MIDI_DeleteNote(take, i)
      deleted = deleted + 1
    end
  end
  return deleted
end

function commands.add_midi_notes(p)
  local item = find_item(p.item_id)
  local take = midi_take(item)
  return with_undo("add MIDI notes", function()
    local base_qn, end_qn = item_bounds_qn(item)
    local replaced = p.replace and delete_notes(take, base_qn, {}) or nil
    local last = base_qn
    for _, n in ipairs(p.notes or {}) do
      local s = base_qn + n.start
      local e = s + n.length
      reaper.MIDI_InsertNote(
        take, n.selected or false, n.muted or false,
        reaper.MIDI_GetPPQPosFromProjQN(take, s), reaper.MIDI_GetPPQPosFromProjQN(take, e),
        int((n.channel or 1) - 1), int(n.pitch), int(n.velocity or 96), true)
      if e > last then last = e end
    end
    reaper.MIDI_Sort(take)
    local result = { item_id = item_guid(item), added = #(p.notes or {}), replaced = replaced }
    if last > end_qn + 1e-6 and p.extend_item ~= false then
      local _, bar_start, bar_end = reaper.TimeMap_QNToMeasures(0, last - 1e-6)
      reaper.MIDI_SetItemExtents(item, base_qn, bar_end)
      result.extended_item_to = time_to_pos(qn_to_time(bar_end))
    end
    local _, total = reaper.MIDI_CountEvts(take)
    result.note_count = total
    return result
  end)
end

function commands.get_midi_notes(p)
  local item = find_item(p.item_id)
  local take = midi_take(item)
  local base_qn = item_bounds_qn(item)
  local _, count = reaper.MIDI_CountEvts(take)
  local limit = p.limit or 2000
  local notes = {}
  for i = 0, math.min(count, limit) - 1 do
    local _, selected, muted, start_ppq, end_ppq, chan, pitch, vel = reaper.MIDI_GetNote(take, i)
    local s = reaper.MIDI_GetProjQNFromPPQPos(take, start_ppq)
    local e = reaper.MIDI_GetProjQNFromPPQPos(take, end_ppq)
    notes[#notes + 1] = {
      pitch = pitch, start = round(s - base_qn, 4), length = round(e - s, 4),
      velocity = vel, channel = chan + 1, muted = muted or nil, selected = selected or nil,
    }
  end
  local info = item_info(item)
  info.notes = notes
  info.truncated = count > limit and count or nil
  return info
end

function commands.delete_midi_notes(p)
  local item = find_item(p.item_id)
  local take = midi_take(item)
  return with_undo("delete MIDI notes", function()
    local deleted = delete_notes(take, item_bounds_qn(item), p)
    reaper.MIDI_Sort(take)
    local _, total = reaper.MIDI_CountEvts(take)
    return { deleted = deleted, note_count = total }
  end)
end

function commands.add_midi_cc(p)
  local item = find_item(p.item_id)
  local take = midi_take(item)
  return with_undo("add MIDI CC", function()
    local base_qn = item_bounds_qn(item)
    local chan = int((p.channel or 1) - 1)
    for _, ev in ipairs(p.events or {}) do
      local ppq = reaper.MIDI_GetPPQPosFromProjQN(take, base_qn + ev.position)
      if ev.cc == "pitchbend" then
        local v = math.max(0, math.min(16383, int(ev.value) + 8192))
        reaper.MIDI_InsertCC(take, false, false, ppq, 0xE0, chan, v & 0x7F, (v >> 7) & 0x7F)
      elseif ev.cc == "program" then
        reaper.MIDI_InsertCC(take, false, false, ppq, 0xC0, chan, math.max(0, math.min(127, int(ev.value))), 0)
      elseif ev.cc == "aftertouch" then
        reaper.MIDI_InsertCC(take, false, false, ppq, 0xD0, chan, math.max(0, math.min(127, int(ev.value))), 0)
      else
        reaper.MIDI_InsertCC(take, false, false, ppq, 0xB0, chan, int(ev.cc), math.max(0, math.min(127, int(ev.value))))
      end
    end
    reaper.MIDI_Sort(take)
    return { added = #(p.events or {}) }
  end)
end

function commands.add_marker(p)
  local start_qn = resolve_qn(p, "start") or fail("a position is required")
  local end_qn = resolve_qn(p, "end")
  local color = 0
  if p.color then
    local r, g, b = tostring(p.color):match("^#?(%x%x)(%x%x)(%x%x)$")
    if not r then fail("colors look like #RRGGBB") end
    color = reaper.ColorToNative(tonumber(r, 16), tonumber(g, 16), tonumber(b, 16)) | 0x1000000
  end
  return with_undo("add marker " .. p.name, function()
    local is_region = end_qn ~= nil
    local pos = qn_to_time(start_qn)
    local finish = is_region and qn_to_time(end_qn) or 0
    local number = reaper.AddProjectMarker2(0, is_region, pos, finish, p.name, -1, color)
    return { type = is_region and "region" or "marker", number = number, name = p.name,
             start = time_to_pos(pos), ["end"] = is_region and time_to_pos(finish) or nil }
  end)
end

function commands.transport(p)
  local action = p.action
  if action == "stop" then
    reaper.OnStopButton()
    stop_at = nil
  elseif action == "pause" then
    reaper.OnPauseButton()
  elseif action == "play" or action == "go_to" then
    local start_qn = resolve_qn(p, "start")
    local end_qn = resolve_qn(p, "end")
    if start_qn then reaper.SetEditCurPos(qn_to_time(start_qn), true, false) end
    if action == "play" then
      if end_qn then
        local start_t = start_qn and qn_to_time(start_qn) or reaper.GetCursorPosition()
        reaper.GetSet_LoopTimeRange(true, true, start_t, qn_to_time(end_qn), false)
        reaper.GetSetRepeat(p.loop and 1 or 0)
        stop_at = (not p.loop) and qn_to_time(end_qn) or nil
      end
      reaper.OnPlayButton()
    end
  else
    fail("action must be play, stop, pause or go_to")
  end
  return { action = action, edit_cursor = time_to_pos(reaper.GetCursorPosition()) }
end

function commands.undo(p)
  local undone = {}
  for _ = 1, math.max(1, int(p.steps or 1)) do
    local description = reaper.Undo_CanUndo2(0)
    if not description then break end
    reaper.Undo_DoUndo2(0)
    undone[#undone + 1] = description
  end
  return { undone = undone }
end

local function lookup_action(command)
  local id = tonumber(command)
  if not id then id = reaper.NamedCommandLookup(tostring(command)) end
  if not id or id == 0 then fail("no action with id '" .. tostring(command) .. "'") end
  local name = reaper.kbd_getTextFromCmd(id, 0)
  if name == "" then fail("no action with id '" .. tostring(command) .. "'") end
  return id, name
end

function commands.describe_action(p)
  local id, name = lookup_action(p.command)
  return { command_id = id, name = name }
end

function commands.run_action(p)
  local id, name = lookup_action(p.command)
  reaper.Main_OnCommand(id, 0)
  return { ran = name, command_id = id }
end

function commands.time_to_positions(p)
  local out = {}
  for i, t in ipairs(p.times or {}) do out[i] = time_to_pos(t) end
  return out
end

-- Render settings we touch, saved and restored around every render.
local RENDER_STRING_KEYS = { "RENDER_FILE", "RENDER_PATTERN", "RENDER_FORMAT", "RENDER_FORMAT2" }
local RENDER_NUMBER_KEYS = {
  "RENDER_SETTINGS", "RENDER_BOUNDSFLAG", "RENDER_STARTPOS", "RENDER_ENDPOS", "RENDER_SRATE",
  "RENDER_CHANNELS", "RENDER_TAILFLAG", "RENDER_ADDTOPROJ", "RENDER_DITHER", "RENDER_NORMALIZE",
}
local WAV_32_FLOAT = "ZXZhdyAA" -- base64 of the WAV sink config: 'evaw', 32-bit float

-- Renders [start_t, end_t] of a track (stem) or the master to a 32-bit float WAV in
-- RENDER_DIR, restoring the user's render settings and track selection afterwards.
local function render_range(t, master, start_t, end_t)
  local wanted = {}
  local list = type(t) == "table" and t or { t }
  for _, tr in ipairs(list) do wanted[tr] = true end
  local saved_strings, saved_numbers, saved_selection = {}, {}, {}
  for _, k in ipairs(RENDER_STRING_KEYS) do
    local _, v = reaper.GetSetProjectInfo_String(0, k, "", false)
    saved_strings[k] = v
  end
  for _, k in ipairs(RENDER_NUMBER_KEYS) do saved_numbers[k] = reaper.GetSetProjectInfo(0, k, 0, false) end
  for i = 0, reaper.CountTracks(0) - 1 do
    local tr = reaper.GetTrack(0, i)
    saved_selection[tr] = reaper.IsTrackSelected(tr)
  end

  reaper.RecursiveCreateDirectory(RENDER_DIR, 0)
  local name = string.format("render_%d_%04d", os.time(), math.random(0, 9999))
  if #list > 1 then name = name .. "_$tracknumber" end
  local ok, result = pcall(function()
    reaper.GetSetProjectInfo_String(0, "RENDER_FILE", RENDER_DIR, true)
    reaper.GetSetProjectInfo_String(0, "RENDER_PATTERN", name, true)
    reaper.GetSetProjectInfo_String(0, "RENDER_FORMAT", WAV_32_FLOAT, true)
    reaper.GetSetProjectInfo_String(0, "RENDER_FORMAT2", "", true)
    reaper.GetSetProjectInfo(0, "RENDER_BOUNDSFLAG", 0, true)
    reaper.GetSetProjectInfo(0, "RENDER_STARTPOS", start_t, true)
    reaper.GetSetProjectInfo(0, "RENDER_ENDPOS", end_t, true)
    reaper.GetSetProjectInfo(0, "RENDER_SRATE", project_sample_rate(), true)
    reaper.GetSetProjectInfo(0, "RENDER_CHANNELS", 2, true)
    reaper.GetSetProjectInfo(0, "RENDER_TAILFLAG", 0, true)
    reaper.GetSetProjectInfo(0, "RENDER_ADDTOPROJ", 0, true)
    reaper.GetSetProjectInfo(0, "RENDER_DITHER", 0, true)
    reaper.GetSetProjectInfo(0, "RENDER_NORMALIZE", 0, true)
    if master then
      reaper.GetSetProjectInfo(0, "RENDER_SETTINGS", 0, true)
    else
      for tr in pairs(saved_selection) do reaper.SetTrackSelected(tr, wanted[tr] or false) end
      reaper.GetSetProjectInfo(0, "RENDER_SETTINGS", 3, true) -- stems (selected tracks) only
    end
    local _, targets = reaper.GetSetProjectInfo_String(0, "RENDER_TARGETS", "", false)
    reaper.Main_OnCommand(42230, 0) -- File: Render project, using the most recent render settings, auto-close
    return targets
  end)

  for k, v in pairs(saved_strings) do reaper.GetSetProjectInfo_String(0, k, v, true) end
  for k, v in pairs(saved_numbers) do reaper.GetSetProjectInfo(0, k, v, true) end
  for tr, was_selected in pairs(saved_selection) do reaper.SetTrackSelected(tr, was_selected) end
  if not ok then error(result, 0) end

  local files = {}
  for path in tostring(result):gmatch("[^;]+") do
    if reaper.file_exists(path) then files[#files + 1] = path end
  end
  if #files == 0 then fail("REAPER didn't produce a render file (expected: " .. tostring(result) .. ")") end

  return files
end

function commands.render_audio(p)
  local t = get_track(p.track or "master")
  local master = t == reaper.GetMasterTrack(0)
  local start_qn, end_qn = resolve_qn(p, "start"), resolve_qn(p, "end")
  local start_t = start_qn and qn_to_time(start_qn) or 0
  local end_t = end_qn and qn_to_time(end_qn) or reaper.GetProjectLength(0)
  if end_t <= start_t then fail("nothing to render: the range is empty (is the project empty?)") end
  end_t = end_t + math.max(0, math.min(30, tonumber(p.tail_seconds) or 0))
  if end_t - start_t > 1800 then fail("renders are limited to 30 minutes; pick a shorter range") end

  local files = render_range(t, master, start_t, end_t)

  -- The tracks whose audio is in this render: everything for the master, else
  -- the track and anything in its folder.
  local rendered = { t }
  for i = 0, reaper.CountTracks(0) - 1 do
    local tr = reaper.GetTrack(0, i)
    local parent = reaper.GetParentTrack(tr)
    while parent and not master do
      if parent == t then rendered[#rendered + 1] = tr break end
      parent = reaper.GetParentTrack(parent)
    end
    if master then rendered[#rendered + 1] = tr end
  end
  local realtime = realtime_only_fx(rendered)
  return {
    files = files,
    track = track_ref(t),
    start = time_to_pos(start_t),
    ["end"] = time_to_pos(end_t),
    warning = #realtime > 0 and ("these plugins only produce sound in real time, so this offline render "
      .. "may be missing their audio: " .. table.concat(realtime, ", ")
      .. ". To measure them, record or render their output to an audio track first.") or nil,
  }
end

--------------------------------------------------------- stems and saving

-- Renders each track's own output (post-fader, without the master's effects) in one pass.
function commands.render_stems(p)
  local tracks = {}
  for _, ref in ipairs(p.tracks or {}) do tracks[#tracks + 1] = get_track(ref) end
  if #tracks == 0 then fail("no tracks to render") end
  local start_qn, end_qn = resolve_qn(p, "start"), resolve_qn(p, "end")
  local start_t = start_qn and qn_to_time(start_qn) or 0
  local end_t = (end_qn and qn_to_time(end_qn) or reaper.GetProjectLength(0))
    + math.max(0, math.min(30, tonumber(p.tail_seconds) or 0))
  if end_t <= start_t then fail("nothing to render: the range is empty") end
  local files = render_range(tracks, false, start_t, end_t)
  local by_track = {}
  for _, tr in ipairs(tracks) do
    local number = int(reaper.GetMediaTrackInfo_Value(tr, "IP_TRACKNUMBER"))
    for _, f in ipairs(files) do
      local tail = f:match("_(%d+)%.[%w]+$")
      if tail and int(tonumber(tail)) == number then by_track[#by_track + 1] = { track = track_ref(tr), file = f } end
    end
  end
  return { stems = by_track, files = files, start = time_to_pos(start_t), ["end"] = time_to_pos(end_t) }
end

function commands.save_project(p)
  local proj, current = reaper.EnumProjects(-1)
  if p.mode == "save" then
    if current == "" then fail("the project has no file yet: give a name to save it as") end
    reaper.Main_OnCommand(40026, 0) -- File: Save project
  elseif p.mode == "copy" then
    reaper.Main_SaveProjectEx(proj, p.path, 0)
    if not reaper.file_exists(p.path) then fail("REAPER couldn't write " .. p.path) end
  else -- save as: write the file, then open it in this tab so the project is attached to it
    reaper.Main_SaveProjectEx(proj, p.path, 0)
    if not reaper.file_exists(p.path) then fail("REAPER couldn't write " .. p.path) end
    reaper.Main_openProject("noprompt:" .. p.path)
  end
  local _, now = reaper.EnumProjects(-1)
  return { path = now ~= "" and now or nil, written = p.path or now, dirty = reaper.IsProjectDirty(0) == 1,
           project = reaper.GetProjectName(0, "") }
end

function commands.project_paths()
  local _, current = reaper.EnumProjects(-1)
  return { project = current ~= "" and current or nil, default_folder = reaper.GetProjectPath(""),
           name = reaper.GetProjectName(0, "") }
end

------------------------------------------------------------ recording

function commands.list_inputs()
  local audio, midi = {}, {}
  for i = 0, reaper.GetNumAudioInputs() - 1 do
    audio[#audio + 1] = { channel = i + 1, name = reaper.GetInputChannelName(i) }
  end
  for i = 0, reaper.GetNumMIDIInputs() - 1 do
    local ok, name = reaper.GetMIDIInputName(i, "")
    if ok then midi[#midi + 1] = { device = i, name = name } end
  end
  return { audio_inputs = audio, midi_inputs = midi }
end

local RECMODES = { input = 0, output = 1, none = 2, ["midi overdub"] = 7, ["midi replace"] = 8 }
local MONITOR = { off = 0, on = 1, auto = 2 }

local function describe_input(v)
  v = int(v)
  if v < 0 then return "none" end
  if v & 4096 ~= 0 then
    local device, chan = (v >> 5) & 63, v & 31
    local name = device == 63 and "all MIDI inputs" or device == 62 and "virtual keyboard"
      or select(2, reaper.GetMIDIInputName(device, "")) or ("MIDI device " .. device)
    return "MIDI: " .. name .. (chan == 0 and ", all channels" or (", channel " .. chan))
  end
  local start = (v & 1023) + 1
  if v & 1024 ~= 0 then return "audio: inputs " .. start .. "-" .. (start + 1) .. " (stereo)" end
  return "audio: input " .. start .. " (mono)"
end

local function record_info(t)
  return {
    track = track_ref(t),
    armed = reaper.GetMediaTrackInfo_Value(t, "I_RECARM") == 1,
    input = describe_input(reaper.GetMediaTrackInfo_Value(t, "I_RECINPUT")),
    monitoring = ({ [0] = "off", [1] = "on", [2] = "auto" })[int(reaper.GetMediaTrackInfo_Value(t, "I_RECMON"))],
  }
end

function commands.set_record_settings(p)
  local t = get_track(p.track)
  return with_undo("record settings on " .. track_name(t), function()
    if p.audio_input then
      local first = int(p.audio_input) - 1
      if first < 0 or first >= reaper.GetNumAudioInputs() then fail("there's no audio input " .. p.audio_input) end
      reaper.SetMediaTrackInfo_Value(t, "I_RECINPUT", p.stereo and (1024 + first) or first)
      reaper.SetMediaTrackInfo_Value(t, "I_RECMODE", 0)
    elseif p.midi_device then
      local device = p.midi_device == "all" and 63 or int(p.midi_device)
      local chan = math.max(0, math.min(16, int(p.midi_channel or 0)))
      reaper.SetMediaTrackInfo_Value(t, "I_RECINPUT", 4096 + (device << 5) + chan)
      reaper.SetMediaTrackInfo_Value(t, "I_RECMODE", RECMODES[p.mode or "input"] or 0)
    elseif p.no_input then
      reaper.SetMediaTrackInfo_Value(t, "I_RECINPUT", -1)
    end
    if p.mode and not p.midi_device then reaper.SetMediaTrackInfo_Value(t, "I_RECMODE", RECMODES[p.mode] or 0) end
    if p.monitor then reaper.SetMediaTrackInfo_Value(t, "I_RECMON", MONITOR[p.monitor] or 1) end
    if p.arm ~= nil then reaper.SetMediaTrackInfo_Value(t, "I_RECARM", p.arm and 1 or 0) end
    return record_info(t)
  end)
end

function commands.record(p)
  local armed = {}
  for i = 0, reaper.CountTracks(0) - 1 do
    local t = reaper.GetTrack(0, i)
    if reaper.GetMediaTrackInfo_Value(t, "I_RECARM") == 1 then armed[#armed + 1] = record_info(t) end
  end
  if #armed == 0 then fail("no track is armed for recording: arm one first (set_record_settings arm=true)") end
  local start_qn = resolve_qn(p, "start")
  local end_qn = resolve_qn(p, "end")
  if start_qn then reaper.SetEditCurPos(qn_to_time(start_qn), true, false) end
  stop_at = end_qn and qn_to_time(end_qn) or nil
  reaper.Main_OnCommand(1013, 0) -- Transport: Record
  beat_now = true -- tell clients right away that a stop will bring up the prompt
  return { recording = reaper.GetPlayState() & 4 ~= 0, armed = armed,
           from = time_to_pos(reaper.GetCursorPosition()), stops_at = stop_at and time_to_pos(stop_at) or nil,
           stop_prompt = stop_prompt_on() or nil }
end

function commands.recording_status()
  local state = reaper.GetPlayState()
  return { recording = state & 4 ~= 0, playing = state & 1 ~= 0, position = time_to_pos(reaper.GetPlayPosition()),
           stops_at = stop_at and time_to_pos(stop_at) or nil,
           stop_prompt = state & 4 ~= 0 and stop_prompt_on() or nil }
end

----------------------------------------------------------------- takes

local function take_list(item)
  local active = reaper.GetActiveTake(item)
  local out = {}
  for i = 0, reaper.CountTakes(item) - 1 do
    local take = reaper.GetTake(item, i)
    if take then
      local src = reaper.GetMediaItemTake_Source(take)
      local file = src and reaper.GetMediaSourceFileName(src) or ""
      out[#out + 1] = { take = i + 1, name = reaper.GetTakeName(take), active = take == active or nil,
                        midi = reaper.TakeIsMIDI(take) or nil, file = file ~= "" and file or nil }
    end
  end
  return out
end

function commands.list_takes(p)
  local item = find_item(p.item_id)
  return { item_id = p.item_id, takes = take_list(item) }
end

function commands.set_active_take(p)
  local item = find_item(p.item_id)
  local chosen
  for i = 0, reaper.CountTakes(item) - 1 do
    local take = reaper.GetTake(item, i)
    if take and ((p.take and i + 1 == int(p.take)) or (p.name and reaper.GetTakeName(take):lower() == tostring(p.name):lower())) then
      chosen = take
    end
  end
  if not chosen then fail("that item has no such take") end
  return with_undo("choose take", function()
    reaper.SetActiveTake(chosen)
    reaper.UpdateItemInProject(item)
    return { item_id = p.item_id, takes = take_list(item) }
  end)
end

local function with_items_selected(items, fn)
  local before = {}
  for i = 0, reaper.CountSelectedMediaItems(0) - 1 do before[#before + 1] = reaper.GetSelectedMediaItem(0, i) end
  reaper.SelectAllMediaItems(0, false)
  for _, it in ipairs(items) do reaper.SetMediaItemSelected(it, true) end
  local ok, err = pcall(fn)
  reaper.SelectAllMediaItems(0, false)
  for _, it in ipairs(before) do if reaper.ValidatePtr(it, "MediaItem*") then reaper.SetMediaItemSelected(it, true) end end
  if not ok then error(err, 0) end
end

function commands.explode_takes(p)
  local item = find_item(p.item_id)
  local existing = {}
  for i = 0, reaper.CountTracks(0) - 1 do existing[reaper.GetTrack(0, i)] = true end
  local made = {}
  with_undo("explode takes to tracks", function()
    with_items_selected({ item }, function() reaper.Main_OnCommand(40224, 0) end)
    -- REAPER leaves the new tracks unnamed: name each after the take on it.
    for i = 0, reaper.CountTracks(0) - 1 do
      local t = reaper.GetTrack(0, i)
      if not existing[t] then
        local first = reaper.GetTrackMediaItem(t, 0)
        local take = first and reaper.GetActiveTake(first)
        local _, name = reaper.GetSetMediaTrackInfo_String(t, "P_NAME", "", false)
        if name == "" and take then
          reaper.GetSetMediaTrackInfo_String(t, "P_NAME", (reaper.GetTakeName(take):gsub("%.%w+$", "")), true)
        end
        made[#made + 1] = track_ref(t)
      end
    end
  end)
  return { new_tracks = made }
end

------------------------------------------------- time selection and loop

function commands.set_time_selection(p)
  local start_qn, end_qn = resolve_qn(p, "start"), resolve_qn(p, "end")
  if p.clear then
    reaper.GetSet_LoopTimeRange(true, false, 0, 0, false)
    if p.loop ~= false then reaper.GetSet_LoopTimeRange(true, true, 0, 0, false) end
  else
    if not start_qn or not end_qn or end_qn <= start_qn then fail("give a start and an end after it") end
    local a, b = qn_to_time(start_qn), qn_to_time(end_qn)
    reaper.GetSet_LoopTimeRange(true, false, a, b, false)
    if p.loop then reaper.GetSet_LoopTimeRange(true, true, a, b, false) end
  end
  if p["repeat"] ~= nil then reaper.GetSetRepeat(p["repeat"] and 1 or 0) end
  local s0, s1 = reaper.GetSet_LoopTimeRange(false, false, 0, 0, false)
  local l0, l1 = reaper.GetSet_LoopTimeRange(false, true, 0, 0, false)
  return { time_selection = s1 > s0 and { start = time_to_pos(s0), ["end"] = time_to_pos(s1) } or nil,
           loop = l1 > l0 and { start = time_to_pos(l0), ["end"] = time_to_pos(l1) } or nil,
           ["repeat"] = reaper.GetSetRepeat(-1) == 1 }
end

------------------------------------------------------ markers, regions

local function find_marker(p)
  local _, nm, nr = reaper.CountProjectMarkers(0)
  local found = {}
  for i = 0, nm + nr - 1 do
    local _, isrgn, pos, rgnend, name, number, color = reaper.EnumProjectMarkers3(0, i)
    local kind_ok = p.region == nil or (p.region and isrgn) or (p.region == false and not isrgn)
    if kind_ok and ((p.number and number == int(p.number)) or (p.name and name:lower() == tostring(p.name):lower())) then
      found[#found + 1] = { index = i, isrgn = isrgn, pos = pos, rgnend = rgnend, name = name, number = number, color = color }
    end
  end
  if #found == 0 then fail("no marker or region matches " .. tostring(p.name or p.number)) end
  if #found > 1 then fail("several markers/regions match; give its number, or region=true/false") end
  return found[1]
end

function commands.edit_marker(p)
  local m = find_marker(p)
  return with_undo("edit marker " .. m.name, function()
    local pos = p.start_bar and qn_to_time(bar_to_qn(p.start_bar, p.start_beat)) or m.pos
    local rend = p.end_bar and qn_to_time(bar_to_qn(p.end_bar, p.end_beat)) or m.rgnend
    if m.isrgn and rend <= pos then fail("a region has to end after it starts") end
    local color = m.color
    if p.color then
      local r, g, b = p.color:match("#?(%x%x)(%x%x)(%x%x)")
      if r then color = reaper.ColorToNative(tonumber(r, 16), tonumber(g, 16), tonumber(b, 16)) | 0x1000000 end
    end
    reaper.SetProjectMarkerByIndex2(0, m.index, m.isrgn, pos, rend, m.number, p.new_name or m.name, color, p.new_name == "" and 1 or 0)
    return { kind = m.isrgn and "region" or "marker", name = p.new_name or m.name, start = time_to_pos(pos),
             ["end"] = m.isrgn and time_to_pos(rend) or nil }
  end)
end

function commands.delete_marker(p)
  local m = find_marker(p)
  return with_undo("delete " .. (m.isrgn and "region " or "marker ") .. m.name, function()
    reaper.DeleteProjectMarkerByIndex(0, m.index)
    return { deleted = m.name, kind = m.isrgn and "region" or "marker" }
  end)
end

--------------------------------------------- track templates and freeze

local function template_dir() return reaper.GetResourcePath() .. "/TrackTemplates" end

function commands.save_track_template(p)
  local chunks = {}
  for _, ref in ipairs(p.tracks or {}) do
    local t = get_track(ref)
    local ok, chunk = reaper.GetTrackStateChunk(t, "", false)
    if not ok then fail("couldn't read " .. track_name(t)) end
    chunks[#chunks + 1] = chunk
  end
  if #chunks == 0 then fail("give the tracks to save") end
  reaper.RecursiveCreateDirectory(template_dir(), 0)
  local path = template_dir() .. "/" .. p.name .. ".RTrackTemplate"
  local f = io.open(path, "wb")
  if not f then fail("couldn't write " .. path) end
  f:write(table.concat(chunks, "\n"))
  f:close()
  return { saved = path, tracks = #chunks }
end

function commands.list_track_templates()
  local out = {}
  local function walk(dir, prefix)
    local i = 0
    while true do
      local f = reaper.EnumerateFiles(dir, i)
      if not f then break end
      if f:match("%.RTrackTemplate$") then out[#out + 1] = prefix .. f:gsub("%.RTrackTemplate$", "") end
      i = i + 1
    end
    i = 0
    while true do
      local d = reaper.EnumerateSubdirectories(dir, i)
      if not d then break end
      walk(dir .. "/" .. d, prefix .. d .. "/")
      i = i + 1
    end
  end
  walk(template_dir(), "")
  return { folder = template_dir(), templates = out }
end

function commands.apply_track_template(p)
  local path = template_dir() .. "/" .. p.name .. ".RTrackTemplate"
  if not reaper.file_exists(path) then fail("there's no track template called " .. p.name) end
  local before = reaper.CountTracks(0)
  -- Opening a track template adds its tracks to the project (after the selected track).
  reaper.Main_openProject(path)
  local added = {}
  for i = 0, reaper.CountTracks(0) - 1 do
    local t = reaper.GetTrack(0, i)
    if reaper.IsTrackSelected(t) then added[#added + 1] = track_ref(t) end
  end
  return { added = reaper.CountTracks(0) - before, tracks = added }
end

local function with_tracks_selected(tracks, fn)
  local before = {}
  for i = 0, reaper.CountTracks(0) - 1 do
    local t = reaper.GetTrack(0, i)
    before[t] = reaper.IsTrackSelected(t)
    reaper.SetTrackSelected(t, false)
  end
  for _, t in ipairs(tracks) do reaper.SetTrackSelected(t, true) end
  local ok, err = pcall(fn)
  for t, sel in pairs(before) do if reaper.ValidatePtr(t, "MediaTrack*") then reaper.SetTrackSelected(t, sel) end end
  if not ok then error(err, 0) end
end

function commands.freeze_tracks(p)
  local tracks = {}
  for _, ref in ipairs(p.tracks or {}) do tracks[#tracks + 1] = get_track(ref) end
  if #tracks == 0 then fail("give the tracks") end
  local action = p.unfreeze and 41644 or (p.mono and 40901 or 41223)
  with_tracks_selected(tracks, function() reaper.Main_OnCommand(action, 0) end)
  local out = {}
  for _, t in ipairs(tracks) do
    local frozen = reaper.BR_GetMediaTrackFreezeCount and reaper.BR_GetMediaTrackFreezeCount(t) or nil
    out[#out + 1] = { track = track_ref(t), fx = reaper.TrackFX_GetCount(t), frozen_layers = frozen }
  end
  return { action = p.unfreeze and "unfrozen" or "frozen", tracks = out }
end

------------------------------------------------------------- tempo map

local function tempo_markers()
  local out = {}
  for i = 0, reaper.CountTempoTimeSigMarkers(0) - 1 do
    local _, timepos, _, _, bpm, num, denom, linear = reaper.GetTempoTimeSigMarker(0, i)
    out[#out + 1] = {
      index = i + 1,
      position = time_to_pos(timepos),
      bpm = round(bpm, 3),
      time_signature = num > 0 and (num .. "/" .. denom) or nil,
      ramp_to_next = linear or nil,
    }
  end
  return out
end

function commands.get_tempo_map()
  local num, denom, bpm = reaper.TimeMap_GetTimeSigAtTime(0, 0)
  return { start_tempo_bpm = round(bpm, 3), start_time_signature = num .. "/" .. denom, changes = tempo_markers() }
end

-- Adds or updates tempo and time-signature changes at bars, in time order so each
-- bar is found on the map as it stands after the earlier changes.
function commands.set_tempo_map(p)
  local changes = p.changes or {}
  table.sort(changes, function(a, b) return (a.bar + (a.beat or 1) / 1000) < (b.bar + (b.beat or 1) / 1000) end)
  for _, c in ipairs(changes) do
    if (c.numerator or c.denominator) and (c.beat or 1) ~= 1 then
      fail("time signature changes have to be on a bar line (beat 1), bar " .. tostring(c.bar))
    end
  end
  return with_undo("edit tempo map", function()
    if p.clear then
      for i = reaper.CountTempoTimeSigMarkers(0) - 1, 1, -1 do reaper.DeleteTempoTimeSigMarker(0, i) end
    end
    for _, bar in ipairs(p.remove_bars or {}) do
      for i = reaper.CountTempoTimeSigMarkers(0) - 1, 0, -1 do
        local _, timepos, measure = reaper.GetTempoTimeSigMarker(0, i)
        if measure + 1 == int(bar) and not (i == 0 and timepos < 0.001) then reaper.DeleteTempoTimeSigMarker(0, i) end
      end
    end
    for _, c in ipairs(changes) do
      local t = qn_to_time(bar_to_qn(c.bar, c.beat or 1))
      local bpm = c.bpm or reaper.TimeMap2_GetDividedBpmAtTime(0, t)
      local existing = -1
      for i = 0, reaper.CountTempoTimeSigMarkers(0) - 1 do
        local _, timepos = reaper.GetTempoTimeSigMarker(0, i)
        if math.abs(timepos - t) < 0.001 then existing = i end
      end
      local num, denom = c.numerator or 0, c.denominator or (c.numerator and 4 or 0)
      if existing >= 0 and num == 0 then
        local _, _, _, _, _, old_num, old_denom = reaper.GetTempoTimeSigMarker(0, existing)
        num, denom = old_num, old_denom
      end
      -- Placed by bar and beat, not time: a ramp before it would otherwise slide it off the beat.
      reaper.SetTempoTimeSigMarker(0, existing, -1, int(c.bar) - 1, (c.beat or 1) - 1, bpm, num, denom,
        c.ramp_to_next and true or false)
    end
    reaper.UpdateTimeline()
    return commands.get_tempo_map()
  end)
end

--------------------------------------------------------- MIDI events

local function cc_kind(chanmsg)
  if chanmsg == 0xB0 then return "cc" end
  if chanmsg == 0xE0 then return "pitchbend" end
  if chanmsg == 0xC0 then return "program" end
  if chanmsg == 0xD0 then return "aftertouch" end
  if chanmsg == 0xA0 then return "poly aftertouch" end
  return string.format("0x%X", chanmsg)
end

local function cc_matches(p, kind, number, chan, qn)
  if p.kind and p.kind ~= kind then return false end
  if p.cc and not (kind == "cc" and number == p.cc) then return false end
  if p.channel and chan + 1 ~= p.channel then return false end
  if p.start and qn < p.start - 1e-6 then return false end
  if p["end"] and qn >= p["end"] - 1e-6 then return false end
  return true
end

function commands.get_midi_cc(p)
  local item = find_item(p.item_id)
  local take = midi_take(item)
  local base_qn = item_bounds_qn(item)
  local _, _, count = reaper.MIDI_CountEvts(take)
  local events, limit = {}, p.limit or 2000
  for i = 0, count - 1 do
    local _, _, muted, ppq, chanmsg, chan, msg2, msg3 = reaper.MIDI_GetCC(take, i)
    local qn = reaper.MIDI_GetProjQNFromPPQPos(take, ppq) - base_qn
    local kind = cc_kind(chanmsg)
    local number = kind == "cc" and msg2 or nil
    if cc_matches(p, kind, msg2, chan, qn) and #events < limit then
      local value = msg3
      if kind == "pitchbend" then value = (msg3 << 7 | msg2) - 8192 end
      if kind == "program" then value = msg2 + 1 end
      if kind == "aftertouch" then value = msg2 end
      events[#events + 1] = { position = round(qn, 4), kind = kind, cc = number, value = value, channel = chan + 1,
                              muted = muted or nil }
    end
  end
  return { item_id = p.item_id, count = #events, truncated = #events >= limit or nil, events = events }
end

function commands.delete_midi_cc(p)
  local item = find_item(p.item_id)
  local take = midi_take(item)
  local base_qn = item_bounds_qn(item)
  return with_undo("delete MIDI CC", function()
    local _, _, count = reaper.MIDI_CountEvts(take)
    local removed = 0
    for i = count - 1, 0, -1 do
      local _, _, _, ppq, chanmsg, chan, msg2 = reaper.MIDI_GetCC(take, i)
      local qn = reaper.MIDI_GetProjQNFromPPQPos(take, ppq) - base_qn
      if cc_matches(p, cc_kind(chanmsg), msg2, chan, qn) then
        reaper.MIDI_DeleteCC(take, i)
        removed = removed + 1
      end
    end
    reaper.MIDI_Sort(take)
    return { removed = removed }
  end)
end

-------------------------------------------------------------- routing

local SEND_MODES = { [0] = "post-fader", [1] = "pre-fx", [2] = "post-fx", [3] = "post-fx" }

local function channel_text(v)
  if v < 0 then return nil end
  local start, width = (v & 1023) + 1, v >> 10
  if width == 1 then return tostring(start) end
  local n = width == 0 and 2 or width * 2
  return start .. "-" .. (start + n - 1)
end

function commands.get_routing()
  local tracks = {}
  for i = 0, reaper.CountTracks(0) - 1 do
    local t = reaper.GetTrack(0, i)
    local parent = reaper.GetParentTrack(t)
    local entry = {
      number = i + 1,
      name = track_name(t),
      folder = ({ [1] = "starts a folder" })[int(reaper.GetMediaTrackInfo_Value(t, "I_FOLDERDEPTH"))] or nil,
      in_folder = parent and track_name(parent) or nil,
      to_master = reaper.GetMediaTrackInfo_Value(t, "B_MAINSEND") == 1,
      sends = {},
    }
    if parent and entry.to_master then entry.to_master, entry.to_parent_folder = nil, true end
    for s_i = 0, reaper.GetTrackNumSends(t, 0) - 1 do
      local dest = reaper.GetTrackSendInfo_Value(t, 0, s_i, "P_DESTTRACK")
      local src = int(reaper.GetTrackSendInfo_Value(t, 0, s_i, "I_SRCCHAN"))
      local dst = int(reaper.GetTrackSendInfo_Value(t, 0, s_i, "I_DSTCHAN"))
      local midi = int(reaper.GetTrackSendInfo_Value(t, 0, s_i, "I_MIDIFLAGS"))
      local send = {
        to = dest and track_name(dest) or "?",
        volume_db = amp_to_db(reaper.GetTrackSendInfo_Value(t, 0, s_i, "D_VOL")),
        pan = round(reaper.GetTrackSendInfo_Value(t, 0, s_i, "D_PAN"), 2),
        mute = reaper.GetTrackSendInfo_Value(t, 0, s_i, "B_MUTE") == 1 or nil,
        mode = SEND_MODES[int(reaper.GetTrackSendInfo_Value(t, 0, s_i, "I_SENDMODE"))] or "post-fader",
        audio = src >= 0 and (channel_text(src) .. " -> " .. channel_text(dst)) or nil,
        midi = (midi & 31) ~= 31 or nil,
      }
      if dst >= 0 and (dst & 1023) == 2 then send.note = "into channels 3-4: a sidechain input" end
      entry.sends[#entry.sends + 1] = send
    end
    if #entry.sends == 0 then entry.sends = nil end
    local hw = reaper.GetTrackNumSends(t, 1)
    if hw > 0 then entry.hardware_outputs = hw end
    tracks[#tracks + 1] = entry
  end
  return { tracks = tracks }
end

-- Puts tracks into a new folder (a summing group): the folder track sits above them
-- and they play through it.
function commands.create_folder(p)
  local members = {}
  for _, ref in ipairs(p.tracks or {}) do members[#members + 1] = get_track(ref) end
  if #members == 0 then fail("give the tracks to put in the folder") end
  local first = math.huge
  for _, t in ipairs(members) do first = math.min(first, int(reaper.GetMediaTrackInfo_Value(t, "IP_TRACKNUMBER")) - 1) end
  return with_undo("create folder " .. (p.name or ""), function()
    local was_selected = {}
    for i = 0, reaper.CountTracks(0) - 1 do
      local t = reaper.GetTrack(0, i)
      was_selected[t] = reaper.IsTrackSelected(t)
    end
    reaper.InsertTrackAtIndex(first, true)
    local folder = reaper.GetTrack(0, first)
    reaper.GetSetMediaTrackInfo_String(folder, "P_NAME", p.name or "Folder", true)
    if p.color then set_color(folder, p.color) end
    for t in pairs(was_selected) do reaper.SetTrackSelected(t, false) end
    reaper.SetTrackSelected(folder, false)
    for _, t in ipairs(members) do reaper.SetTrackSelected(t, true) end
    reaper.ReorderSelectedTracks(first + 1, 1)  -- 1: the track before becomes their folder
    for t, sel in pairs(was_selected) do reaper.SetTrackSelected(t, sel) end
    reaper.SetTrackSelected(folder, false)
    return { folder = track_summary(folder), members = #members }
  end)
end

----------------------------------------------------------- sampler kits

-- Loads one ReaSamplOmatic5000 per sample onto a track, each playing on one key.
function commands.build_sampler_kit(p)
  local t = get_track(p.track)
  local pads = p.pads or {}
  if #pads == 0 then fail("give at least one sample") end
  for _, pad in ipairs(pads) do
    if type(pad.path) ~= "string" or not reaper.file_exists(pad.path) then fail("can't find the sample " .. tostring(pad.path)) end
  end
  return with_undo("build sampler kit on " .. track_name(t), function()
    local loaded = {}
    for _, pad in ipairs(pads) do
      local fx = reaper.TrackFX_AddByName(t, "ReaSamplOmatic5000 (Cockos)", false, -1)
      if fx < 0 then fail("couldn't load ReaSamplOmatic5000") end
      reaper.TrackFX_SetNamedConfigParm(t, fx, "FILE0", pad.path)
      reaper.TrackFX_SetNamedConfigParm(t, fx, "DONE", "")
      reaper.TrackFX_SetParamNormalized(t, fx, 3, int(pad.note) / 127)  -- note range start
      reaper.TrackFX_SetParamNormalized(t, fx, 4, int(pad.note) / 127)  -- note range end
      if pad.name then reaper.TrackFX_SetNamedConfigParm(t, fx, "renamed_name", pad.name) end
      local _, start_name = reaper.TrackFX_GetFormattedParamValue(t, fx, 3)
      loaded[#loaded + 1] = { fx = fx + 1, note = int(pad.note), plays_on = start_name, sample = pad.path:match("[^\\/]+$") }
    end
    return { track = track_ref(t), pads = loaded }
  end)
end

-- Tests one plugin on a hidden temporary track after the end of the project:
-- an instrument plays the given notes, an effect processes the given audio file.
-- The track is rendered offline and deleted again, so the project is unchanged.
function commands.probe_plugin(p)
  if type(p.name) ~= "string" or p.name == "" then fail("probe_plugin needs a plugin name") end
  local name = resolve_plugin(p.name, p.kind == "instrument") or p.name
  local length = math.max(1, math.min(120, tonumber(p.length) or 10))
  local start_t = reaper.GetProjectLength(0) + 2
  local info, files = {}, nil
  with_undo("test plugin " .. p.name .. " (no change)", function()
    local count = reaper.CountTracks(0)
    reaper.InsertTrackAtIndex(count, false)
    local t = reaper.GetTrack(0, count)
    reaper.GetSetMediaTrackInfo_String(t, "P_NAME", "creaper plugin test", true)
    reaper.SetMediaTrackInfo_Value(t, "B_SHOWINTCP", 0)
    reaper.SetMediaTrackInfo_Value(t, "B_SHOWINMIXER", 0)
    local ok, err = pcall(function()
      local fx = reaper.TrackFX_AddByName(t, name, false, -1)
      if fx < 0 then fail("couldn't load '" .. p.name .. "'") end
      info.fx = fx_name(t, fx)
      local has_pdc, pdc = reaper.TrackFX_GetNamedConfigParm(t, fx, "pdc")
      info.reported_latency_samples = has_pdc and tonumber(pdc) or nil
      info.parameters = reaper.TrackFX_GetNumParams(t, fx)
      local _, ins, outs = reaper.TrackFX_GetIOSize(t, fx)
      info.inputs, info.outputs = ins, outs
      info.is_instrument = reaper.TrackFX_GetInstrument(t) == fx
      if p.kind == "instrument" then
        local item = reaper.CreateNewMIDIItemInProj(t, start_t, start_t + length, false)
        local take = reaper.GetActiveTake(item)
        for _, n in ipairs(p.notes or {}) do
          local s0 = reaper.MIDI_GetPPQPosFromProjTime(take, start_t + n.start)
          local s1 = reaper.MIDI_GetPPQPosFromProjTime(take, start_t + n.start + n.length)
          reaper.MIDI_InsertNote(take, false, false, s0, s1, int((n.channel or 1) - 1), int(n.pitch),
            int(n.velocity or 100), true)
        end
        reaper.MIDI_Sort(take)
      else
        if type(p.audio_file) ~= "string" or not reaper.file_exists(p.audio_file) then
          fail("the test signal file is missing")
        end
        local src = reaper.PCM_Source_CreateFromFile(p.audio_file)
        if not src then fail("couldn't read the test signal") end
        local item = reaper.AddMediaItemToTrack(t)
        local take = reaper.AddTakeToMediaItem(item)
        reaper.SetMediaItemTake_Source(take, src)
        local offset = math.max(0, tonumber(p.offset) or 0)
        reaper.SetMediaItemInfo_Value(item, "D_POSITION", start_t + offset)
        reaper.SetMediaItemInfo_Value(item, "D_LENGTH", math.max(0.1, length - offset))
        -- No fades: a default fade-in would erase the test signal's opening impulse.
        for _, k in ipairs({ "D_FADEINLEN", "D_FADEOUTLEN", "D_FADEINLEN_AUTO", "D_FADEOUTLEN_AUTO" }) do
          reaper.SetMediaItemInfo_Value(item, k, 0)
        end
      end
      files = render_range(t, false, start_t, start_t + length)
    end)
    reaper.DeleteTrack(t)
    if not ok then error(err, 0) end
  end)
  info.files = files
  info.sample_rate = project_sample_rate()
  return info
end

------------------------------------------------------------ automation

local SHAPES = { linear = 0, square = 1, smooth = 2, fast_start = 3, fast_end = 4, bezier = 5 }
local SHAPE_NAMES = { [0] = "linear", "square", "smooth", "fast_start", "fast_end", "bezier" }
-- REAPER stores pan envelopes inverted relative to the track's pan (see tests).
local PAN_ENV_SIGN = -1
local TRACK_ENVELOPES = {
  volume = { chunk = "<VOLENV2", name = "Volume", action = 40406 }, -- Track: Toggle track volume envelope visible
  pan = { chunk = "<PANENV2", name = "Pan", action = 40407 },       -- Track: Toggle track pan envelope visible
}

local function with_only_track_selected(t, fn)
  local selected = {}
  for i = 0, reaper.CountTracks(0) - 1 do
    local tr = reaper.GetTrack(0, i)
    selected[tr] = reaper.IsTrackSelected(tr)
  end
  reaper.SetOnlyTrackSelected(t)
  local ok, err = pcall(fn)
  for tr, was in pairs(selected) do reaper.SetTrackSelected(tr, was) end
  if not ok then error(err, 0) end
end

local function track_envelope(t, kind, create)
  local spec = TRACK_ENVELOPES[kind]
  local env = reaper.GetTrackEnvelopeByChunkName(t, spec.chunk) or reaper.GetTrackEnvelopeByName(t, spec.name)
  if not env and create then
    with_only_track_selected(t, function() reaper.Main_OnCommand(spec.action, 0) end)
    env = reaper.GetTrackEnvelopeByChunkName(t, spec.chunk) or reaper.GetTrackEnvelopeByName(t, spec.name)
  end
  return env
end

-- Envelopes only play back while active; show them too, so the user sees the change.
local function activate_envelope(env)
  local ok, chunk = reaper.GetEnvelopeStateChunk(env, "", false)
  if not ok then return end
  local changed = chunk:gsub("\nACT 0", "\nACT 1"):gsub("\nVIS 0", "\nVIS 1")
  if changed ~= chunk then reaper.SetEnvelopeStateChunk(env, changed, false) end
end

-- target: { kind = "volume" | "pan" | "fx", fx = ..., parameter = ... }
local function automation_target(t, target, create)
  local kind = target and target.kind
  if kind == "volume" or kind == "pan" then
    return track_envelope(t, kind, create), kind
  elseif kind == "fx" then
    local fx = get_fx(t, target.fx)
    local param = find_param(t, fx, target.parameter)
    return reaper.GetFXEnvelope(t, fx, param, create), kind, fx, param
  end
  fail("the automation target must be volume, pan or an FX parameter")
end

local function point_time(pt)
  if pt.bar then return qn_to_time(bar_to_qn(pt.bar, pt.beat)) end
  if pt.qn then return qn_to_time(pt.qn) end
  if pt.seconds then return pt.seconds end
  fail("each automation point needs a bar (and optional beat), qn or seconds")
end

-- FX envelopes use the parameter's own range; for most plugins that's 0-1.
local function fx_range(t, fx, param)
  local _, minv, maxv = reaper.TrackFX_GetParam(t, fx, param)
  if not minv or not maxv or maxv <= minv then return 0, 1 end
  return minv, maxv
end

local function envelope_value(t, env, kind, fx, param, pt, cache)
  if kind == "volume" then
    local db = pt.db or pt.value
    if not db then fail("volume points need a db value") end
    local amp = db <= -150 and 0 or db_to_amp(db)
    return reaper.ScaleToEnvelopeMode(reaper.GetEnvelopeScalingMode(env), amp)
  elseif kind == "pan" then
    return math.max(-1, math.min(1, pt.pan or pt.value or 0)) * PAN_ENV_SIGN
  end
  local norm = pt.value
  if norm == nil then
    local key = pt.display_text and ("t:" .. pt.display_text) or ("v:" .. tostring(pt.display_value))
    norm = cache[key]
    if norm == nil then
      local original = reaper.TrackFX_GetParamNormalized(t, fx, param)
      if pt.display_text then
        norm = solve_display_text(t, fx, param, tostring(pt.display_text))
      elseif pt.display_value ~= nil then
        norm = solve_display_value(t, fx, param, pt.display_value)
      else
        fail("plugin automation points need value (0-1), display_value or display_text")
      end
      reaper.TrackFX_SetParamNormalized(t, fx, param, original)
      cache[key] = norm
    end
  end
  local minv, maxv = fx_range(t, fx, param)
  return minv + math.max(0, math.min(1, norm)) * (maxv - minv)
end

local function describe_point(t, env, kind, fx, param, time, value, shape)
  local pt = { position = time_to_pos(time), shape = SHAPE_NAMES[int(shape)] }
  if kind == "volume" then
    pt.db = amp_to_db(reaper.ScaleFromEnvelopeMode(reaper.GetEnvelopeScalingMode(env), value))
  elseif kind == "pan" then
    pt.pan = round(value * PAN_ENV_SIGN, 3)
  else
    local minv, maxv = fx_range(t, fx, param)
    local norm = (value - minv) / (maxv - minv)
    pt.value = round(norm, 4)
    local ok, display = reaper.TrackFX_FormatParamValueNormalized(t, fx, param, norm, "")
    if ok and display ~= "" then pt.display = display end
  end
  return pt
end

local function envelope_label(t, env)
  local _, name = reaper.GetEnvelopeName(env)
  return name
end

function commands.write_automation(p)
  local t = get_track(p.track)
  local default_shape = SHAPES[p.shape or "linear"]
  if not default_shape then fail("shape must be linear, smooth, square, fast_start, fast_end or bezier") end
  return with_undo("automate " .. track_name(t), function()
    local env, kind, fx, param = automation_target(t, p.target, true)
    if not env then fail("REAPER couldn't create that envelope") end
    local cache, points = {}, {}
    for _, pt in ipairs(p.points or {}) do
      local shape = pt.shape and SHAPES[pt.shape] or default_shape
      points[#points + 1] = { time = point_time(pt), value = envelope_value(t, env, kind, fx, param, pt, cache), shape = shape }
    end
    if #points == 0 then fail("give at least one automation point") end
    table.sort(points, function(a, b) return a.time < b.time end)
    if p.replace ~= false then
      reaper.DeleteEnvelopePointRange(env, points[1].time - 1e-6, points[#points].time + 1e-6)
    end
    for _, pt in ipairs(points) do reaper.InsertEnvelopePoint(env, pt.time, pt.value, pt.shape, 0, false, true) end
    reaper.Envelope_SortPoints(env)
    activate_envelope(env)
    return {
      envelope = envelope_label(t, env), track = track_ref(t), points_written = #points,
      total_points = reaper.CountEnvelopePoints(env),
      from = describe_point(t, env, kind, fx, param, points[1].time, points[1].value, points[1].shape),
      to = describe_point(t, env, kind, fx, param, points[#points].time, points[#points].value, points[#points].shape),
    }
  end)
end

function commands.read_automation(p)
  local t = get_track(p.track)
  if not p.target then
    local list = {}
    for i = 0, reaper.CountTrackEnvelopes(t) - 1 do
      local env = reaper.GetTrackEnvelope(t, i)
      local count = reaper.CountEnvelopePoints(env)
      if count > 0 then list[#list + 1] = { envelope = envelope_label(t, env), points = count } end
    end
    return { track = track_ref(t), envelopes = list }
  end
  local env, kind, fx, param = automation_target(t, p.target, false)
  if not env then return { track = track_ref(t), points = {}, note = "there's no automation for that yet" } end
  local count, points = reaper.CountEnvelopePoints(env), {}
  for i = 0, math.min(count, p.limit or 500) - 1 do
    local _, time, value, shape = reaper.GetEnvelopePoint(env, i)
    points[#points + 1] = describe_point(t, env, kind, fx, param, time, value, shape)
  end
  return { envelope = envelope_label(t, env), track = track_ref(t), point_count = count, points = points }
end

function commands.clear_automation(p)
  local t = get_track(p.track)
  local env = automation_target(t, p.target, false)
  if not env then fail("there's no automation for that") end
  local start_qn, end_qn = resolve_qn(p, "start"), resolve_qn(p, "end")
  return with_undo("clear automation on " .. track_name(t), function()
    local from = start_qn and qn_to_time(start_qn) or -1
    local to = end_qn and qn_to_time(end_qn) or (reaper.GetProjectLength(0) + 3600)
    reaper.DeleteEnvelopePointRange(env, from - 1e-6, to + 1e-6)
    reaper.Envelope_SortPoints(env)
    return { envelope = envelope_label(t, env), remaining_points = reaper.CountEnvelopePoints(env) }
  end)
end

------------------------------------------------------------ clip editing

function commands.edit_item(p)
  local item = find_item(p.item_id)
  return with_undo("edit item", function()
    if p.track then
      local t = get_track(p.track)
      if t == reaper.GetMasterTrack(0) then fail("items can't go on the master track") end
      reaper.MoveMediaItemToTrack(item, t)
    end
    local take = reaper.GetActiveTake(item)
    local is_midi = take and reaper.TakeIsMIDI(take)
    local pos = reaper.GetMediaItemInfo_Value(item, "D_POSITION")

    if p.trim_start_seconds and p.trim_start_seconds ~= 0 then
      -- Shorten (or extend) from the left while the content stays where it is.
      local d = p.trim_start_seconds
      local len = reaper.GetMediaItemInfo_Value(item, "D_LENGTH")
      if d >= len then fail("that would trim away the whole item") end
      pos = pos + d
      reaper.SetMediaItemInfo_Value(item, "D_POSITION", pos)
      reaper.SetMediaItemInfo_Value(item, "D_LENGTH", len - d)
      if take then
        local rate = reaper.GetMediaItemTakeInfo_Value(take, "D_PLAYRATE")
        reaper.SetMediaItemTakeInfo_Value(take, "D_STARTOFFS",
          reaper.GetMediaItemTakeInfo_Value(take, "D_STARTOFFS") + d * rate)
      end
    end

    local start_qn = resolve_qn(p, "start")
    if start_qn then
      pos = qn_to_time(start_qn)
      reaper.SetMediaItemInfo_Value(item, "D_POSITION", pos)
    end

    local new_end
    local pos_qn = time_to_qn(pos)
    if p.length_bars then new_end = qn_to_time(pos_qn + p.length_bars * bar_length_qn_at(pos_qn))
    elseif p.length_qn then new_end = qn_to_time(pos_qn + p.length_qn)
    elseif p.length_seconds then new_end = pos + p.length_seconds end
    if new_end then
      if new_end <= pos then fail("the length must be positive") end
      if is_midi then
        reaper.MIDI_SetItemExtents(item, pos_qn, time_to_qn(new_end))
      else
        reaper.SetMediaItemInfo_Value(item, "D_LENGTH", new_end - pos)
      end
    end

    if p.fade_in_seconds then reaper.SetMediaItemInfo_Value(item, "D_FADEINLEN", math.max(0, p.fade_in_seconds)) end
    if p.fade_out_seconds then reaper.SetMediaItemInfo_Value(item, "D_FADEOUTLEN", math.max(0, p.fade_out_seconds)) end
    if p.volume_db then reaper.SetMediaItemInfo_Value(item, "D_VOL", db_to_amp(p.volume_db)) end
    if p.mute ~= nil then reaper.SetMediaItemInfo_Value(item, "B_MUTE", p.mute and 1 or 0) end
    if p.loop ~= nil then reaper.SetMediaItemInfo_Value(item, "B_LOOPSRC", p.loop and 1 or 0) end
    if p.color then
      local r, g, b = tostring(p.color):match("^#?(%x%x)(%x%x)(%x%x)$")
      if not r then fail("colors look like #RRGGBB") end
      reaper.SetMediaItemInfo_Value(item, "I_CUSTOMCOLOR",
        reaper.ColorToNative(tonumber(r, 16), tonumber(g, 16), tonumber(b, 16)) | 0x1000000)
    end
    if take then
      if p.name then reaper.GetSetMediaItemTakeInfo_String(take, "P_NAME", p.name, true) end
      if p.pitch_semitones then reaper.SetMediaItemTakeInfo_Value(take, "D_PITCH", p.pitch_semitones) end
      if p.playrate then
        if p.playrate <= 0 then fail("playrate must be positive") end
        reaper.SetMediaItemTakeInfo_Value(take, "D_PLAYRATE", p.playrate)
      end
      if p.preserve_pitch ~= nil then reaper.SetMediaItemTakeInfo_Value(take, "B_PPITCH", p.preserve_pitch and 1 or 0) end
    end
    reaper.UpdateItemInProject(item)
    local info = item_info(item)
    info.fade_in_seconds = round(reaper.GetMediaItemInfo_Value(item, "D_FADEINLEN"), 3)
    info.fade_out_seconds = round(reaper.GetMediaItemInfo_Value(item, "D_FADEOUTLEN"), 3)
    info.volume_db = amp_to_db(reaper.GetMediaItemInfo_Value(item, "D_VOL"))
    if take and not is_midi then
      info.pitch_semitones = round(reaper.GetMediaItemTakeInfo_Value(take, "D_PITCH"), 2)
      info.playrate = round(reaper.GetMediaItemTakeInfo_Value(take, "D_PLAYRATE"), 4)
    end
    return info
  end)
end

function commands.split_item(p)
  local item = find_item(p.item_id)
  local at_qn = resolve_qn(p, "at") or fail("give where to split (at_bar, at_beat)")
  local at = qn_to_time(at_qn)
  local pos = reaper.GetMediaItemInfo_Value(item, "D_POSITION")
  local len = reaper.GetMediaItemInfo_Value(item, "D_LENGTH")
  if at <= pos + 1e-6 or at >= pos + len - 1e-6 then
    local s, e = time_to_pos(pos), time_to_pos(pos + len)
    fail(string.format("that point isn't inside the item (it runs from bar %d beat %s to bar %d beat %s)",
      s.bar, s.beat, e.bar, e.beat))
  end
  return with_undo("split item", function()
    local right = reaper.SplitMediaItem(item, at)
    if not right then fail("REAPER couldn't split the item there") end
    return { left = item_info(item), right = item_info(right) }
  end)
end

function commands.duplicate_item(p)
  local item = find_item(p.item_id)
  local track = reaper.GetMediaItem_Track(item)
  local pos = reaper.GetMediaItemInfo_Value(item, "D_POSITION")
  local len = reaper.GetMediaItemInfo_Value(item, "D_LENGTH")
  local count = math.max(1, math.min(int(p.count or 1), 256))
  local _, chunk = reaper.GetItemStateChunk(item, "", false)
  -- Without their GUIDs, REAPER gives the copies new ones.
  chunk = chunk:gsub("\n%s*IGUID [^\n]*", ""):gsub("\n%s*GUID [^\n]*", "")
  local start_qn = resolve_qn(p, "start")
  return with_undo("duplicate item", function()
    local copies, next_qn = {}, start_qn or time_to_qn(pos + len)
    local item_qn = time_to_qn(pos + len) - time_to_qn(pos)
    for _ = 1, count do
      local copy = reaper.AddMediaItemToTrack(track)
      reaper.SetItemStateChunk(copy, chunk, false)
      reaper.SetMediaItemInfo_Value(copy, "D_POSITION", qn_to_time(next_qn))
      copies[#copies + 1] = item_info(copy)
      next_qn = next_qn + item_qn
    end
    reaper.UpdateArrange()
    return { copies = copies }
  end)
end

function commands.delete_item(p)
  local item = find_item(p.item_id)
  local info = item_info(item)
  with_undo("delete item", function() reaper.DeleteTrackMediaItem(reaper.GetMediaItem_Track(item), item) end)
  return { deleted = info }
end

local AUDIO_EXTENSIONS = { wav = true, aif = true, aiff = true, flac = true, mp3 = true, ogg = true,
                           opus = true, wv = true, m4a = true, mid = true, midi = true }

function commands.insert_audio_file(p)
  local path = tostring(p.path or "")
  local ext = (path:match("%.([%w]+)$") or ""):lower()
  if not AUDIO_EXTENSIONS[ext] then fail("that isn't an audio or MIDI file REAPER can import: " .. path) end
  if not reaper.file_exists(path) then fail("there's no file at " .. path) end
  local t = get_track(p.track)
  if t == reaper.GetMasterTrack(0) then fail("items can't go on the master track") end
  local start_qn = resolve_qn(p, "start", time_to_qn(reaper.GetCursorPosition()))
  return with_undo("insert " .. (path:match("[^\\/]+$") or path), function()
    local cursor = reaper.GetCursorPosition()
    local selected_items = {}
    for i = 0, reaper.CountSelectedMediaItems(0) - 1 do selected_items[#selected_items + 1] = reaper.GetSelectedMediaItem(0, i) end
    local inserted
    with_only_track_selected(t, function()
      reaper.SelectAllMediaItems(0, false)
      reaper.SetEditCurPos(qn_to_time(start_qn), false, false)
      reaper.InsertMedia(path, 0) -- 0 = add to the selected track
      inserted = reaper.GetSelectedMediaItem(0, 0)
    end)
    reaper.SelectAllMediaItems(0, false)
    for _, it in ipairs(selected_items) do reaper.SetMediaItemSelected(it, true) end
    reaper.SetEditCurPos(cursor, false, false)
    if not inserted then fail("REAPER couldn't import " .. path) end
    return item_info(inserted)
  end)
end

------------------------------------------------------------ routing jobs

local function find_send(src, dest)
  local guid = reaper.GetTrackGUID(dest)
  for i = 0, reaper.GetTrackNumSends(src, 0) - 1 do
    local other = reaper.GetTrackSendInfo_Value(src, 0, i, "P_DESTTRACK")
    if other and reaper.GetTrackGUID(other) == guid then return i end
  end
end

-- Sends `source` to channels 3/4 of `target`, where a compressor listens to it.
function commands.setup_sidechain(p)
  local src, dest = get_track(p.source), get_track(p.target)
  if src == dest then fail("a track can't sidechain itself") end
  local compressor = p.compressor and (resolve_plugin(p.compressor) or p.compressor)
  return with_undo("sidechain " .. track_name(src) .. " -> " .. track_name(dest), function()
    -- Instruments leak a trigger arriving on channels 3/4 into their output (tested:
    -- ReaSynth and Arturia synths), so the target would play the kick. Duck an
    -- instrument track on a bus after it instead; its own effects stay where they are.
    local ducking_bus
    if reaper.TrackFX_GetInstrument(dest) >= 0 and not p.fx then
      local bus_name = track_name(dest) .. " Duck"
      for i = 0, reaper.GetTrackNumSends(dest, 0) - 1 do
        local other = reaper.GetTrackSendInfo_Value(dest, 0, i, "P_DESTTRACK")
        if other and track_name(other) == bus_name then ducking_bus = other break end
      end
      if not ducking_bus then
        local number = int(reaper.GetMediaTrackInfo_Value(dest, "IP_TRACKNUMBER"))
        -- After the track; before it if it's a folder (a child would feed back into it).
        local index = reaper.GetMediaTrackInfo_Value(dest, "I_FOLDERDEPTH") == 1 and number - 1 or number
        reaper.InsertTrackAtIndex(index, true)
        ducking_bus = reaper.GetTrack(0, index)
        reaper.GetSetMediaTrackInfo_String(ducking_bus, "P_NAME", bus_name, true)
        local color = reaper.GetTrackColor(dest)
        if color ~= 0 then reaper.SetTrackColor(ducking_bus, color) end
        reaper.CreateTrackSend(dest, ducking_bus) -- post-fader
        reaper.SetMediaTrackInfo_Value(dest, "B_MAINSEND", 0)
      end
      dest = ducking_bus
    end
    local fx, added
    if p.fx then
      fx = get_fx(dest, p.fx)
    else
      if not compressor then
        for i = 0, reaper.TrackFX_GetCount(dest) - 1 do
          if fx_name(dest, i):find("ReaComp", 1, true) then fx = i break end
        end
      end
      if not fx then
        fx = reaper.TrackFX_AddByName(dest, compressor or "ReaComp", false, -1)
        if fx < 0 then fail("couldn't find a compressor named '" .. tostring(compressor) .. "'") end
        added = true
      end
    end
    if reaper.GetMediaTrackInfo_Value(dest, "I_NCHAN") < 4 then reaper.SetMediaTrackInfo_Value(dest, "I_NCHAN", 4) end
    -- Only channels 1/2 go on to the parent/master: the trigger on 3/4 must never be heard.
    reaper.SetMediaTrackInfo_Value(dest, "C_MAINSEND_NCH", 2)
    local send = find_send(src, dest) or reaper.CreateTrackSend(src, dest)
    reaper.SetTrackSendInfo_Value(src, 0, send, "I_SRCCHAN", 0)
    reaper.SetTrackSendInfo_Value(src, 0, send, "I_DSTCHAN", 2)  -- into channels 3/4
    reaper.SetTrackSendInfo_Value(src, 0, send, "I_SENDMODE", 3) -- post-FX, before the source's fader
    reaper.SetTrackSendInfo_Value(src, 0, send, "D_VOL", 1)

    -- Feed the compressor's sidechain inputs (pins 3/4) from channels 3/4.
    local _, inputs = reaper.TrackFX_GetIOSize(dest, fx)
    if inputs and inputs >= 4 then
      reaper.TrackFX_SetPinMappings(dest, fx, 0, 2, 4, 0)
      reaper.TrackFX_SetPinMappings(dest, fx, 0, 3, 8, 0)
    end

    local name = fx_name(dest, fx)
    local switched = {}
    if name:find("ReaComp", 1, true) then
      -- ReaComp's detector input channel ("SignIn"): 2 = channels 3/4.
      local param = find_param(dest, fx, "SignIn")
      local value = solve_display_value(dest, fx, param, 2)
      reaper.TrackFX_SetParamNormalized(dest, fx, param, value)
      switched[#switched + 1] = "detector input: channels 3/4"
      if added then
        for _, change in ipairs({
          { parameter = "Ratio", display_value = 4 },
          { parameter = "Attack", display_value = 1 },
          { parameter = "Release", display_value = 120 },
        }) do pcall(apply_param_change, dest, fx, change) end
      end
    else
      -- Third-party compressors have their own sidechain switch. Leave alone the
      -- controls that monitor or filter the sidechain ("Sidechain Listen" would
      -- replace the output with the trigger signal).
      for i = 0, reaper.TrackFX_GetNumParams(dest, fx) - 1 do
        local _, pname = reaper.TrackFX_GetParamName(dest, fx, i, "")
        local lower = pname:lower()
        local is_monitor = lower:find("listen") or lower:find("monitor") or lower:find("solo")
          or lower:find("audition") or lower:find("preview") or lower:find("eq") or lower:find("filter")
          or lower:find("gain") or lower:find("time") or lower:find("detection")
        if not is_monitor and (lower:find("sidechain") or lower:find("side chain") or lower:find("sc source")
            or lower:find("external") or lower:find("key input")) then
          for _, wanted in ipairs({ "External", "Ext", "On", "Sidechain" }) do
            local ok = pcall(function()
              reaper.TrackFX_SetParamNormalized(dest, fx, i, solve_display_text(dest, fx, i, wanted))
            end)
            if ok then switched[#switched + 1] = pname .. ": " .. wanted break end
          end
        end
      end
    end
    return {
      source = track_ref(src), target = track_ref(dest), compressor = name, fx_index = fx + 1,
      added_compressor = added or nil, is_reacomp = name:find("ReaComp", 1, true) ~= nil,
      ducking_bus = ducking_bus and track_ref(ducking_bus) or nil,
      switched = switched,
      note = #switched == 0 and "turn on the compressor's sidechain / external input in its window" or nil,
    }
  end)
end

-- A bus track the given tracks send to (post-fader). By default they stop
-- sending to the master directly; keep_main_send keeps both (parallel processing).
function commands.create_bus(p)
  local sources = {}
  for _, ref in ipairs(p.tracks or {}) do
    local t = get_track(ref)
    if t == reaper.GetMasterTrack(0) then fail("the master track can't feed a bus") end
    sources[#sources + 1] = t
  end
  if #sources == 0 then fail("give the tracks that should feed the bus") end
  local plugins = {}
  for _, name in ipairs(p.fx or {}) do plugins[#plugins + 1] = resolve_plugin(name, false) or name end
  return with_undo("create bus " .. p.name, function()
    local last = 0
    for _, t in ipairs(sources) do last = math.max(last, int(reaper.GetMediaTrackInfo_Value(t, "IP_TRACKNUMBER"))) end
    reaper.InsertTrackAtIndex(last, true)
    local bus = reaper.GetTrack(0, last)
    reaper.GetSetMediaTrackInfo_String(bus, "P_NAME", p.name, true)
    if p.color then set_color(bus, p.color) end
    for _, t in ipairs(sources) do
      local send = find_send(t, bus) or reaper.CreateTrackSend(t, bus)
      reaper.SetTrackSendInfo_Value(t, 0, send, "I_SENDMODE", p.pre_fader and 3 or 0)
      if not p.keep_main_send then reaper.SetMediaTrackInfo_Value(t, "B_MAINSEND", 0) end
    end
    local added = {}
    for _, name in ipairs(plugins) do
      local fx = reaper.TrackFX_AddByName(bus, name, false, -1)
      if fx >= 0 then added[#added + 1] = { index = fx + 1, name = fx_name(bus, fx) } end
    end
    local refs = {}
    for _, t in ipairs(sources) do refs[#refs + 1] = track_ref(t) end
    return { bus = track_summary(bus), sources = refs, fx = added }
  end)
end

---------------------------------------------------------------- the loop

local function handle(raw)
  local ok, req = pcall(json.decode, raw)
  if not ok or type(req) ~= "table" then
    return { ok = false, error = "bad request: " .. tostring(req) }
  end
  local fn = commands[req.cmd]
  if not fn then
    return { id = req.id, ok = false,
             error = "this bridge (v" .. BRIDGE_VERSION .. ") doesn't know '" .. tostring(req.cmd) .. "'; update creaper_bridge.lua" }
  end
  local ok2, result = xpcall(fn, function(e)
    if type(e) == "table" then return e end
    return { message = tostring(e), traceback = debug.traceback("", 2) }
  end, req.params or {})
  if ok2 then return { id = req.id, ok = true, result = result } end
  return { id = req.id, ok = false, error = result.message, traceback = result.traceback }
end

reaper.RecursiveCreateDirectory(BRIDGE_DIR, 0)
math.randomseed(os.time())
local INSTANCE = string.format("%d%04d", os.time(), math.random(0, 9999))
local CLAIMED_PATH = REQUEST_PATH .. "." .. INSTANCE

-- Replaces a file atomically (write a temp file, rename it over). On Windows
-- the rename fails while another program has the file open for a moment (the
-- server reads the heartbeat often), so retry, then fall back to writing in
-- place. Returns false instead of raising: a missed write must never stop the bridge.
local function write_file(path, text)
  local tmp = path .. "." .. INSTANCE .. ".tmp"
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
local last_heartbeat = 0

-- Only one bridge may answer requests. The newest one to start takes over, so
-- running an updated copy replaces the old one without restarting REAPER; the
-- old one notices it no longer owns the bridge and exits.
local function owns_bridge() return reaper.GetExtState("creaper", "owner") == INSTANCE end
local previous_beat = tonumber(reaper.GetExtState("creaper", "heartbeat"))
local taking_over = previous_beat and reaper.time_precise() - previous_beat < 2
reaper.SetExtState("creaper", "owner", INSTANCE, false)
-- Give a bridge that's still running time to see the handover before we claim requests.
local claim_after = reaper.time_precise() + (taking_over and 0.5 or 0)
reaper.RecursiveCreateDirectory(REQUESTS_DIR, 0)
reaper.RecursiveCreateDirectory(RESPONSES_DIR, 0)
if not taking_over then
  -- Leftovers from a previous session: requests nobody is waiting for any more,
  -- answers nobody collected.
  os.remove(REQUEST_PATH)
  os.remove(RESPONSE_PATH)
  for _, dir in ipairs({ REQUESTS_DIR, RESPONSES_DIR }) do
    reaper.EnumerateFiles(dir, -1)
    local names, i = {}, 0
    while true do
      local name = reaper.EnumerateFiles(dir, i)
      if not name then break end
      names[#names + 1] = name
      i = i + 1
    end
    for _, name in ipairs(names) do os.remove(join(dir, name)) end
  end
end

local _, _, section_id, command_id = reaper.get_action_context()
if command_id and command_id > 0 then
  reaper.SetToggleCommandState(section_id, command_id, 1)
  reaper.RefreshToolbar2(section_id, command_id)
end

-- Put the chat panel in the action list, so it can go on a toolbar or a shortcut.
if reaper.file_exists(SCRIPT_DIR .. "creaper_chat.lua") then
  reaper.AddRemoveReaScript(true, 0, SCRIPT_DIR .. "creaper_chat.lua", true)
end

-- nil if the file is locked for a moment (e.g. a virus scanner checking it).
local function read_claimed(path)
  local f = io.open(path, "rb")
  if not f then return nil end
  local raw = f:read("a")
  f:close()
  os.remove(path)
  return raw
end

-- Answers that couldn't be written yet (another program holding the folder's
-- files for a moment); retried every tick for up to a minute.
local unsent = {}

local function answer(raw, response_path, id)
  local response = handle(raw)
  response.id = response.id or id
  local ok, encoded = pcall(json.encode, response)
  if not ok then
    encoded = json.encode({ id = response.id, ok = false, error = "couldn't encode the result: " .. tostring(encoded) })
  end
  if not write_file(response_path, encoded) then
    unsent[#unsent + 1] = { path = response_path, text = encoded, since = reaper.time_precise() }
  end
end

local function retry_unsent()
  for i = #unsent, 1, -1 do
    local u = unsent[i]
    if write_file(u.path, u.text) then
      table.remove(unsent, i)
    elseif reaper.time_precise() - u.since > 60 then
      table.remove(unsent, i)
      reaper.ShowConsoleMsg("creaper: gave up writing a response to " .. u.path .. "\n")
    end
  end
end

-- While recording, the heartbeat says whether stopping will bring up REAPER's
-- save/delete prompt: if the heartbeat then goes quiet, clients know REAPER is
-- waiting for the user rather than gone, and wait too.
local function write_heartbeat(now)
  last_heartbeat = now
  local recording = reaper.GetPlayState() & 4 ~= 0
  write_file(HEARTBEAT_PATH, json.encode({
    bridge_version = BRIDGE_VERSION, protocol = PROTOCOL, time = os.time(),
    reaper_version = reaper.GetAppVersion(),
    recording = recording or nil, stop_prompt = recording and stop_prompt_on() or nil,
  }))
end

local function step()
  local now = reaper.time_precise()
  reaper.SetExtState("creaper", "heartbeat", tostring(now), false)
  if beat_now or now - last_heartbeat >= 1 then
    beat_now = nil
    write_heartbeat(now)
  end

  if stop_at then
    if reaper.GetPlayState() & 1 == 0 then
      stop_at = nil
    elseif reaper.GetPlayPosition() >= stop_at then
      stop_at = nil
      write_heartbeat(now) -- fresh, in case stopping opens the prompt and blocks us
      reaper.OnStopButton()
    end
  end

  if now < claim_after then return end
  retry_unsent()

  -- Protocol 2: every request has its own file, so clients never overwrite each
  -- other. Renaming claims a request atomically.
  reaper.EnumerateFiles(REQUESTS_DIR, -1) -- refresh REAPER's cached listing
  local pending, i = {}, 0
  while #pending < 20 do
    local name = reaper.EnumerateFiles(REQUESTS_DIR, i)
    if not name then break end
    local id = name:match("^([%w_%-]+)%.json$")
    if id then pending[#pending + 1] = id end
    i = i + 1
  end
  for _, id in ipairs(pending) do
    local request = join(REQUESTS_DIR, id .. ".json")
    local claimed = join(REQUESTS_DIR, id .. "." .. INSTANCE .. ".claimed")
    if os.rename(request, claimed) then
      local raw = read_claimed(claimed)
      if raw then
        answer(raw, join(RESPONSES_DIR, id .. ".json"), id)
      else
        os.rename(claimed, request) -- couldn't read it yet: put it back for the next tick
      end
    end
  end

  -- Protocol 1 (creaper 0.1-0.4 servers): a single shared request file.
  if os.rename(REQUEST_PATH, CLAIMED_PATH) then
    local raw = read_claimed(CLAIMED_PATH)
    if raw then answer(raw, RESPONSE_PATH) else os.rename(CLAIMED_PATH, REQUEST_PATH) end
  end
end

local last_error
local function tick()
  if not owns_bridge() then return end -- a newer bridge took over; let this script end
  -- Whatever goes wrong in one tick, keep the bridge running; report each new error once.
  local ok, err = xpcall(step, debug.traceback)
  if not ok and err ~= last_error then
    last_error = err
    reaper.ShowConsoleMsg("creaper bridge error (still running): " .. tostring(err) .. "\n")
  end
  reaper.defer(tick)
end

reaper.atexit(function()
  if owns_bridge() then
    os.remove(HEARTBEAT_PATH)
    reaper.DeleteExtState("creaper", "heartbeat", false)
    reaper.DeleteExtState("creaper", "owner", false)
  end
  if command_id and command_id > 0 then
    reaper.SetToggleCommandState(section_id, command_id, 0)
    reaper.RefreshToolbar2(section_id, command_id)
  end
end)

tick()

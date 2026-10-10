-- @description creaper bridge: lets Claude work in REAPER through the creaper MCP server
-- @author nickcapron
-- @version 0.1.0
-- @link https://github.com/nickcapron/creaper
-- @about
--   Keep this script running while you use creaper. It watches a folder in
--   REAPER's resource path for requests from the creaper MCP server, runs them
--   with the ReaScript API and writes the answers back.
--
--   Every change it makes is a named undo point ("creaper: ..."), so Ctrl+Z
--   reverts anything Claude did.

local BRIDGE_VERSION = "0.1.0"
local PROTOCOL = 1

----------------------------------------------------------------------- JSON

local json = {}
do
  json.null = setmetatable({}, { __tostring = function() return "null" end })
  local OBJECT_MT = {}

  -- Mark a table as a JSON object, so an empty one encodes as {} not [].
  function json.object(t) return setmetatable(t or {}, OBJECT_MT) end

  local escapes = {
    ['"'] = '\\"', ['\\'] = '\\\\', ['\b'] = '\\b', ['\f'] = '\\f',
    ['\n'] = '\\n', ['\r'] = '\\r', ['\t'] = '\\t',
  }
  local function encode_string(s)
    return '"' .. (s:gsub('[%c"\\]', function(c)
      return escapes[c] or string.format("\\u%04x", c:byte())
    end)) .. '"'
  end

  local function array_length(t)
    if getmetatable(t) == OBJECT_MT then return nil end
    local n = 0
    for k in pairs(t) do
      if math.type(k) ~= "integer" or k < 1 then return nil end
      n = n + 1
    end
    for i = 1, n do if t[i] == nil then return nil end end
    return n
  end

  local function encode(v, out)
    local tv = type(v)
    if v == nil or v == json.null then
      out[#out + 1] = "null"
    elseif tv == "boolean" then
      out[#out + 1] = v and "true" or "false"
    elseif tv == "number" then
      if v ~= v or v == math.huge or v == -math.huge then
        out[#out + 1] = "null"
      elseif math.type(v) == "integer" then
        out[#out + 1] = string.format("%d", v)
      else
        out[#out + 1] = string.format("%.10g", v)
      end
    elseif tv == "string" then
      out[#out + 1] = encode_string(v)
    elseif tv == "table" then
      local n = array_length(v)
      if n then
        out[#out + 1] = "["
        for i = 1, n do
          if i > 1 then out[#out + 1] = "," end
          encode(v[i], out)
        end
        out[#out + 1] = "]"
      else
        out[#out + 1] = "{"
        local first = true
        for k, val in pairs(v) do
          if not first then out[#out + 1] = "," end
          first = false
          out[#out + 1] = encode_string(tostring(k))
          out[#out + 1] = ":"
          encode(val, out)
        end
        out[#out + 1] = "}"
      end
    else
      out[#out + 1] = encode_string(tostring(v))
    end
  end

  function json.encode(v)
    local out = {}
    encode(v, out)
    return table.concat(out)
  end

  local function decode_error(pos, msg)
    error(string.format("JSON error at character %d: %s", pos, msg), 0)
  end

  local function skip_ws(str, pos)
    return str:find("[^ \t\r\n]", pos) or #str + 1
  end

  local unescapes = {
    b = "\b", f = "\f", n = "\n", r = "\r", t = "\t", ['"'] = '"', ["\\"] = "\\", ["/"] = "/",
  }

  local function parse_string(str, pos)
    local buf, i = {}, pos + 1
    while true do
      local c = str:sub(i, i)
      if c == "" then decode_error(i, "unterminated string") end
      if c == '"' then return table.concat(buf), i + 1 end
      if c == "\\" then
        local e = str:sub(i + 1, i + 1)
        if unescapes[e] then
          buf[#buf + 1] = unescapes[e]
          i = i + 2
        elseif e == "u" then
          local cp = tonumber(str:sub(i + 2, i + 5), 16) or decode_error(i, "bad \\u escape")
          i = i + 6
          if cp >= 0xD800 and cp <= 0xDBFF and str:sub(i, i + 1) == "\\u" then
            local lo = tonumber(str:sub(i + 2, i + 5), 16)
            if lo and lo >= 0xDC00 and lo <= 0xDFFF then
              cp = 0x10000 + (cp - 0xD800) * 0x400 + (lo - 0xDC00)
              i = i + 6
            end
          end
          buf[#buf + 1] = utf8.char(cp)
        else
          decode_error(i, "bad escape")
        end
      else
        local j = str:find('["\\]', i) or decode_error(i, "unterminated string")
        buf[#buf + 1] = str:sub(i, j - 1)
        i = j
      end
    end
  end

  local parse
  parse = function(str, pos)
    pos = skip_ws(str, pos)
    local c = str:sub(pos, pos)
    if c == "{" then
      local obj = json.object()
      pos = skip_ws(str, pos + 1)
      if str:sub(pos, pos) == "}" then return obj, pos + 1 end
      while true do
        pos = skip_ws(str, pos)
        if str:sub(pos, pos) ~= '"' then decode_error(pos, "expected a key") end
        local key
        key, pos = parse_string(str, pos)
        pos = skip_ws(str, pos)
        if str:sub(pos, pos) ~= ":" then decode_error(pos, "expected ':'") end
        local val
        val, pos = parse(str, pos + 1)
        obj[key] = val
        pos = skip_ws(str, pos)
        local d = str:sub(pos, pos)
        if d == "}" then return obj, pos + 1 end
        if d ~= "," then decode_error(pos, "expected ',' or '}'") end
        pos = pos + 1
      end
    elseif c == "[" then
      local arr, n = {}, 0
      pos = skip_ws(str, pos + 1)
      if str:sub(pos, pos) == "]" then return arr, pos + 1 end
      while true do
        local val
        val, pos = parse(str, pos)
        n = n + 1
        arr[n] = val
        pos = skip_ws(str, pos)
        local d = str:sub(pos, pos)
        if d == "]" then return arr, pos + 1 end
        if d ~= "," then decode_error(pos, "expected ',' or ']'") end
        pos = pos + 1
      end
    elseif c == '"' then
      return parse_string(str, pos)
    elseif str:find("^true", pos) then
      return true, pos + 4
    elseif str:find("^false", pos) then
      return false, pos + 5
    elseif str:find("^null", pos) then
      return nil, pos + 4
    end
    local num_str = str:match("^-?%d+%.?%d*[eE]?[-+]?%d*", pos)
    local num = num_str and tonumber(num_str)
    if not num then decode_error(pos, "unexpected character '" .. c .. "'") end
    return num, pos + #num_str
  end

  function json.decode(str)
    local v, pos = parse(str, 1)
    if skip_ws(str, pos) <= #str then decode_error(pos, "unexpected trailing text") end
    return v
  end
end

---------------------------------------------------------------------- paths

local SEP = package.config:sub(1, 1)
local function join(...) return table.concat({ ... }, SEP) end

local BRIDGE_DIR = join(reaper.GetResourcePath(), "creaper")
local REQUEST_PATH = join(BRIDGE_DIR, "request.json")
local RESPONSE_PATH = join(BRIDGE_DIR, "response.json")
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

local function get_track(ref)
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
    name = name:lower()
    if name == wanted then return i end
    if not partial and name:find(wanted, 1, true) then partial = i end
  end
  if partial then return partial end
  fail("no parameter matching '" .. tostring(ref) .. "' (get_fx_parameters lists them)")
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

-- Finds the normalized value whose displayed value is `target`, assuming the
-- display is monotonic. Uses FormatParamValueNormalized when the plugin
-- supports it, otherwise sets the parameter and reads it back.
local function solve_display_value(t, fx, param, target)
  local function display_at(v)
    local ok, s = reaper.TrackFX_FormatParamValueNormalized(t, fx, param, v, "")
    if not ok or s == "" then
      reaper.TrackFX_SetParamNormalized(t, fx, param, v)
      _, s = reaper.TrackFX_GetFormattedParamValue(t, fx, param, "")
    end
    return parse_display_number(s)
  end
  local at_min, at_max = display_at(0), display_at(1)
  if not at_min or not at_max then
    fail("this parameter doesn't show a number; set 'value' (0 to 1) instead")
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

local function param_info(t, fx, i)
  local _, name = reaper.TrackFX_GetParamName(t, fx, i, "")
  local _, display = reaper.TrackFX_GetFormattedParamValue(t, fx, i, "")
  return {
    index = i + 1,
    name = name,
    value = round(reaper.TrackFX_GetParamNormalized(t, fx, i), 4),
    display = display,
  }
end

---------------------------------------------------------------- commands

local commands = {}
local stop_at -- playback stops when it passes this time (seconds)

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
  for i = 0, reaper.TrackFX_GetCount(t) - 1 do
    local _, preset = reaper.TrackFX_GetPreset(t, i, "")
    fx[#fx + 1] = {
      index = i + 1,
      name = fx_name(t, i),
      enabled = reaper.TrackFX_GetEnabled(t, i),
      offline = reaper.TrackFX_GetOffline(t, i) or nil,
      preset = preset ~= "" and preset or nil,
      parameter_count = reaper.TrackFX_GetNumParams(t, i),
    }
  end
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
  local words = {}
  for w in tostring(p.search or ""):lower():gmatch("%S+") do words[#words + 1] = w end
  local offset, limit = p.offset or 0, p.limit or 100
  local params, matched = {}, 0
  for i = 0, count - 1 do
    local _, name = reaper.TrackFX_GetParamName(t, fx, i, "")
    local lower, ok = name:lower(), true
    for _, w in ipairs(words) do
      if not lower:find(w, 1, true) then ok = false break end
    end
    if ok then
      matched = matched + 1
      if matched > offset and #params < limit then params[#params + 1] = param_info(t, fx, i) end
    end
  end
  return { fx = fx_name(t, fx), fx_index = fx + 1, parameter_count = count, matched = matched, parameters = params }
end

function commands.list_installed_fx(p)
  local words = {}
  for w in tostring(p.search or ""):lower():gmatch("%S+") do words[#words + 1] = w end
  local limit = p.limit or 50
  local matches, total, i = {}, 0, 0
  while true do
    local ok, name = reaper.EnumInstalledFX(i)
    if not ok then break end
    local lower, hit = name:lower(), true
    for _, w in ipairs(words) do
      if not lower:find(w, 1, true) then hit = false break end
    end
    if hit then
      total = total + 1
      if #matches < limit then matches[#matches + 1] = name end
    end
    i = i + 1
  end
  return { matches = matches, total_matches = total }
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
      local fx = reaper.TrackFX_AddByName(t, p.instrument, false, -1)
      if fx < 0 then
        result.warning = "couldn't find an instrument named '" .. p.instrument
          .. "'; the track was created without one (list_installed_fx can search)"
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
    return track_summary(t)
  end)
end

function commands.delete_track(p)
  local t = get_track(p.track)
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
  local index = with_undo("add " .. p.name .. " to " .. track_name(t), function()
    local instantiate = -1
    if p.position then instantiate = -1000 - math.max(0, int(p.position) - 1) end
    local i = reaper.TrackFX_AddByName(t, p.name, false, instantiate)
    if i < 0 then
      fail("couldn't find an installed FX named '" .. p.name .. "' (list_installed_fx can search)")
    end
    return i
  end)
  return {
    track = track_ref(t),
    fx_index = index + 1,
    name = fx_name(t, index),
    parameter_count = reaper.TrackFX_GetNumParams(t, index),
  }
end

function commands.set_fx_parameter(p)
  local t = get_track(p.track)
  local fx = get_fx(t, p.fx)
  local param = find_param(t, fx, p.parameter)
  if p.value == nil and p.display_value == nil then fail("give either value (0 to 1) or display_value") end
  return with_undo("set " .. fx_name(t, fx) .. " parameter", function()
    local value, clamped = p.value, false
    if value == nil then
      value, clamped = solve_display_value(t, fx, param, p.display_value)
    end
    reaper.TrackFX_SetParamNormalized(t, fx, param, math.max(0, math.min(1, value)))
    local info = param_info(t, fx, param)
    info.fx = fx_name(t, fx)
    if clamped then info.note = "the requested value is outside this parameter's range, so it was set to the limit" end
    return info
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
        result.warning = "no preset named '" .. p.preset .. "' was found"
      end
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
        take, false, n.muted or false,
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

function commands.run_action(p)
  local id = tonumber(p.command)
  if not id then id = reaper.NamedCommandLookup(tostring(p.command)) end
  if not id or id == 0 then fail("no action with id '" .. tostring(p.command) .. "'") end
  local name = reaper.kbd_getTextFromCmd(id, 0)
  reaper.Main_OnCommand(id, 0)
  return { ran = name ~= "" and name or tostring(p.command), command_id = id }
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

function commands.render_audio(p)
  local t = get_track(p.track or "master")
  local master = t == reaper.GetMasterTrack(0)
  local start_qn, end_qn = resolve_qn(p, "start"), resolve_qn(p, "end")
  local start_t = start_qn and qn_to_time(start_qn) or 0
  local end_t = end_qn and qn_to_time(end_qn) or reaper.GetProjectLength(0)
  if end_t <= start_t then fail("nothing to render: the range is empty (is the project empty?)") end
  if end_t - start_t > 1800 then fail("renders are limited to 30 minutes; pick a shorter range") end

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
      for tr in pairs(saved_selection) do reaper.SetTrackSelected(tr, tr == t) end
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
  return {
    files = files,
    track = track_ref(t),
    start = time_to_pos(start_t),
    ["end"] = time_to_pos(end_t),
  }
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

local function write_file(path, text)
  local tmp = path .. ".tmp"
  local f = assert(io.open(tmp, "wb"))
  f:write(text)
  f:close()
  os.remove(path)
  assert(os.rename(tmp, path))
end

reaper.RecursiveCreateDirectory(BRIDGE_DIR, 0)
math.randomseed(os.time())
local INSTANCE = string.format("%d%04d", os.time(), math.random(0, 9999))
local CLAIMED_PATH = REQUEST_PATH .. "." .. INSTANCE
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
if not taking_over then
  os.remove(REQUEST_PATH)
  os.remove(RESPONSE_PATH)
end

local _, _, section_id, command_id = reaper.get_action_context()
if command_id and command_id > 0 then
  reaper.SetToggleCommandState(section_id, command_id, 1)
  reaper.RefreshToolbar2(section_id, command_id)
end

local function tick()
  if not owns_bridge() then return end -- a newer bridge took over; let this script end
  local now = reaper.time_precise()
  reaper.SetExtState("creaper", "heartbeat", tostring(now), false)
  if now - last_heartbeat >= 1 then
    last_heartbeat = now
    write_file(HEARTBEAT_PATH, json.encode({
      bridge_version = BRIDGE_VERSION, protocol = PROTOCOL, time = os.time(),
      reaper_version = reaper.GetAppVersion(),
    }))
  end

  if stop_at then
    if reaper.GetPlayState() & 1 == 0 then
      stop_at = nil
    elseif reaper.GetPlayPosition() >= stop_at then
      reaper.OnStopButton()
      stop_at = nil
    end
  end

  -- Renaming claims the request atomically.
  if now >= claim_after and os.rename(REQUEST_PATH, CLAIMED_PATH) then
    local f = io.open(CLAIMED_PATH, "rb")
    local raw = f and f:read("a") or ""
    if f then f:close() end
    os.remove(CLAIMED_PATH)
    local response = handle(raw)
    local ok, encoded = pcall(json.encode, response)
    if not ok then
      encoded = json.encode({ id = response.id, ok = false, error = "couldn't encode the result: " .. tostring(encoded) })
    end
    write_file(RESPONSE_PATH, encoded)
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

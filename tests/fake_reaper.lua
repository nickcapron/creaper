-- A small fake of REAPER's ReaScript API for running creaper_bridge.lua in a plain Lua
-- runtime (tests/lua_harness.py). It holds only what the tested paths call. Anything else
-- raises, so a test can't pass on a function that isn't there.
--
-- Returns two tables: `reaper` (the API) and `F` (the fake's state and the helpers tests
-- use to set a scene and look at the result).

local reaper = {}
local F = {
  now = 1000.0,           -- time_precise()
  play_state = 0,         -- 0 stopped, 1 playing, 5 recording
  play_position = 0.0,
  cursor = 0.0,
  project_length = 0.0,
  resource_path = "",     -- set by the harness before the bridge loads
  ini_path = "",          -- reaper.ini; a file that isn't there means "enables unknown"
  config = { promptendrec = "1", audiocloseinactive = "1", defsavepath = "" },
  config_refused = false, -- set_config_var_string changes nothing
  ext = {},               -- ExtState: ext["section/key"] = { value, persist }
  tracks = {},
  audio = { running = true, can_open = true, inputs = 2, opened = 0, quit = 0 },
  midi_outputs = { [0] = "microKORG" },
  midi_inputs = { [0] = "microKORG" },
  action_names = {},      -- [id] = { name, named }
  actions = {},           -- every Main_OnCommand id, in order
  prefs = {},             -- every ViewPrefs page number, in order
  sent = {},              -- { device, bytes } per SendMIDIMessageToHardware
  media = {},             -- [path] = { notes = n, sysex = n, text = n }
  atexit = {},
  sysex_stuck = false,    -- MIDI_DeleteTextSysexEvt refuses
  raise_in = {},          -- [function name] = true: that API call raises (REAPER misbehaving)
  recorded_file = "take.wav",
}

-- Functions the bridge asks for before it uses them (they came with later REAPERs).
-- F.without(name) takes one away; reading it then gives nil, like in an older REAPER.
local OPTIONAL = { get_ini_file = true, set_config_var_string = true, ViewPrefs = true,
                   SendMIDIMessageToHardware = true, MIDI_GetRecentInputEvent = true,
                   ReverseNamedCommandLookup = true }

function F.without(name)
  assert(OPTIONAL[name], name .. " isn't optional in the bridge")
  rawset(reaper, name, nil)
end

local guids = 0
local function new_guid()
  guids = guids + 1
  return string.format("{%08X-0000-0000-0000-000000000000}", guids)
end

local TRACK_DEFAULTS = { I_RECARM = 0, I_RECMON = 0, I_RECMODE = 0, I_RECINPUT = -1, I_MIDIHWOUT = -1,
                         B_MUTE = 0, I_FOLDERDEPTH = 0 }
local ITEM_DEFAULTS = { D_POSITION = 0.0, D_LENGTH = 0.0, B_MUTE = 0 }

local master = { guid = "master", name = "MASTER", v = {}, ext = {}, items = {}, selected = false }

local function make_track(name)
  local v = {}
  for k, d in pairs(TRACK_DEFAULTS) do v[k] = d end
  return { guid = new_guid(), name = name or "", v = v, ext = {}, items = {}, selected = false }
end

local function make_take(midi)
  return { midi = midi and true or false, notes = {}, events = {}, v = { D_STARTOFFS = 0.0 }, name = "", file = "" }
end

local function make_item(track, pos, len, take)
  local item = { guid = new_guid(), track = track, v = { D_POSITION = pos, D_LENGTH = len, B_MUTE = 0 },
                 ext = {}, takes = { take }, selected = false }
  track.items[#track.items + 1] = item
  return item
end

local function index_of(list, x)
  for i, v in ipairs(list) do
    if v == x then return i end
  end
end

local function all_items()
  local out = {}
  for _, t in ipairs(F.tracks) do
    for _, item in ipairs(t.items) do out[#out + 1] = item end
  end
  return out
end

------------------------------------------------------------ helpers for tests

function F.new_track(name, values)
  local t = make_track(name)
  for k, v in pairs(values or {}) do t.v[k] = v end
  F.tracks[#F.tracks + 1] = t
  return t
end

function F.track(name)
  for _, t in ipairs(F.tracks) do
    if t.name == name then return t end
  end
end

-- A MIDI item with `sysex` SysEx messages, `text` text events and `notes` notes.
function F.new_midi_item(track, pos, len, counts)
  counts = counts or {}
  local take = make_take(true)
  for i = 1, counts.text or 0 do take.events[#take.events + 1] = { kind = 1, msg = "text " .. i } end
  for i = 1, counts.sysex or 0 do
    take.events[#take.events + 1] = { kind = -1, msg = string.char(0x42, 0x30, 0x58, i) }
  end
  for i = 1, counts.notes or 0 do take.notes[i] = { pitch = 59 + i } end
  return make_item(track, pos, len, take)
end

function F.new_audio_item(track, pos, len, file)
  local take = make_take(false)
  take.file = file or "old.wav"
  return make_item(track, pos, len, take)
end

function F.sysex_count(item)
  local n = 0
  for _, take in ipairs(item.takes) do
    for _, e in ipairs(take.events) do
      if e.kind == -1 then n = n + 1 end
    end
  end
  return n
end

function F.ext_value(section, key)
  local e = F.ext[section .. "/" .. key]
  return e and e[1] or ""
end

function F.run_atexit()
  for _, fn in ipairs(F.atexit) do fn() end
end

-------------------------------------------------------------- the script host

function reaper.GetResourcePath() return F.resource_path end
function reaper.get_ini_file() return F.ini_path end
function reaper.RecursiveCreateDirectory() return 1 end
function reaper.EnumerateFiles() return nil end
function reaper.file_exists(path)
  if F.media[path] then return true end
  local f = io.open(path, "rb")
  if f then f:close() end
  return f ~= nil
end
function reaper.get_action_context() return false, "creaper_bridge.lua", 0, 0, 0, 0, 0 end
function reaper.AddRemoveReaScript() return 0 end
function reaper.atexit(fn) F.atexit[#F.atexit + 1] = fn end
function reaper.defer() error("the bridge started its loop: the test hook didn't hold it", 2) end
function reaper.ShowConsoleMsg(text) F.console = (F.console or "") .. text end
function reaper.time_precise() return F.now end
function reaper.GetAppVersion() return "7.85/fake" end
function reaper.TrackFX_SetParamNormalized() return true end -- wrapped by the bridge when it loads

function reaper.GetExtState(section, key) return F.ext_value(section, key) end
function reaper.SetExtState(section, key, value, persist) F.ext[section .. "/" .. key] = { value, persist } end
function reaper.DeleteExtState(section, key) F.ext[section .. "/" .. key] = nil end

function reaper.get_config_var_string(name)
  local value = F.config[name]
  if value == nil then return false, "" end
  return true, value
end

function reaper.set_config_var_string(name, value)
  if F.config[name] == nil then error("fake reaper has no config variable " .. tostring(name), 2) end
  if not F.config_refused then F.config[name] = value end
  return true
end

function reaper.Undo_BeginBlock2() end
function reaper.Undo_EndBlock2() end
function reaper.PreventUIRefresh() end
function reaper.TrackList_AdjustWindows() end
function reaper.UpdateArrange() end

------------------------------------------------------------- audio and MIDI

function reaper.Audio_IsRunning()
  if F.audio.answer ~= nil then return F.audio.answer end -- a test pins the raw answer
  return F.audio.running and 1 or 0                       -- REAPER answers a number
end
function reaper.Audio_Init()
  F.audio.opened = F.audio.opened + 1
  if F.audio.can_open then F.audio.running = true end
end
function reaper.Audio_Quit()
  F.audio.quit = F.audio.quit + 1
  F.audio.running = false
end
function reaper.GetNumAudioInputs() return F.audio.running and F.audio.inputs or 0 end
function reaper.GetAudioDeviceInfo(key)
  local info = { MODE = "ASIO", IDENT_IN = "SSL 2+", IDENT_OUT = "SSL 2+", SRATE = "48000", BSIZE = "256" }
  if not F.audio.running or not info[key] then return false, "" end
  return true, info[key]
end

local function port_count(ports)
  local n = 0
  for i in pairs(ports) do n = math.max(n, i + 1) end
  return n
end
function reaper.GetNumMIDIOutputs() return port_count(F.midi_outputs) end
function reaper.GetNumMIDIInputs() return port_count(F.midi_inputs) end
function reaper.GetMIDIOutputName(i) return F.midi_outputs[i] ~= nil, F.midi_outputs[i] or "" end
function reaper.GetMIDIInputName(i) return F.midi_inputs[i] ~= nil, F.midi_inputs[i] or "" end
function reaper.SendMIDIMessageToHardware(device, bytes) F.sent[#F.sent + 1] = { device = device, bytes = bytes } end

------------------------------------------------------------------ transport

function reaper.GetPlayState() return F.play_state end
function reaper.GetPlayPosition() return F.play_position end
function reaper.GetCursorPosition() return F.cursor end
function reaper.SetEditCurPos(t) F.cursor = t end
function reaper.GetProjectLength() return F.project_length end

function reaper.ViewPrefs(page, name)
  assert(name == "", "a page name does nothing in REAPER 7.85: pages are opened by number")
  F.prefs[#F.prefs + 1] = page
end

function reaper.Main_OnCommand(id)
  F.actions[#F.actions + 1] = id
  if id == 1013 then -- Transport: Record
    F.play_state = 5
    F.recording_from = F.cursor
    F.play_position = F.cursor
  elseif id == 40131 then -- Take: Crop to active take in items
    for _, t in ipairs(F.tracks) do
      for _, item in ipairs(t.items) do
        if item.selected then
          item.takes = { item.takes[item.active or 1] }
          item.active = nil
        end
      end
    end
  end
end

-- Stopping a recording leaves a new audio item on every armed track, as REAPER does.
function reaper.OnStopButton()
  if F.play_state & 4 ~= 0 then
    for _, t in ipairs(F.tracks) do
      if t.v.I_RECARM == 1 then
        local length = math.max(0.5, F.play_position - F.recording_from)
        local from, to = F.recording_from, F.recording_from + length
        local function piece(a, b)
          local item = F.new_audio_item(t, a, b - a, F.recorded_file)
          item.takes[1].v.D_STARTOFFS = a - from
          item.takes[1].length = length
          return item
        end
        if not F.adds_takes then
          piece(from, to)
        else
          -- REAPER's default for a recording over older items ("splits existing items and
          -- creates new takes"), as read from REAPER 7.85 on 2026-11-14: the old item is
          -- split at both ends of the pass, the piece under it gets the recording as a
          -- second, active take, the pieces outside get an empty take lane, and what no
          -- old item covered becomes an item of its own.
          local olds = {}
          for _, old in ipairs(t.items) do olds[#olds + 1] = old end
          table.sort(olds, function(a, b) return a.v.D_POSITION < b.v.D_POSITION end)
          local at = from
          for _, old in ipairs(olds) do
            local pos, fin = old.v.D_POSITION, old.v.D_POSITION + old.v.D_LENGTH
            if pos < to and fin > from then
              local mid = old
              if pos < from then
                mid = reaper.SplitMediaItem(old, from)
                old.takes[2] = F.EMPTY
              end
              if fin > to then reaper.SplitMediaItem(mid, to).takes[2] = F.EMPTY end
              if mid.v.D_POSITION > at then piece(at, mid.v.D_POSITION) end
              local new = piece(mid.v.D_POSITION, mid.v.D_POSITION + mid.v.D_LENGTH)
              table.remove(t.items)              -- its take moves into the old piece
              mid.takes[#mid.takes + 1] = new.takes[1]
              mid.active = #mid.takes
              at = mid.v.D_POSITION + mid.v.D_LENGTH
            end
          end
          if at < to then piece(at, to) end
        end
      end
    end
  end
  F.play_state = 0
end

-- 120 bpm in 4/4 all the way: a quarter note is half a second.
function reaper.TimeMap2_QNToTime(_, qn) return qn / 2 end
function reaper.TimeMap2_timeToQN(_, t) return t * 2 end
function reaper.TimeMap_GetMeasureInfo(_, measure) return 0.0, measure * 4, measure * 4 + 4, 4, 4, 120.0 end
function reaper.TimeMap2_timeToBeats(_, t)
  local qn = t * 2
  local measures = qn // 4
  return qn - measures * 4, measures, 4
end

--------------------------------------------------------------------- actions

function reaper.NamedCommandLookup(name)
  for id, a in pairs(F.action_names) do
    if a.named == name then return id end
  end
  return 0
end
function reaper.kbd_getTextFromCmd(id) return F.action_names[id] and F.action_names[id].name or "" end
function reaper.ReverseNamedCommandLookup(id) return F.action_names[id] and F.action_names[id].named or nil end

---------------------------------------------------------------------- tracks

function reaper.GetMasterTrack() return master end
function reaper.CountTracks() return #F.tracks end
function reaper.GetTrack(_, i) return F.tracks[i + 1] end
function reaper.GetTrackGUID(t) return t.guid end
function reaper.GetTrackName(t) return true, t.name end
function reaper.InsertTrackAtIndex(index) table.insert(F.tracks, index + 1, make_track("")) end
function reaper.DeleteTrack(t) table.remove(F.tracks, assert(index_of(F.tracks, t), "no such track")) end
function reaper.IsTrackSelected(t) return t.selected end
function reaper.SetTrackSelected(t, selected) t.selected = selected end
function reaper.SetOnlyTrackSelected(t)
  for _, other in ipairs(F.tracks) do other.selected = other == t end
end

function reaper.GetMediaTrackInfo_Value(t, key)
  if key == "IP_TRACKNUMBER" then return t == master and -1 or index_of(F.tracks, t) end
  if TRACK_DEFAULTS[key] == nil then error("fake reaper has no track value " .. tostring(key), 2) end
  return t.v[key]
end
function reaper.SetMediaTrackInfo_Value(t, key, value)
  if TRACK_DEFAULTS[key] == nil then error("fake reaper has no track value " .. tostring(key), 2) end
  t.v[key] = value
  return true
end

function reaper.GetSetMediaTrackInfo_String(t, key, value, set)
  if key == "P_NAME" then
    if set then t.name = value end
    return true, t.name
  end
  local ext = key:match("^P_EXT:(.+)$")
  if not ext then error("fake reaper has no track string " .. tostring(key), 2) end
  if set then t.ext[ext] = value end
  return t.ext[ext] ~= nil, t.ext[ext] or ""
end

----------------------------------------------------------------------- items

function reaper.CountTrackMediaItems(t) return #t.items end
function reaper.GetTrackMediaItem(t, i) return t.items[i + 1] end
function reaper.GetMediaItem_Track(item) return item.track end
function reaper.DeleteTrackMediaItem(t, item)
  table.remove(t.items, assert(index_of(t.items, item), "the item isn't on that track"))
  return true
end

function reaper.GetMediaItemInfo_Value(item, key)
  if ITEM_DEFAULTS[key] == nil then error("fake reaper has no item value " .. tostring(key), 2) end
  return item.v[key]
end
function reaper.SetMediaItemInfo_Value(item, key, value)
  if ITEM_DEFAULTS[key] == nil then error("fake reaper has no item value " .. tostring(key), 2) end
  item.v[key] = value
  return true
end

function reaper.GetSetMediaItemInfo_String(item, key, value, set)
  if key == "GUID" then return true, item.guid end
  local ext = key:match("^P_EXT:(.+)$")
  if not ext then error("fake reaper has no item string " .. tostring(key), 2) end
  if set then item.ext[ext] = value end
  return item.ext[ext] ~= nil, item.ext[ext] or ""
end

function reaper.CountSelectedMediaItems()
  local n = 0
  for _, item in ipairs(all_items()) do
    if item.selected then n = n + 1 end
  end
  return n
end
function reaper.GetSelectedMediaItem(_, i)
  local n = -1
  for _, item in ipairs(all_items()) do
    if item.selected then
      n = n + 1
      if n == i then return item end
    end
  end
end
function reaper.SelectAllMediaItems(_, selected)
  for _, item in ipairs(all_items()) do item.selected = selected end
end
function reaper.SetMediaItemSelected(item, selected) item.selected = selected end
function reaper.IsMediaItemSelected(item) return item.selected end

function reaper.CreateNewMIDIItemInProj(t, from, to)
  return make_item(t, from, to - from, make_take(true))
end

-- Imports F.media[path] onto the selected track at the cursor and selects what it made.
function reaper.InsertMedia(path)
  local spec = F.media[path]
  if not spec then return 0 end
  for _, t in ipairs(F.tracks) do
    if t.selected then
      local item
      if path:lower():match("%.midi?$") then
        item = F.new_midi_item(t, F.cursor, spec.length or 4.0, spec)
      else
        item = F.new_audio_item(t, F.cursor, spec.length or 4.0, path)
      end
      item.selected = true
      return 1
    end
  end
  return 0
end

----------------------------------------------------------------------- takes

F.EMPTY = { empty = true, events = {}, notes = {}, v = {} }  -- an empty take lane: REAPER hands back nil for it
local function real(take) if take ~= F.EMPTY then return take end end
function reaper.CountTakes(item) return #item.takes end
function reaper.GetTake(item, i) return real(item.takes[i + 1]) end
function reaper.GetActiveTake(item) return real(item.takes[item.active or 1]) end
function reaper.TakeIsMIDI(take) return take.midi end
function reaper.GetMediaItemTake_Source(take) return take end
function reaper.GetMediaSourceFileName(source) return source.file end
-- The right-hand piece, as REAPER returns it; nil when the position isn't inside the item.
function reaper.SplitMediaItem(item, position)
  local pos, len = item.v.D_POSITION, item.v.D_LENGTH
  if position <= pos or position >= pos + len then return nil end
  local right = F.new_audio_item(item.track, position, pos + len - position, item.takes[1].file)
  right.takes[1].v.D_STARTOFFS = item.takes[1].v.D_STARTOFFS + (position - pos)
  right.takes[1].name = item.takes[1].name
  item.v.D_LENGTH = position - pos
  return right
end
function reaper.GetMediaSourceLength(source) return source.length or 0, false end
function reaper.GetMediaItemTakeInfo_Value(take, key)
  if key == "D_PLAYRATE" then return take.v[key] or 1.0 end
  if key ~= "D_STARTOFFS" then error("fake reaper has no take value " .. tostring(key), 2) end
  return take.v[key]
end
-- A MIDI take's events as REAPER packs them: int32 offset, flags byte, int32 length, bytes.
function reaper.MIDI_GetAllEvts(take, _)
  return true, take.evts or ""
end
function reaper.SetMediaItemTakeInfo_Value(take, key, value)
  if key ~= "D_STARTOFFS" then error("fake reaper has no take value " .. tostring(key), 2) end
  take.v[key] = value
  return true
end
function reaper.GetSetMediaItemTakeInfo_String(take, key, value, set)
  if key ~= "P_NAME" then error("fake reaper has no take string " .. tostring(key), 2) end
  if set then take.name = value end
  return true, take.name
end

function reaper.MIDI_CountEvts(take) return true, #take.notes, 0, #take.events end
function reaper.MIDI_GetTextSysexEvt(take, i)
  local e = take.events[i + 1]
  if not e then return false, false, false, 0, 0, "" end
  return true, false, false, 0, e.kind, e.msg
end
function reaper.MIDI_DeleteTextSysexEvt(take, i)
  if F.sysex_stuck or not take.events[i + 1] then return false end
  table.remove(take.events, i + 1)
  return true
end
function reaper.MIDI_InsertTextSysexEvt(take, _, _, _, kind, msg)
  take.events[#take.events + 1] = { kind = kind, msg = msg }
  return true
end
function reaper.MIDI_InsertNote(take, _, _, from, to, chan, pitch, velocity)
  take.notes[#take.notes + 1] = { from = from, to = to, chan = chan, pitch = pitch, velocity = velocity }
  return true
end
function reaper.MIDI_Sort() end
function reaper.MIDI_GetPPQPosFromProjTime(_, t) return t * 1920 end

-------------------------------------------------------------- loud when missing

-- A call a test has marked in F.raise_in raises, as if REAPER had failed there.
for name, fn in pairs(reaper) do
  reaper[name] = function(...)
    if F.raise_in[name] then error("fake reaper: " .. name .. " failed (the test asked for it)", 2) end
    return fn(...)
  end
end

setmetatable(reaper, { __index = function(_, name)
  if OPTIONAL[name] then return nil end
  error("fake reaper has no '" .. tostring(name) .. "': add it to tests/fake_reaper.lua if the bridge really calls it", 2)
end })

return reaper, F

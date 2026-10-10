-- @noindex
-- Minimal JSON encoder/decoder shared by the creaper scripts.
-- Empty tables encode as []; wrap with json.object() to get {}.

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

return json

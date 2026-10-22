--[[ capture.lua -- render every dial in the clock tree to a PNG, headlessly.

     Run it through conky, which supplies the Lua + cairo the clocks expect:

         CAP_OUT=assets/img CAP_META=tools/manifest.json \
           conky -c tools/capture/capture.conf

     Why conky and not plain lua: the clocks are conky clocks.  lib/dial.lua
     loads each one -- either its dial.lua adapter, or its .conf plus the Lua
     that conf loads, through the lib/standalone.lua sandbox, which hands a
     clock an offscreen surface in place of its window.  So what lands in the
     PNG is the same code path the live desktop clock runs, at exactly the size
     it is drawn on screen, with no window manager, compositor or screenshot
     in the loop.

     Environment:
       CLOCK_DIR  the clock tree      (default ~/.config/conky/clocks)
       CAP_OUT    image directory     (default assets/img)
       CAP_META   manifest json path  (default tools/manifest.json)
       CAP_SIZE   square canvas in px (default 640)
       CAP_IDS    file of ids, one per line (default: everything discover())
       CAP_ONLY   substring filter on the id
]]

local DIR  = os.getenv('CLOCK_DIR') or (os.getenv('HOME') .. '/.config/conky/clocks')
local OUT  = os.getenv('CAP_OUT') or 'assets/img'
local META = os.getenv('CAP_META') or 'tools/manifest.json'
local SIZE = tonumber(os.getenv('CAP_SIZE') or '640')
local ONLY = os.getenv('CAP_ONLY')

-- conky was told to call this as the draw hook; the work happens at load time,
-- before it would be called, so that one conky process writes every PNG.
function capture() end

local D = dofile(DIR .. '/lib/dial.lua')

local function readlines(path)
  local f = path and io.open(path, 'r')
  if not f then return nil end
  local t = {}
  for l in f:lines() do if l:match('%S') then t[#t + 1] = l end end
  f:close()
  return t
end

local function esc(s)
  s = tostring(s or '')
  s = s:gsub('\\', '\\\\'):gsub('"', '\\"'):gsub('[\r\n]', ' ')
  return s
end

local ids = readlines(os.getenv('CAP_IDS')) or D.discover()

os.execute("mkdir -p '" .. OUT .. "'")

local rows, nok, nfail = {}, 0, 0
for _, id in ipairs(ids) do
  if not ONLY or id:find(ONLY, 1, true) then
    local name = id:gsub('/', '__') .. '.png'
    local dial, err = nil, nil
    local ok = pcall(function() dial, err = D.load(id) end)
    if not ok then dial, err = nil, tostring(dial) end

    if type(dial) ~= 'table' or type(dial.draw) ~= 'function' then
      nfail = nfail + 1
      print('LOADFAIL ' .. id .. ' ' .. tostring(err or 'no dial'))
    else
      local surf = cairo_image_surface_create(CAIRO_FORMAT_ARGB32, SIZE, SIZE)
      local cr = cairo_create(surf)
      local drew, derr = pcall(dial.draw, cr, SIZE / 2, SIZE / 2, SIZE * 0.46)
      cairo_surface_flush(surf)
      local wr = cairo_surface_write_to_png(surf, OUT .. '/' .. name)
      cairo_destroy(cr)
      cairo_surface_destroy(surf)

      if drew and wr == 0 then
        nok = nok + 1
        rows[#rows + 1] = string.format(
          '{"id":"%s","name":"%s","blurb":"%s","file":"%s"}',
          esc(id), esc(dial.name), esc(dial.blurb), esc(name))
      else
        nfail = nfail + 1
        print('DRAWFAIL ' .. id .. ' ' .. tostring(derr) .. ' write=' .. tostring(wr))
      end
    end
  end
end

local f = io.open(META, 'w')
if f then f:write('[\n' .. table.concat(rows, ',\n') .. '\n]\n'); f:close() end
print(string.format('captured %d, failed %d -> %s', nok, nfail, META))
os.exit(0)

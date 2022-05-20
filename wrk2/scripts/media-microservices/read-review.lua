require "socket"
local time = socket.gettime()*1000
math.randomseed(time)
math.random(); math.random(); math.random()

request = function()
  local movie_id = tostring(math.random(1,990))
  local start = tostring(math.random(0,79))
  local stop = tostring(start + 10)

  local args = "movie_id=" .. movie_id .. "&start=" .. start .. "&stop=" .. stop
  local method = "GET"
  local headers = {}
  headers["Content-Type"] = "application/x-www-form-urlencoded"
  -- Use your cluster-ip here:
  --local path = "http://localhost:8080/wrk2-api/user-timeline/read?" .. args
  local path = "http://userv2:8080/wrk2-api/review/read?" .. args
  return wrk.format(method, path, headers, nil)

end

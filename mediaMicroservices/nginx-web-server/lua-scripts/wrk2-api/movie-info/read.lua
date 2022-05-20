local _M = {}

local function _StrIsEmpty(s)
  return s == nil or s == ''
end

local function _LoadMovieInfo(data)
  local all_movie_info = {}
  for _, movie_info in ipairs(data) do
    local new_movie_info = {}
    new_movie_info["plot_id"] = tostring(movie_info.plot_id)
    new_movie_info["movie_id"] = tostring(movie_info.movie_id)
    new_movie_info["num_rating"] = tostring(movie_info.num_rating)    
    new_movie_info["avg_rating"] = tostring(movie_info.avg_rating)
    new_movie_info["title"] = movie_info.title
        
    table.insert(all_movie_info, new_movie_info)
  end
  return all_movie_info
end

function _M.ReadMovieInfo()
  local bridge_tracer = require "opentracing_bridge_tracer"
  local GenericObjectPool = require "GenericObjectPool"
  local MovieInfoServiceClient = require 'media_service_MovieInfoService'
  local ttypes = require("media_service_ttypes")
  local Cast = ttypes.Cast
  local ngx = ngx
  local cjson = require("cjson")

  local req_id = tonumber(string.sub(ngx.var.request_id, 0, 15), 16)
  local tracer = bridge_tracer.new_from_global()
  local parent_span_context = tracer:binary_extract(
      ngx.var.opentracing_binary_context)
  local span = tracer:start_span("ReadMovieInfoService",
      {["references"] = {{"child_of", parent_span_context}}})
  local carrier = {}
  tracer:text_map_inject(span:context(), carrier)

  ngx.req.read_body()
  local args = ngx.req.get_uri_args()

  if (_StrIsEmpty(args.movie_id)) then
    ngx.status = ngx.HTTP_BAD_REQUEST
    ngx.say("Incomplete arguments")
    ngx.log(ngx.ERR, "Incomplete arguments")
    ngx.exit(ngx.HTTP_BAD_REQUEST)
  end

  local client = GenericObjectPool:connection(
      MovieInfoServiceClient, "movie-info-service", 9090)
  local status, ret = pcall(client.ReadMovieInfo, client, req_id,tonumber(args.movie_id), carrier)

  GenericObjectPool:returnConnection(client)
  if not status then
    ngx.status = ngx.HTTP_INTERNAL_SERVER_ERROR
    if (ret.message) then
      ngx.say("Get movie-info failure: " .. ret.message)
      ngx.log(ngx.ERR, "Get movie-info failure: " .. ret.message)
    else
      ngx.say("Get movie-info failure: : no return..")
      ngx.log(ngx.ERR, "Get movie-info failure: : no return..")
    end
    ngx.exit(ngx.HTTP_INTERNAL_SERVER_ERROR)
  else
    local all_movie_info = _LoadMovieInfo(ret)
    ngx.header.content_type = "application/json; charset=utf-8"
    ngx.say(cjson.encode(all_movie_info) )

  end
end

return _M

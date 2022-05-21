local _M = {}

local function _StrIsEmpty(s)
  return s == nil or s == ''
end

local function _LoadPlotInfo(data)
  local all_plot_infos = {}
  
  --for _, review_post in ipairs(data) do
    --local new_plot = {}
    --new_plot["plot_id"] = tostring(review_post.plot_id)
    --new_plot["plot"] = tostring(review_post.plot)
    --table.insert(all_plot_infos, new_plot)
  --end
  table.insert(all_plot_infos,new_plot)
  return all_plot_infos
end

function _M.ReadPlotInfo()
  
  local bridge_tracer = require "opentracing_bridge_tracer"
  local GenericObjectPool = require "GenericObjectPool"
  local PlotServiceClient = require 'media_service_PlotService'
  local ngx = ngx
  local cjson = require("cjson")  

  local req_id = tonumber(string.sub(ngx.var.request_id, 0, 15), 16)
  local tracer = bridge_tracer.new_from_global()
  local parent_span_context = tracer:binary_extract(ngx.var.opentracing_binary_context)
  local span = tracer:start_span("ReadPlot", {["references"] = {{"child_of", parent_span_context}}})
  local carrier = {}
  tracer:text_map_inject(span:context(), carrier)

  ngx.req.read_body()
  local args = ngx.req.get_uri_args()
  
  if (_StrIsEmpty(args.plot_id)) then
    ngx.status = ngx.HTTP_BAD_REQUEST
    ngx.say("Incomplete arguments")
    ngx.log(ngx.ERR, "Incomplete arguments")
    ngx.exit(ngx.HTTP_BAD_REQUEST)
  end
  
  local client = GenericObjectPool:connection(
      PlotServiceClient, "plot-service", 9090)
  local status, ret = pcall(client.ReadPlot, client, req_id, tonumber(args.plot_id),carrier)
  GenericObjectPool:returnConnection(client)
  
  if not status then
    ngx.status = ngx.HTTP_INTERNAL_SERVER_ERROR
    if (ret.message) then
      ngx.say("Get read-plot-info failure: " .. ret.message)
      ngx.log(ngx.ERR, "Get  read-plot-info failure: " .. ret.message)
    else
      ngx.say("Get  read-plot-info  failure: no return..")
      ngx.log(ngx.ERR, "Get  read-plot-info  failure:  no return..")
    end
    ngx.exit(ngx.HTTP_INTERNAL_SERVER_ERROR)
  else
    local all_plot_infos = _LoadPlotInfo(ret)
    ngx.header.content_type = "application/json; charset=utf-8"
    ngx.say(cjson.encode(all_plot_infos) )

  end
end

return _M

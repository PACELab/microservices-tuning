local _M = {}

local function _StrIsEmpty(s)
  return s == nil or s == ''
end

local function _LoadReviews(data)
  local movie_reviews = {}
  for _, review_post in ipairs(data) do
    local new_post = {}
    new_post["review_id"] = tostring(review_post.review_id)
    new_post["movie_id"] = tostring(review_post.movie_id)
    new_post["rating"] = tostring(review_post.rating)    
    new_post["text"] = review_post.text
    new_post["timestamp"] = tostring(review_post.timestamp)
    new_post["post_type"] = review_post.post_type
        
    table.insert(movie_reviews, new_post)
  end
  return movie_reviews
end

function _M.ReadMovieReviews()
  local bridge_tracer = require "opentracing_bridge_tracer"
  local ngx = ngx
  local GenericObjectPool = require "GenericObjectPool"
  local MovieReviewServiceClient = require "media_service_MovieReviewService"
  local cjson = require "cjson"
  local liblualongnumber = require "liblualongnumber"

  local req_id = tonumber(string.sub(ngx.var.request_id, 0, 15), 16)
  local tracer = bridge_tracer.new_from_global()
  local parent_span_context = tracer:binary_extract(
      ngx.var.opentracing_binary_context)
  local span = tracer:start_span("ReadMovieReviewService",
      {["references"] = {{"child_of", parent_span_context}}})
  local carrier = {}
  tracer:text_map_inject(span:context(), carrier)

  ngx.req.read_body()
  local args = ngx.req.get_uri_args()

  if (_StrIsEmpty(args.movie_id) or _StrIsEmpty(args.start) or _StrIsEmpty(args.stop)) then
    ngx.status = ngx.HTTP_BAD_REQUEST
    ngx.say("Incomplete arguments")
    ngx.log(ngx.ERR, "Incomplete arguments")
    ngx.exit(ngx.HTTP_BAD_REQUEST)
  end

  local client = GenericObjectPool:connection(
      MovieReviewServiceClient, "movie-review-service", 9090)
  local status, ret = pcall(client.ReadMovieReviews, client, req_id,
      tonumber(args.movie_id), tonumber(args.start), tonumber(args.stop), carrier)
  GenericObjectPool:returnConnection(client)
  if not status then
    ngx.status = ngx.HTTP_INTERNAL_SERVER_ERROR
    if (ret.message) then
      ngx.say("Get movie-reviews failure: " .. ret.message)
      ngx.log(ngx.ERR, "Get movie-reviews failure: " .. ret.message)
    else
      ngx.say("Get movie-reviews failure: : no return..")
      ngx.log(ngx.ERR, "Get movie-reviews failure: : no return..")
    end
    ngx.exit(ngx.HTTP_INTERNAL_SERVER_ERROR)
  else
    local movie_reviews = _LoadReviews(ret)
    ngx.header.content_type = "application/json; charset=utf-8"
    ngx.say(cjson.encode(movie_reviews) )

  end
end

return _M

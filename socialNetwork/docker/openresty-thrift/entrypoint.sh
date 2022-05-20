while true
do
	curl http://127.0.0.1/nginx_status
	sleep 60
done &

/usr/local/openresty/bin/openresty -g daemon off

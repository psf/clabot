bind = "unix:/var/run/cabotage/cabotage.sock"
worker_class = "clabot.workers.UvicornWorker"
workers = 2

backlog = 2048
preload_app = True
max_requests = 100_000
max_requests_jitter = 5_000

timeout = 20
keepalive = 2

errorlog = "-"
loglevel = "info"
accesslog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(M)'

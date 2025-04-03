worker_class = "clabot.workers.UvicornWorker"
workers = 2

backlog = 2048
preload_app = True
max_requests = 2048
max_requests_jitter = 128

timeout = 60
keepalive = 2

errorlog = "-"
loglevel = "info"
accesslog = "-"

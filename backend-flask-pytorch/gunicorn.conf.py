"""One model process with threads for responsive status requests."""
workers = 1
worker_class = "gthread"
threads = 4
bind = "0.0.0.0:5000"
timeout = 180
graceful_timeout = 30

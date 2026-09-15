class server_info:
    server_name = "python-on-pails or maybe ruby even nmap can't tell"
    server_version = "2.0"
class project_info:
    name = 'Sample_Name'
    version= 1.0

class scripts:
    run = 'python3 main.py'

class config:
    entry = 'main.py'
    host = '0.0.0.0'
    port = 80 #http port
    
    enableTLS = False #enable for TLS Support
    sPort=443 #secure/https port
    PATH_TLS_KEY_FILE = None #give path to key file here (string)
    PATH_TLS_CERT_FILE = None #give path to CERT file here (string)
    redirect_to_https = False # enable to redirect all http requests to https

    #some options for security
    wildcard_response = True #will give 200 even from missing files
    fool_nmap = True #will send 200 and random response for arbitrary http methods , which will hopefully fool nmap
    fool_nmap_content = "Unsupported method But handled like a Pro" #change it and tell me if it has any effect

    # --- protocol / serving contracts (see docs/serving.md) ---
    # production=False preserves legacy dev behaviour (fool_nmap 200s,
    # 500 on missing files). production=True returns standards-based
    # 400/404/405/413/414/431/500/501 responses.
    production = False
    legacy_compat = True  # explicit opt-out: set False + production True

    # request limits -> 413/414/431
    max_body_size = 1024 * 1024   # 1 MiB
    max_url_length = 8192
    max_header_size = 16384

    # timeouts (seconds); dev server applies request/idle timeouts
    request_timeout = 30
    header_timeout = 10
    body_timeout = 30
    idle_timeout = 60
    shutdown_drain_seconds = 10

    # trusted proxy: set trust_proxy_headers=True behind Nginx/Caddy/
    # Cloudflare to honor X-Forwarded-{For,Host,Proto,Port}. Optionally
    # restrict with trusted_proxies=["10.0.0.1"] (["*"] trusts all).
    trust_proxy_headers = False
    trusted_proxies = []

    # lifecycle hooks: lists of no-arg callables
    on_startup = []
    on_shutdown = []

    models='mvc/models/'
    controllers='mvc/controllers/'
    views='mvc/views/'
    static='mvc/views/static/'
    logging=False





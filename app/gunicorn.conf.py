import os
workers = 1
timeout = 1800
bind = f"0.0.0.0:{os.getenv('PORT', '3000')}"

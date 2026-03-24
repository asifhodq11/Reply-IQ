# ============================================================
# ReplyIQ Backend — Extensions
# Initialized once, imported everywhere
# ============================================================

import os
from supabase import create_client, Client
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from flask_talisman import Talisman

# 1. Database client — ONE instance, shared across the entire application
# NEVER call create_client() inside a route or service
supabase: Client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_ROLE_KEY"],  # We use service role key for backend operations
)

# 2. Rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"], storage_uri="memory://")

# 3. CORS — configured in create_app to FRONTEND_URL
cors = CORS()

# 4. HTTPS enforcement + security headers
talisman = Talisman()

import os

# We must set these environment variables before the app factory runs
# because config.py uses os.environ['KEY'] to ensure aggressive failure
# if required config is missing.
os.environ['SECRET_KEY'] = 'test-secret'
os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
os.environ['SUPABASE_ANON_KEY'] = 'test-anon-key'
os.environ['SUPABASE_SERVICE_ROLE_KEY'] = 'test-service-key'
os.environ['OPENAI_API_KEY'] = 'test-openai-key'
os.environ['GEMINI_API_KEY'] = 'test-gemini-key'
os.environ['GOOGLE_API_KEY'] = 'test-google-key'
os.environ['STRIPE_SECRET_KEY'] = 'test-stripe-key'
os.environ['STRIPE_WEBHOOK_SECRET'] = 'test-webhook-secret'
os.environ['STRIPE_PRICE_ID_STARTER'] = 'test-price-id'
os.environ['RESEND_API_KEY'] = 'test-resend-key'
os.environ['FRONTEND_URL'] = 'http://test.localhost'

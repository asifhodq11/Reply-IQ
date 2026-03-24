"""
tests/services/test_stripe_service.py

5 tests for Phase 6 Stripe payment service.
All Stripe and Supabase calls are fully mocked — no real API calls.
"""

import os

# Set dummy env vars BEFORE any app imports
os.environ['SECRET_KEY'] = 'test-secret'
os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
FAKE_JWT = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSJ9.fake_signature_for_testing'
os.environ['SUPABASE_ANON_KEY'] = FAKE_JWT
os.environ['SUPABASE_SERVICE_ROLE_KEY'] = FAKE_JWT
os.environ['OPENAI_API_KEY'] = 'test-openai-key'
os.environ['GEMINI_API_KEY'] = 'test-gemini-key'
os.environ['GOOGLE_API_KEY'] = 'test-google-key'
os.environ['STRIPE_SECRET_KEY'] = 'test-stripe-key'
os.environ['STRIPE_WEBHOOK_SECRET'] = 'test-webhook-secret'
os.environ['STRIPE_PRICE_ID_STARTER'] = 'price_test_starter'
os.environ['RESEND_API_KEY'] = 'test-resend-key'
os.environ['FRONTEND_URL'] = 'http://test.localhost'

import pytest
import stripe
from unittest.mock import patch, MagicMock, call

from app.services.stripe_service import (
    handle_webhook_event,
    cancel_subscription,
    _processed_event_ids,
)
from app.utils.exceptions import StripeWebhookInvalid


FAKE_USER_ID = 'aaaaaaaa-0000-0000-0000-aaaaaaaaaaaa'
FAKE_CUSTOMER_ID = 'cus_test_fakecustomer'


def _make_checkout_event(event_id='evt_001'):
    """Builds a fake checkout.session.completed event dict."""
    return {
        'id': event_id,
        'type': 'checkout.session.completed',
        'data': {
            'object': {
                'client_reference_id': FAKE_USER_ID,
                'customer': FAKE_CUSTOMER_ID,
            }
        }
    }


def _make_payment_failed_event(event_id='evt_002'):
    """Builds a fake invoice.payment_failed event dict."""
    return {
        'id': event_id,
        'type': 'invoice.payment_failed',
        'data': {
            'object': {
                'customer': FAKE_CUSTOMER_ID,
            }
        }
    }


# ──────────────────────────────────────────────────────────────
# TEST 1 — Valid webhook signature upgrades plan to starter
# ──────────────────────────────────────────────────────────────

def test_valid_webhook_upgrades_plan():
    event = _make_checkout_event(event_id='evt_test1')
    
    # Ensure this event hasn't been seen before
    _processed_event_ids.discard('evt_test1')

    mock_query = MagicMock()
    mock_query.update.return_value = mock_query
    mock_query.eq.return_value = mock_query
    mock_query.execute.return_value = MagicMock(data=None)

    with patch('stripe.Webhook.construct_event', return_value=event), \
         patch('app.services.stripe_service.supabase') as mock_sb:

        mock_sb.from_.return_value = mock_query

        result = handle_webhook_event(b'fake-payload', 'fake-sig-header')

    assert result == {'received': True}
    mock_query.update.assert_called_once_with({
        'plan': 'starter',
        'stripe_customer_id': FAKE_CUSTOMER_ID,
    })


# ──────────────────────────────────────────────────────────────
# TEST 2 — Invalid webhook signature raises StripeWebhookInvalid
# ──────────────────────────────────────────────────────────────

def test_invalid_signature_raises():
    with patch(
        'stripe.Webhook.construct_event',
        side_effect=stripe.error.SignatureVerificationError(
            'invalid', 'sig_header'
        )
    ):
        with pytest.raises(StripeWebhookInvalid):
            handle_webhook_event(b'bad-payload', 'bad-sig')


# ──────────────────────────────────────────────────────────────
# TEST 3 — invoice.payment_failed downgrades plan to free
# ──────────────────────────────────────────────────────────────

def test_payment_failed_downgrades_plan():
    event = _make_payment_failed_event(event_id='evt_test3')

    _processed_event_ids.discard('evt_test3')

    mock_query = MagicMock()
    mock_query.update.return_value = mock_query
    mock_query.eq.return_value = mock_query
    mock_query.execute.return_value = MagicMock(data=None)

    with patch('stripe.Webhook.construct_event', return_value=event), \
         patch('app.services.stripe_service.supabase') as mock_sb:

        mock_sb.from_.return_value = mock_query

        result = handle_webhook_event(b'fake-payload', 'fake-sig')

    assert result == {'received': True}
    mock_query.update.assert_called_once_with({'plan': 'free'})


# ──────────────────────────────────────────────────────────────
# TEST 4 — Replayed event is idempotent (DB called only once)
# ──────────────────────────────────────────────────────────────

def test_replayed_event_is_idempotent():
    event = _make_checkout_event(event_id='evt_test4')

    # Ensure clean state for this specific event
    _processed_event_ids.discard('evt_test4')

    mock_query = MagicMock()
    mock_query.update.return_value = mock_query
    mock_query.eq.return_value = mock_query
    mock_query.execute.return_value = MagicMock(data=None)

    with patch('stripe.Webhook.construct_event', return_value=event), \
         patch('app.services.stripe_service.supabase') as mock_sb:

        mock_sb.from_.return_value = mock_query

        # First call — should process
        handle_webhook_event(b'fake-payload', 'fake-sig')
        # Second call — same event_id, should be skipped
        handle_webhook_event(b'fake-payload', 'fake-sig')

    # DB update should have been called exactly once
    assert mock_query.update.call_count == 1


# ──────────────────────────────────────────────────────────────
# TEST 5 — cancel_subscription cancels at period end
# ──────────────────────────────────────────────────────────────

def test_cancel_subscription_at_period_end():
    mock_subscription = MagicMock()
    mock_subscription.id = 'sub_test_fake123'

    mock_subscriptions_list = MagicMock()
    mock_subscriptions_list.data = [mock_subscription]

    mock_query = MagicMock()
    mock_query.update.return_value = mock_query
    mock_query.eq.return_value = mock_query
    mock_query.execute.return_value = MagicMock(data=None)

    with patch('stripe.Subscription.list', return_value=mock_subscriptions_list), \
         patch('stripe.Subscription.modify') as mock_modify, \
         patch('app.services.stripe_service.supabase') as mock_sb:

        mock_sb.from_.return_value = mock_query

        result = cancel_subscription(
            user_id=FAKE_USER_ID,
            stripe_customer_id=FAKE_CUSTOMER_ID,
            reason='too_expensive',
        )

    assert result is True
    mock_modify.assert_called_once_with(
        'sub_test_fake123',
        cancel_at_period_end=True,
    )
    mock_query.update.assert_called_once_with({
        'plan': 'free',
        'cancellation_reason': 'too_expensive',
    })

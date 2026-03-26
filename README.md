<div align="center">
  <img src="docs/assets/banner.png" alt="ReplyIQ Banner" width="100%">

  [![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](https://opensource.org/licenses/MIT)
  [![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
  [![Framework](https://img.shields.io/badge/Framework-Flask-black.svg)](https://flask.palletsprojects.com/)
  [![Database](https://img.shields.io/badge/Database-Supabase-green.svg)](https://supabase.com/)
  [![Tests](https://img.shields.io/badge/Tests-53%2F53%20Passing-brightgreen.svg)](tests/)

  <h3><b>ReplyIQ: The 3-Pass AI Review Humaniser</b></h3>
  <p><i>Turn automated responses into authentic conversations with zero AI artifacts.</i></p>
</div>

---

## ✨ The Magic: Why ReplyIQ?

Most AI responses feel "robotic" and can damage your brand. ReplyIQ uses a proprietary **3-Pass Humaniser Pipeline** to ensure your customers feel heard by a human, not a bot.

- 🤖 **Pass 1: Professional Draft** — Generates a high-context response based on business type and sentiment.
- 🌿 **Pass 2: De-Botting** — Strips 24 specifically identified "AI-sounding" patterns (e.g., "pivotal," "vibrant," "delve").
- ✍️ **Pass 3: Tone Audit** — A final self-correction pass for perfect grammar and natural flow.

---

## 🚀 Speed to Value: Quick Start

See the humaniser in action in under 60 seconds:

```bash
# 1. Clone & Setup
git clone https://github.com/asifhodq11/Reply-IQ.git
cd Reply-IQ
make install

# 2. Configure (AI Provider switch)
cp .env.example .env
# Set AI_PROVIDER=openrouter or openai

# 3. Launch
make run
```

---

## 🛡️ Trust Architecture

Built for scale, security, and compliance from day one.

- **Smart Model Routing:** Crises get GPT-4o; simple ratings get Gemini-Flash-Lite. Save costs without losing quality.
- **Tenant Isolation:** Multi-layer security ensures users only ever see their own data.
- **GDPR Compliance:** Built-in account anonymisation and data retention jobs.
- **Atomic Operations:** Race-condition-free usage tracking and billing integration (Stripe).

---

## 🛠️ The Mechanics

<details>
<summary><b>Technical Stack</b></summary>

- **Backend:** Flask (Application Factory Pattern)
- **Database:** Supabase (Postgres)
- **AI Engines:** OpenAI / Google Gemini / OpenRouter
- **Payments:** Stripe SDK (Sub-lifecycle managed)
- **Rate Limiting:** Flask-Limiter (Per-route enforcement)
- **Testing:** Pytest (53+ Integration & Unit tests)

</details>

<details>
<summary><b>Environment Configuration</b></summary>

Required keys (sample):
- `SUPABASE_URL` & `SUPABASE_SERVICE_ROLE_KEY`
- `AI_PROVIDER` (`openai` | `openrouter`)
- `OPENROUTER_API_KEY` or `OPENAI_API_KEY`
- `STRIPE_SECRET_KEY` & `STRIPE_WEBHOOK_SECRET`
- `RESEND_API_KEY`

</details>

---

## 🤝 Contributing

We welcome high-signal contributions. Please see `CONTRIBUTING.md` (coming soon) or open an Issue for major feature requests.

---

<div align="center">
  <sub>Built with ❤️ for SaaS Founders & Business Owners.</sub>
</div>

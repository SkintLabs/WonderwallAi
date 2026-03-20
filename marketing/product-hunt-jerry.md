# Product Hunt Launch — Jerry The Customer Service Bot

## Tagline (under 60 chars)
AI customer service that actually knows your Shopify store

## Description (under 260 chars)
Jerry is an AI customer service bot built for Shopify. It syncs your catalog, tracks orders, handles returns, speaks 50+ languages, and attributes revenue — all protected by an AI firewall. Not a chatbot wrapper. A full AI employee.

## Maker's Comment

Hey Product Hunt! I'm Louis, and Jerry is the product I never planned to build.

At 40, with zero software background, I decided to teach myself to code. I had this simple idea: what if a Shopify store could have an AI assistant that actually understood its products — not keyword matching, but real semantic understanding?

Six months later, Jerry exists. I built every piece of it: the FastAPI backend, the React widget, the semantic search engine, the billing system, the AI firewall. Some days I had no idea what I was doing. Most days, honestly. But AI tools gave me superpowers I never expected, and stubbornness filled in the rest.

What makes Jerry different from the dozens of "AI chatbot" tools on the Shopify App Store is that Jerry actually connects to your store. It syncs your full product catalog into a vector database and understands queries like "something warm for hiking under $80." It pulls real order data from the Shopify Admin API for tracking. It processes returns through your actual policies. It even attributes revenue back to conversations so you can measure exactly what Jerry earns you.

The part I'm most proud of is the security layer. After launching Jerry in production, I watched users try to jailbreak it within the first week. Someone tried to extract an API key from the context window. That scared me enough to build WonderwallAi — an open-source AI firewall that now protects every Jerry conversation. It's a separate product, also launching on Product Hunt.

I'm a solo founder, first-time builder, and I made this because I genuinely believe small Shopify stores deserve the same quality AI support that enterprise companies get — without enterprise pricing.

I'd love your feedback. Try the live demo and break things. That's how I learn.

## Key Features

- **Semantic Product Search** — Customers search in natural language ("red dress under $60"), not keywords. Jerry understands price, size, colour, material, and occasion.
- **Order Tracking & Returns** — Real-time order status, shipping estimates, and return processing directly through the Shopify Admin API. Handles the #1 support query (WISMO) instantly.
- **Voice Chat & 50+ Languages** — Built-in speech-to-text and text-to-speech using browser Web Speech API. Automatic language detection. Zero extra cost.
- **Revenue Attribution** — 24-hour attribution window links conversations to purchases. See exactly how much revenue Jerry generates in your dashboard.
- **AI Firewall Protection** — Every conversation is protected by WonderwallAi's 4-layer pipeline: semantic routing, prompt injection detection, data leak prevention, and canary tokens.

## Links

- **Live Demo:** https://sunsetbot-production.up.railway.app/static/demo.html
- **Landing Page:** https://jerry.skintlabs.ai
- **GitHub:** https://github.com/Buddafest/sunsetbot
- **Parent Company:** https://skintlabs.ai

## Pricing

- **Base:** $299 USD/mo + $0.50/resolution + 1% revenue share on attributed sales
- **Elite:** $1,499 USD/mo + $1.00/resolution + 1% revenue share (includes custom brand voice, dedicated account manager, advanced analytics)

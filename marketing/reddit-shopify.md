# r/shopify Post

## Title
I built an AI customer service bot that actually connects to your Shopify store (not just a GPT wrapper)

## Body

I've been lurking in this sub for a while and I see the same pain points come up constantly: customer support volume is crushing, "Where Is My Order" tickets are relentless, and most AI chatbot tools just send messages to ChatGPT with your FAQ pasted in.

I built something different. Jerry The Customer Service Bot is an AI assistant that connects directly to your Shopify store through the Admin API. Here's what that actually means in practice:

**Semantic product search, not keyword matching.** A customer can type "I need something warm for hiking, nothing too expensive" and Jerry will search your actual catalog using vector embeddings, filter by price and attributes, and recommend products that are genuinely in stock. It understands size, colour, material, occasion — not just product titles.

**Real order tracking.** Jerry pulls live order data from Shopify. When a customer asks "where's my order #4821," Jerry checks fulfilment status, shipping carrier, and delivery estimates. No scripted "please check your email for tracking" responses.

**Returns processing.** Jerry knows your return policy, checks eligibility windows, and walks customers through the return flow. It can initiate returns and refunds through Shopify directly.

**Revenue attribution.** This is the part I'm most excited about. Jerry tracks which conversations lead to purchases within a 24-hour attribution window using Shopify order webhooks. You can see exactly how much revenue Jerry generated in your dashboard. It's not a cost centre — it's measurable.

**Built-in AI security.** Every conversation is protected by a 4-layer AI firewall (my other product, WonderwallAi). Nobody can jailbreak it, use it as a free coding assistant, or extract sensitive data. This matters more than people think — within the first week of testing, someone tried to get the LLM to reveal API keys.

**Voice chat and 50+ languages.** Uses the browser's built-in Web Speech API, so there's no extra cost and no external service. Customers can talk or type in any language.

The pricing is a flat $299/mo base plus performance billing ($0.50 per resolved conversation + 1% revenue share on attributed sales). The idea is you should only pay more when Jerry is earning you more.

I'm a solo founder and this is my first product. I built it because I genuinely think small and mid-size Shopify stores deserve AI support that actually works, not glorified FAQ bots.

There's a live demo you can try — it runs against a sample store so you can test product search, ask about orders, and see how it handles off-topic questions:
https://sunsetbot-production.up.railway.app/static/demo.html

Landing page with full details: https://jerry.skintlabs.ai

Happy to answer any questions. And if you try the demo and manage to break it, I genuinely want to know.

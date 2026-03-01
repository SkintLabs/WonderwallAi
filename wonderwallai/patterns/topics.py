"""
WonderwallAi — Pre-built Topic Sets
Use these with the ``topics`` parameter to quickly configure the semantic router.

Example::

    from wonderwallai import Wonderwall
    from wonderwallai.patterns.topics import ECOMMERCE_TOPICS

    wall = Wonderwall(topics=ECOMMERCE_TOPICS)
"""

ECOMMERCE_TOPICS = [
    "I want to buy a product from this store",
    "What products do you have available",
    "I need help with my order tracking and shipping",
    "What is your return and refund policy",
    "I need to return or exchange an item",
    "What sizes do you carry and what size should I get",
    "Tell me about the materials and quality of your products",
    "Do you ship internationally and how much does shipping cost",
    "I want to check my order status where is my order",
    "What payment methods do you accept",
    "Do you have any sales or discounts or coupon codes",
    "Can I speak to a human customer service agent",
    "I have a complaint about my order or a damaged item",
    "Help me find a gift recommendation for someone",
    "Hello hi hey good morning good afternoon greetings",
    "Thank you goodbye have a nice day",
    "I received the wrong item or my order is missing something",
    "How do I use or care for this product",
]

SUPPORT_TOPICS = [
    "I need help with a technical issue or bug",
    "How do I set up or configure my account",
    "I forgot my password and need to reset it",
    "I want to upgrade or downgrade my subscription plan",
    "How do I cancel my subscription",
    "I have a billing question or payment issue",
    "Can I get a refund for my subscription",
    "How do I integrate with my existing tools",
    "I need help with the API or developer documentation",
    "Can I speak to a human support agent",
    "I want to report a bug or give feedback",
    "Hello hi hey good morning good afternoon greetings",
    "Thank you goodbye have a nice day",
]

SAAS_TOPICS = [
    "How do I get started with your product",
    "What features are included in each pricing tier",
    "How do I invite team members to my workspace",
    "I need help with the dashboard or analytics",
    "How do I export or import my data",
    "What integrations do you support",
    "I have a question about data privacy and security",
    "How do I set up single sign-on or SSO",
    "I need help with the API or webhooks",
    "Can I get a custom enterprise plan",
    "I have a billing or invoice question",
    "Can I speak to a sales representative",
    "Hello hi hey good morning good afternoon greetings",
    "Thank you goodbye have a nice day",
]

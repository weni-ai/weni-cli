# Broadcasts

## What Are Broadcasts?

Broadcasts allow your tools to send messages directly to the contact during execution, **before** the tool returns its response. This is useful when your tool performs a long-running operation and you want to keep the user informed, or when you need to send rich interactive messages like catalogs.

Think of broadcasts as a way for your tool to proactively talk to the user while it's working — instead of waiting until the end to respond.

## Why Broadcasts Matter

Broadcasts enable tools to:

- Send real-time progress updates during long-running operations
- Deliver rich interactive messages like product catalogs
- Provide quick reply options to guide the conversation
- Send multiple messages in a single tool execution
- Keep users engaged and informed throughout the process

## Quick Start

To send a broadcast, call `self.send_broadcast()` inside your tool's `execute` method with a message object:

```python
from weni import Tool
from weni.context import Context
from weni.broadcasts import Text
from weni.responses import FinalResponse

class MyTool(Tool):
    def execute(self, context: Context) -> FinalResponse:
        self.send_broadcast(Text(text="Processing your request..."))
        return FinalResponse()
```

The `send_broadcast` method is available on every `Tool` instance. It sends the message immediately to the contact.

## Dict Shorthand

All message types that accept nested objects (catalogs, payments) support **dict shorthand**. Instead of importing auxiliary classes, you can pass plain dictionaries:

```python
# Instead of this:
from weni.broadcasts import OneClickPayment, OrderItem

self.send_broadcast(OneClickPayment(
    ...,
    items=[OrderItem(retailer_id="SKU-1", name="Shirt", amount=15000)],
))

# You can do this (no extra imports):
from weni.broadcasts import OneClickPayment

self.send_broadcast(OneClickPayment(
    ...,
    items=[{"retailer_id": "SKU-1", "name": "Shirt", "amount": 15000}],
))
```

Dicts are automatically converted internally. This works for all nested fields across `WhatsAppCatalog`, `WeniWebChatCatalog`, `OneClickPayment`, and `PixPayment`.

## Message Types

The broadcasts module provides several message types, each suited for different use cases.

### `Text`

A simple text message.

```python
from weni.broadcasts import Text

self.send_broadcast(Text(text="Hello! How can I help you?"))
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | `str` | Yes | The message text content |

---

### `QuickReply`

A message with quick reply buttons that the user can tap to respond.

```python
from weni.broadcasts import QuickReply

self.send_broadcast(QuickReply(
    text="Do you want to continue?",
    options=["Yes", "No", "Maybe"],
    header="Question",
    footer="Tap to select",
))
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | `str` | Yes | The message text |
| `options` | `list[str]` | No | List of quick reply button labels |
| `header` | `str` | No | Optional header text displayed above the message |
| `footer` | `str` | No | Optional footer text displayed below the message |

---

### `WhatsAppCatalog`

A lightweight catalog message that only requires product retailer IDs — the channel resolves the full product details on its own. Ideal for channels that natively support product catalogs.

```python
from weni.broadcasts import WhatsAppCatalog

self.send_broadcast(WhatsAppCatalog(
    text="Here are our shirts",
    products=[
        {"product": "Workshirt Titan Coyote", "product_retailer_ids": ["12552#1#1", "12553#1#1"]},
        {"product": "Sports Collection", "product_retailer_ids": ["12600#1#1", "12601#1#1"]},
    ],
    header="Our Store",
    footer="Tap a product to view details",
))
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | `str` | Yes | Body text displayed with the catalog |
| `products` | `list[dict]` | No | List of product groups (see below) |
| `action_button_text` | `str` | No | Label for the catalog action button (default: `"Comprar"`) |
| `send_catalog` | `bool` | No | Whether to send the full catalog (default: `False`) |
| `header` | `str` | No | Optional header text |
| `footer` | `str` | No | Optional footer text |

**Product group dict fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `product` | `str` | Yes | The product group/category name |
| `product_retailer_ids` | `list[str]` | Yes | List of product retailer ID strings |

---

### `WeniWebChatCatalog`

A rich catalog message that carries full product details (name, price, image, etc.) so the channel can render complete product cards. Use this when the channel does not natively resolve product information from retailer IDs alone.

```python
from weni.broadcasts import WeniWebChatCatalog

self.send_broadcast(WeniWebChatCatalog(
    text="Here are our products",
    products=[{
        "product": "Shirts",
        "product_retailer_info": [
            {
                "name": "Blue Shirt",
                "price": "149.90",
                "retailer_id": "85961",
                "seller_id": "1",
                "description": "Premium cotton blue shirt",
                "image": "https://example.com/images/blue-shirt.jpg",
                "product_url": "https://store.com/blue-shirt",
            },
            {
                "name": "Red Shirt",
                "price": "129.90",
                "retailer_id": "85962",
                "seller_id": "1",
                "sale_price": "99.90",
            },
        ],
    }],
    header="Our Store",
    footer="Tap a product to view details",
    action_button_text="Buy Now",
))
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | `str` | Yes | Body text displayed with the catalog |
| `products` | `list[dict]` | No | List of product groups with full product details |
| `action_button_text` | `str` | No | Label for the catalog action button (default: `"Comprar"`) |
| `send_catalog` | `bool` | No | Whether to send the full catalog (default: `False`) |
| `header` | `str` | No | Optional header text |
| `footer` | `str` | No | Optional footer text |

**Product dict fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `str` | Yes | Product display name |
| `price` | `str` | Yes | Product price (e.g. `"149.90"`) |
| `retailer_id` | `str` | Yes | Unique product retailer identifier |
| `seller_id` | `str` | Yes | Seller identifier |
| `currency` | `str` | No | Currency code (default: `"BRL"`) |
| `description` | `str` | No | Product description |
| `image` | `str` | No | URL to the product image |
| `sale_price` | `str` | No | Discounted sale price, if applicable |

---

### `OneClickPayment`

Sends an order confirmation with a saved card for one-click payment via WhatsApp.

```python
from weni.broadcasts import OneClickPayment

self.send_broadcast(OneClickPayment(
    text="We found a saved card. Use it to complete payment?",
    reference_id="ORDER-123",
    last_four_digits="4242",
    credential_id="acc_001",
    total_amount=15000,
    items=[
        {"retailer_id": "SKU-1", "name": "Shirt", "amount": 10000, "quantity": 1},
        {"retailer_id": "SKU-2", "name": "Socks", "amount": 2500, "quantity": 2},
    ],
    subtotal=15000,
    tax_value=500,
    discount_value=1000,
    shipping_value=800,
))
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | `str` | Yes | Message text displayed to the contact |
| `reference_id` | `str` | Yes | Order reference ID |
| `last_four_digits` | `str` | Yes | Last four digits of the saved card |
| `credential_id` | `str` | Yes | Account/credential ID for the saved card |
| `total_amount` | `int` | Yes | Total amount in cents |
| `items` | `list[dict]` | No | Order items (see item fields below) |
| `subtotal` | `int` | No | Subtotal in cents (default: `0`) |
| `tax_value` | `int` | No | Tax in cents (default: `0`) |
| `discount_value` | `int` | No | Discount in cents (default: `0`) |
| `shipping_value` | `int` | No | Shipping in cents (default: `0`) |

---

### `PixPayment`

Sends an order details message with PIX payment configuration, allowing the contact to copy the PIX code and complete payment.

```python
from weni.broadcasts import PixPayment

self.send_broadcast(PixPayment(
    text="Copy the PIX code below to complete payment.",
    reference_id="1484830849478-01",
    pix_key="7d4e8f2a-3b1c-4d5e-9f6a-8b7c2d1e0f3a",
    pix_key_type="EVP",
    merchant_name="CITEROL LTDA",
    pix_code="00020126580014br.gov.bcb.pix...",
    total_amount=34990,
    items=[
        {"retailer_id": "31245#1", "name": "Nike Air Max 90", "amount": 24990},
        {"retailer_id": "78432#1", "name": "Meia Esportiva", "amount": 2500, "quantity": 2},
    ],
    subtotal=29990,
    discount_value=1500,
    shipping_value=6500,
    footer="Obrigado pela preferencia",
))
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | `str` | Yes | Message text displayed to the contact |
| `reference_id` | `str` | Yes | Order reference ID |
| `pix_key` | `str` | Yes | PIX key |
| `pix_key_type` | `str` | Yes | PIX key type (`EVP`, `CPF`, `CNPJ`, etc.) |
| `merchant_name` | `str` | Yes | Merchant display name |
| `pix_code` | `str` | Yes | Full PIX copy-paste code |
| `total_amount` | `int` | Yes | Total amount in cents |
| `items` | `list[dict]` | No | Order items (see item fields below) |
| `subtotal` | `int` | No | Subtotal in cents (default: `0`) |
| `tax_value` | `int` | No | Tax in cents (default: `0`) |
| `discount_value` | `int` | No | Discount in cents (default: `0`) |
| `shipping_value` | `int` | No | Shipping in cents (default: `0`) |
| `footer` | `str` | No | Optional footer text |

---

### `WhatsAppFlows`

Sends a WhatsApp Flows interactive message that opens a structured flow screen for the contact.

```python
from weni.broadcasts import WhatsAppFlows

self.send_broadcast(WhatsAppFlows(
    text="You have a pending confirmation.",
    flow_id="1451561746318256",
    flow_cta="Confirm Now",
    flow_screen="COLLECT_DATA",
    flow_data={"order_value": "R$ 150,00", "card_last_four": "1234"},
    flow_token="optional-token-123",
))
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | `str` | Yes | Message text displayed to the contact |
| `flow_id` | `str` | Yes | WhatsApp Flow ID |
| `flow_cta` | `str` | Yes | Call-to-action button text |
| `flow_screen` | `str` | Yes | Initial screen to display |
| `flow_token` | `str` | No | Optional flow token |
| `flow_data` | `dict` | No | Data to pass to the flow (default: `{}`) |
| `flow_mode` | `str` | No | Flow mode: `"published"` or `"draft"` (default: `"published"`) |

## Sending Multiple Messages

Call `self.send_broadcast()` multiple times to send more than one message during a single tool execution:

```python
from weni.broadcasts import Text, QuickReply

class MyTool(Tool):
    def execute(self, context: Context):
        self.send_broadcast(Text(text="Step 1: Fetching your data..."))
        self.send_broadcast(Text(text="Step 2: Processing results..."))
        self.send_broadcast(QuickReply(
            text="All done! What would you like to do next?",
            options=["View Details", "Start Over"],
        ))
        return FinalResponse()
```

## Complete Example

Here is a full example of a tool that searches for products and sends a catalog broadcast to the contact:

```python
from weni import Tool
from weni.context import Context
from weni.responses import TextResponse, FinalResponse
from weni.broadcasts import Text, WhatsAppCatalog, WeniWebChatCatalog


class SendProductCatalog(Tool):
    def execute(self, context: Context) -> FinalResponse:
        category = context.parameters.get("category", "")
        contact_urn = context.contact.get("urn", "")

        self.send_broadcast(Text(text=f"Searching products in {category}..."))

        products = self.fetch_products(category, context)

        if not products:
            return TextResponse(data={"error": "No products found"})

        if contact_urn.startswith("whatsapp:"):
            self.send_broadcast(WhatsAppCatalog(
                text=f"Products in {category}:",
                products=[{"product": category, "product_retailer_ids": [p["id"] for p in products]}],
            ))
        else:
            self.send_broadcast(WeniWebChatCatalog(
                text=f"Products in {category}:",
                products=[{
                    "product": category,
                    "product_retailer_info": [
                        {"name": p["name"], "price": p["price"], "retailer_id": p["id"], "seller_id": "1", "image": p.get("image")}
                        for p in products
                    ],
                }],
            ))

        return FinalResponse()

    def fetch_products(self, category, context):
        api_key = context.credentials.get("api_key")
        return [
            {"name": "Product A", "price": "99.90", "id": "001", "image": "https://..."},
            {"name": "Product B", "price": "149.90", "id": "002", "image": "https://..."},
        ]
```

## Best Practices

When working with broadcasts:

1. **Use dict shorthand**: Pass nested objects as plain dicts to keep your imports minimal — only import the message type itself
2. **Use broadcasts for real-time feedback**: Send progress messages during long-running operations so the user knows the tool is working
3. **Choose the right catalog type**: Use `WhatsAppCatalog` when the channel natively resolves product details from retailer IDs, and `WeniWebChatCatalog` when full product details need to be provided explicitly
4. **Detect the channel from the contact URN**: Check `context.contact.get("urn")` to determine the contact's channel and send the appropriate message type
5. **Keep broadcasts concise**: Avoid flooding the user with too many messages — only send what is necessary
6. **Use FinalResponse when appropriate**: If the broadcast is the primary output of your tool, return `FinalResponse()` instead of `TextResponse` to avoid duplicate information. See the [FinalResponse](./final-response.md) documentation for more details

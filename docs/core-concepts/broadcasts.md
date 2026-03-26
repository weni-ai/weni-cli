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
from weni.broadcasts import WhatsAppCatalog, WhatsAppProductGroup

self.send_broadcast(WhatsAppCatalog(
    text="Here are our shirts",
    products=[
        WhatsAppProductGroup(
            product="Workshirt Titan Coyote",
            product_retailer_ids=["12552#1#1", "12553#1#1"],
        ),
        WhatsAppProductGroup(
            product="Sports Collection",
            product_retailer_ids=["12600#1#1", "12601#1#1", "12602#1#1"],
        ),
    ],
    header="Our Store",
    footer="Tap a product to view details",
))
```

#### `WhatsAppCatalog` Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | `str` | Yes | Body text displayed with the catalog |
| `products` | `list[WhatsAppProductGroup]` | No | List of product groups to display |
| `action_button_text` | `str` | No | Label for the catalog action button (default: `"Comprar"`) |
| `send_catalog` | `bool` | No | Whether to send the full catalog (default: `False`) |
| `header` | `str` | No | Optional header text |
| `footer` | `str` | No | Optional footer text |

#### `WhatsAppProductGroup` Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `product` | `str` | Yes | The product group/category name |
| `product_retailer_ids` | `list[str]` | No | List of product retailer ID strings |

---

### `WeniWebChatCatalog`

A rich catalog message that carries full product details (name, price, image, etc.) so the channel can render complete product cards. Use this when the channel does not natively resolve product information from retailer IDs alone.

```python
from weni.broadcasts import WeniWebChatCatalog, WebChatProductGroup, WebChatProduct

self.send_broadcast(WeniWebChatCatalog(
    text="Here are our products",
    products=[
        WebChatProductGroup(
            product="Shirts",
            product_retailer_info=[
                WebChatProduct(
                    name="Blue Shirt",
                    price="149.90",
                    retailer_id="85961",
                    seller_id="1",
                    currency="BRL",
                    description="Premium cotton blue shirt",
                    image="https://example.com/images/blue-shirt.jpg",
                ),
                WebChatProduct(
                    name="Red Shirt",
                    price="129.90",
                    retailer_id="85962",
                    seller_id="1",
                    currency="BRL",
                    sale_price="99.90",
                ),
            ],
        ),
        WebChatProductGroup(
            product="Pants",
            product_retailer_info=[
                WebChatProduct(
                    name="Cargo Pants",
                    price="199.90",
                    retailer_id="85970",
                    seller_id="1",
                ),
            ],
        ),
    ],
    header="Our Store",
    footer="Tap a product to view details",
    action_button_text="Buy Now",
))
```

#### `WeniWebChatCatalog` Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | `str` | Yes | Body text displayed with the catalog |
| `products` | `list[WebChatProductGroup]` | No | List of product groups with full product details |
| `action_button_text` | `str` | No | Label for the catalog action button (default: `"Comprar"`) |
| `send_catalog` | `bool` | No | Whether to send the full catalog (default: `False`) |
| `header` | `str` | No | Optional header text |
| `footer` | `str` | No | Optional footer text |

#### `WebChatProductGroup` Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `product` | `str` | Yes | The product group/category name |
| `product_retailer_info` | `list[WebChatProduct]` | No | List of products with full details |

#### `WebChatProduct` Fields

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
from weni.broadcasts import (
    Text,
    WhatsAppCatalog,
    WhatsAppProductGroup,
    WeniWebChatCatalog,
    WebChatProductGroup,
    WebChatProduct,
)


class SendProductCatalog(Tool):
    def execute(self, context: Context) -> FinalResponse:
        category = context.parameters.get("category", "")
        contact_urn = context.contact.get("urn", "")

        self.send_broadcast(Text(text=f"Searching products in {category}..."))

        products = self.fetch_products(category, context)

        if not products:
            return TextResponse(data={"error": "No products found"})

        if self.channel_supports_native_catalog(contact_urn):
            self.send_lightweight_catalog(category, products)
        else:
            self.send_rich_catalog(category, products)

        return FinalResponse()

    def fetch_products(self, category, context):
        api_key = context.credentials.get("api_key")
        # Your product fetching logic here
        return [
            {"name": "Product A", "price": "99.90", "id": "001", "image": "https://..."},
            {"name": "Product B", "price": "149.90", "id": "002", "image": "https://..."},
        ]

    def channel_supports_native_catalog(self, urn: str) -> bool:
        # Determine if the channel resolves product details natively
        return urn.startswith("whatsapp:")

    def send_lightweight_catalog(self, category, products):
        self.send_broadcast(WhatsAppCatalog(
            text=f"Products in {category}:",
            products=[
                WhatsAppProductGroup(
                    product=category,
                    product_retailer_ids=[p["id"] for p in products],
                ),
            ],
        ))

    def send_rich_catalog(self, category, products):
        self.send_broadcast(WeniWebChatCatalog(
            text=f"Products in {category}:",
            products=[
                WebChatProductGroup(
                    product=category,
                    product_retailer_info=[
                        WebChatProduct(
                            name=p["name"],
                            price=p["price"],
                            retailer_id=p["id"],
                            seller_id="1",
                            image=p.get("image"),
                        )
                        for p in products
                    ],
                ),
            ],
        ))
```

## Error Handling

If a broadcast fails, you can catch the error and handle it gracefully:

```python
from weni.broadcasts import BroadcastSenderError

class MyTool(Tool):
    def execute(self, context: Context):
        try:
            self.send_broadcast(Text(text="Hello!"))
        except BroadcastSenderError as e:
            return TextResponse(data={"error": f"Broadcast failed: {e}"})

        return FinalResponse()
```

## Best Practices

When working with broadcasts:

1. **Use broadcasts for real-time feedback**: Send progress messages during long-running operations so the user knows the tool is working
2. **Choose the right catalog type**: Use `WhatsAppCatalog` when the channel natively resolves product details from retailer IDs, and `WeniWebChatCatalog` when full product details need to be provided explicitly
3. **Detect the channel from the contact URN**: Check `context.contact.get("urn")` to determine the contact's channel and send the appropriate message type
4. **Handle errors gracefully**: Wrap broadcast calls in try/except blocks when broadcast failure should not prevent the tool from returning a response
5. **Keep broadcasts concise**: Avoid flooding the user with too many messages — only send what is necessary
6. **Use FinalResponse when appropriate**: If the broadcast is the primary output of your tool, return `FinalResponse()` instead of `TextResponse` to avoid duplicate information. See the [FinalResponse](./final-response.md) documentation for more details

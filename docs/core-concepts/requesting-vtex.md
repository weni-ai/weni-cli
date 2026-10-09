# Requesting VTEX

## What Is requesting_vtex?

`self.requesting_vtex` lets your tools call private VTEX APIs during execution. The call goes through Retail's proxy — your tool passes the VTEX path and the HTTP method, and Retail resolves the store account, signs the request, and returns the parsed JSON.

Think of it as the way a requesting tool talks to VTEX: you never call VTEX IO yourself, and you never assemble Retail authentication.

## Why requesting_vtex Matters

`self.requesting_vtex` enables tools to:

- Read and write private VTEX APIs (OMS, catalog, checkout, and any other path the proxy accepts)
- Skip URL building, account resolution, and JWT signing
- Reuse the project token already present in the execution context
- Keep the same call style on every `Tool`, the way [broadcasts](./broadcasts.md) and [contacts](./contacts.md) do

## Quick Start

Call `self.requesting_vtex` inside `execute`. It is available on every `Tool`, created on first access, and cached for that execution.

```python
from weni import Tool
from weni.context import Context
from weni.responses import TextResponse

class GetOrdersTool(Tool):
    def execute(self, context: Context) -> TextResponse:
        orders = self.requesting_vtex(
            endpoint="api/oms/pvt/orders",
            method="GET",
            params={"f_status": "ready-for-handling"},
        )
        return TextResponse(data=orders)
```

You do not pass the VTEX account, the store domain, or a VTEX token. Retail reads the project from `context.project["auth_token"]` and forwards the call to `POST /vtex/proxy/`.

## Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `endpoint` | `str` | Yes | VTEX API path. A leading `/` is added if missing. Absolute `http(s)://` URLs are rejected. `path` is an alias; when both are passed, `path` wins. |
| `method` | `str` | No | `GET` (default), `POST`, `PUT`, or `PATCH`. Case-insensitive. `DELETE` is not supported. |
| `headers` | `dict` | No | Extra headers forwarded to VTEX. Not used to authenticate with Retail. |
| `data` | `dict` or `list` | No | JSON body for `POST`, `PUT`, or `PATCH`. An empty dict or list is still sent. |
| `params` | `dict` | No | Query parameters appended to the VTEX URL. |
| `merchant_name` | `str` | No | Seller account override. Retail allows it only when the project account lists that merchant as a VTEX seller. |

```python
self.requesting_vtex(
    endpoint="/api/oms/pvt/orders",
    method="POST",
    headers={"Accept": "application/json"},
    data={"customer": "user@example.com"},
    params={"an": "store"},
    merchant_name="selleraccount",
)
```

The return value is the parsed JSON from VTEX — an object or an array.

### How the call is sent

1. The path and method are validated before any network call.
2. Retail receives `POST https://retailsetup.weni.ai/vtex/proxy/` with `{"method": "...", "path": "/..."}` plus the optional fields you set.
3. Retail resolves the VTEX account for the project and forwards the call to VTEX IO.
4. The tool receives the JSON object or array.

A missing path, an empty path, an absolute URL, or a method other than `GET`, `POST`, `PUT`, or `PATCH` raises `VtexValidationError` and nothing is sent.

## Complete Example

A tool that lists orders ready for handling and returns them to the agent:

```python
from weni import Tool
from weni.context import Context
from weni.responses import TextResponse
from weni.vtex import VtexError, VtexHTTPError

class ListReadyOrders(Tool):
    def execute(self, context: Context) -> TextResponse:
        status = context.parameters.get("status", "ready-for-handling")

        try:
            orders = self.requesting_vtex(
                endpoint="/api/oms/pvt/orders",
                method="GET",
                params={"f_status": status},
            )
        except VtexHTTPError as exc:
            return TextResponse(data={"error": exc.response_body, "status": exc.status_code})
        except VtexError as exc:
            return TextResponse(data={"error": str(exc)})

        return TextResponse(data={"orders": orders})
```

## Error Handling

All failures subclass `VtexError`:

```python
from weni.vtex import (
    VtexConfigError,
    VtexError,
    VtexHTTPError,
    VtexNetworkError,
    VtexResponseError,
    VtexValidationError,
)

try:
    self.requesting_vtex(endpoint="/api/oms/pvt/orders", method="GET")
except VtexValidationError:
    # Missing path, absolute URL, or unsupported method
    ...
except VtexHTTPError as exc:
    # exc.status_code, exc.response_body
    ...
except VtexConfigError:
    # Missing project auth token
    ...
except VtexNetworkError:
    ...
except VtexResponseError:
    ...
except VtexError:
    ...
```

| Error | When |
|-------|------|
| `VtexConfigError` | Missing `auth_token` in `context.project` |
| `VtexValidationError` | Missing path, empty path, absolute URL, or a method other than GET, POST, PUT, or PATCH |
| `VtexHTTPError` | Retail responds with a non-success status |
| `VtexNetworkError` | The request fails before a response is received |
| `VtexResponseError` | A success body is empty, not JSON, or not an object or array |

Raw `requests` exceptions are not leaked.

## Configuration

| Value | Where it comes from | Required |
|-------|---------------------|----------|
| Auth token | `context.project["auth_token"]` | Yes |
| Retail base URL | `retail_url` in `project`, then `credentials`, then `globals`, then the `RETAIL_BASE_URL` environment variable | No — defaults to `https://retailsetup.weni.ai` |

For a local [tool test](../run/tool-run.md), pass both on the test's `project` block.

## Order helpers

`self.get_order`, `self.get_order_document`, and `self.search_orders` cover the three order calls tools make most often. Call them directly on the tool. You pass an order id or a search query — not a VTEX path.

```python
order = self.get_order(order_id)
document = self.get_order_document(order_id)
matches = self.search_orders("?q=user@email.com")
```

| Access | What it loads |
|--------|----------------|
| `self.get_order(order_id)` | One OMS order: `GET /api/oms/pvt/orders/{order_id}` |
| `self.get_order_document(order_id)` | The order document: `GET /api/orders/pvt/document/{order_id}` |
| `self.search_orders(raw_query)` | An order search: `POST /vtex/orders/` with `{"raw_query": "..."}` |

`self.get_order` and `self.get_order_document` go through the same proxy as `self.requesting_vtex`. `self.search_orders` does not: Retail forwards `raw_query` to VTEX IO `/get-orders`.

When a call needs custom headers, a body, or query parameters, use `self.requesting_vtex` instead.

### get_order

```python
order = self.get_order("v1234567890-01")
order = self.get_order("v1234567890-01", merchant_name="selleraccount")
```

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `order_id` | `str` | Yes | VTEX order id. Leading and trailing whitespace is stripped. |
| `merchant_name` | `str` | No | Seller account override, same rule as `self.requesting_vtex`. |

The id is rejected when it is empty or contains `/`, `\`, `?`, `#`, or whitespace. A valid id is quoted before it is placed in the path.

### get_order_document

Same arguments and id rules as `self.get_order`. The path is the order document, not the OMS order.

```python
document = self.get_order_document("v1234567890-01")
document = self.get_order_document("v1234567890-01", merchant_name="selleraccount")
```

### search_orders

```python
matches = self.search_orders("?q=user@email.com")
matches = self.search_orders("q=user@email.com")  # sent as ?q=user@email.com
matches = self.search_orders("?q=user@email.com&f_status=ready-for-handling")
```

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `raw_query` | `str` | Yes | OMS query string forwarded as Retail `raw_query`. |

An empty query raises `VtexValidationError`. A query without a leading `?` is prefixed. The string is not re-encoded — you own the characters inside it, including `+` in an email. `merchant_name` is not accepted on this call.

#### Raises (in addition to the proxy errors)

| Error | When |
|-------|------|
| `VtexValidationError` | Empty or unsafe `order_id`, or empty `raw_query` |

## Complete Example

A tool that loads one order, its document, and every order for the contact email:

```python
from weni import Tool
from weni.context import Context
from weni.responses import TextResponse
from weni.vtex import VtexError

class LookupOrder(Tool):
    def execute(self, context: Context) -> TextResponse:
        order_id = context.parameters.get("order_id")
        email = context.parameters.get("email")

        try:
            if order_id:
                return TextResponse(data={
                    "order": self.get_order(order_id),
                    "document": self.get_order_document(order_id),
                })

            return TextResponse(data={
                "orders": self.search_orders(f"?q={email}"),
            })
        except VtexError as exc:
            return TextResponse(data={"error": str(exc)})
```

## Best Practices

When working with VTEX:

1. **Use `self.requesting_vtex` for any VTEX path** that is not one of the three order helpers. Pass `endpoint` and `method`.
2. **Use the order helpers when you already have an id or a search query.** `self.get_order`, `self.get_order_document`, and `self.search_orders` are the calls to make — do not rebuild those paths yourself.
3. **Do not send account or token arguments.** The project JWT in the execution context is enough.
4. **Catch `VtexError`.** Return the failure in `TextResponse` so the agent can explain it instead of crashing the tool.
5. **Keep search queries as Retail expects them.** `?q=user@email.com` and extra OMS filters such as `f_status` go in the same `raw_query` string.

## Test Definition

Pass the Retail token and host on `project`. See [Tool Test Run](../run/tool-run.md) for `weni run`.

```yaml
tests:
    test_requesting_vtex:
        project:
            auth_token: "your-retail-jwt"
            retail_url: "https://retailsetup.weni.ai"
        parameters:
            status: "ready-for-handling"

    test_get_order:
        project:
            auth_token: "your-retail-jwt"
            retail_url: "https://retailsetup.weni.ai"
        parameters:
            order_id: "v1234567890-01"

    test_get_order_document:
        project:
            auth_token: "your-retail-jwt"
            retail_url: "https://retailsetup.weni.ai"
        parameters:
            order_id: "v1234567890-01"

    test_search_orders:
        project:
            auth_token: "your-retail-jwt"
            retail_url: "https://retailsetup.weni.ai"
        parameters:
            email: "user@email.com"
```

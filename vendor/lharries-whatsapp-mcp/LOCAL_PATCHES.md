# Local patches

This vendored snapshot is based on `lharries/whatsapp-mcp` under the MIT License.

Local distribution patch:

- The Go REST server is bound to `127.0.0.1` instead of all network interfaces.

Reason:

- The local kit is intended for personal Windows desktop use.
- Localhost binding reduces accidental LAN exposure of the bridge API.

Original upstream project:

```text
https://github.com/lharries/whatsapp-mcp
```


# aiohttp_proxy_connector

This library created to allow usage of different types of proxy, like Secure Web Proxy and Socks Proxy, with aiohttp library.
It only works with uvloop now due to inability of `loop.start_tls()` to start tls in tls connection with standard asyncio loop
(for updates on this you can check [this issue](https://bugs.python.org/issue37179)). Code for connection to socks proxy is taken from [this library](https://github.com/Skactor/aiohttp-proxy).

Requirements
------------
* aiohttp
* uvloop

Usage
-----
To use this library import `ProxyConnector` and use it in `aiohttp.ClientSession`. 
Then session can be used as any other aiohttp session:
```
from aiohttp_proxy_connector import ProxyConnector

async with aiohttp.ClientSession(connector=ProxyConnector()) as session:
    async with session.get(url, proxy=proxy_url) as response:
    ...
```
`ProxyConnector` inherits `TCPConnector`, so it has all the same parameters.
When passing `proxy_url` it can be with credentials in format
`https://username:password@host:port`, or without `https://host:port`.
Schemes that can be used are: `http`, `https`, `socks4`, `socks5`.
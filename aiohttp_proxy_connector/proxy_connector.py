from aiohttp import TCPConnector
from aiohttp.client_reqrep import ClientRequest
from aiohttp.helpers import BasicAuth
from aiohttp.client_proto import ResponseHandler
import asyncio
import base64
import time
import re
import ssl
from .helpers import create_socket_wrapper, parse_proxy_url, parse_response
from urllib.parse import unquote
from.errors import ProxyError


setattr(asyncio.sslproto._SSLProtocolTransport, "_start_tls_compatible", True)


class ProxyConnector(TCPConnector):
    def __init__(self, **kwargs):
        kwargs['force_close'] = True
        super(ProxyConnector, self).__init__(**kwargs)

    async def _create_socks_proxy_connection(self, req: "ClientRequest", _, timeout):
        proxy_type, host, port, username, password = parse_proxy_url(str(req.proxy))
        sock = create_socket_wrapper(
            loop=asyncio.get_running_loop(),
            proxy_type=proxy_type,
            host=host,
            port=port,
            username=unquote(username),
            password=unquote(password)
        )
        await sock.connect((req.host, req.port))
        if req.is_ssl():
            return await self._wrap_create_connection(
                self._factory,
                timeout=timeout,
                sock=sock.socket,
                ssl=ssl.SSLContext(),
                server_hostname=req.host,
                req=req
            )
        else:
            return await self._wrap_create_connection(
                self._factory,
                timeout=timeout,
                sock=sock.socket,
                req=req
            )

    async def _create_connection(self, req, traces, timeout) -> ResponseHandler:
        if req.proxy:
            if req.proxy.scheme.startswith('socks'):
                _, proto = await self._create_socks_proxy_connection(req, traces, timeout)
            else:
                _, proto = await self._create_proxy_connection(req, traces, timeout)
        else:
            _, proto = await self._create_direct_connection(req, traces, timeout)

        return proto

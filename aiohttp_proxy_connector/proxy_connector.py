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


def update_proxy_patch(
        self,
        proxy,
        proxy_auth,
        proxy_headers,
) -> None:
    if proxy_auth and not isinstance(proxy_auth, BasicAuth):
        raise ValueError("proxy_auth must be None or BasicAuth() tuple")
    self.proxy = proxy
    self.proxy_auth = proxy_auth
    self.proxy_headers = proxy_headers


ClientRequest.update_proxy = update_proxy_patch


class ProxyConnector(TCPConnector):
    def __init__(self, **kwargs):
        kwargs['force_close'] = True
        super(ProxyConnector, self).__init__(**kwargs)

    async def _create_https_proxy_connection(self, req, _, timeout):
        loop = asyncio.get_running_loop()
        proxy_auth = None
        if req.proxy.user:
            proxy_auth = 'Basic ' + (base64.standard_b64encode(f'{unquote(req.proxy.user)}:'
                                                               f'{unquote(req.proxy.password)}'.encode('latin1')
                                                               ).decode('latin1'))
            req.headers['Proxy-Authorization'] = proxy_auth
        proxy_context = ssl.SSLContext()
        transport, protocol = await loop.create_connection(self._factory,
                                                           host=req.proxy.host,
                                                           port=req.proxy.port,
                                                           ssl=proxy_context)
        if req.is_ssl():
            query = f'CONNECT {req.host}:{req.port} HTTP/1.1\r\n'
            if proxy_auth:
                query += f'Host: {req.proxy.host}\r\nProxy-Authorization: {proxy_auth}\r\n'
            query += '\r\n'
            transport.write(query.encode('latin1'))
            timer = time.time()
            while protocol._tail == b'':
                await asyncio.sleep(0.01)
                if time.time() - timer > timeout.total:
                    raise ProxyError('Proxy connection connection timeout: answer not received')
            status, message = parse_response(protocol._tail)
            if status != 200:
                raise ProxyError(f'Proxy connection error: {status} "{message}"')
            context = self._get_ssl_context(req)
            transport = await loop.start_tls(transport, protocol, context)
            protocol._tail = b''
            protocol.transport = transport
        return transport, protocol

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
            if req.proxy.scheme == 'https':
                _, proto = await self._create_https_proxy_connection(req, traces, timeout)
            elif req.proxy.scheme.startswith('socks'):
                _, proto = await self._create_socks_proxy_connection(req, traces, timeout)
            else:
                _, proto = await self._create_proxy_connection(req, traces, timeout)
        else:
            _, proto = await self._create_direct_connection(req, traces, timeout)

        return proto

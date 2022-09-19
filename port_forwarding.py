#!/usr/bin/env python3

import socket
import argparse
import logging
import traceback
import asyncio
import selectors


lhost = '0.0.0.0'       # Default server host (to bind)
lport = 9090            # Default server port.
dhost = '127.0.0.1'     # Default destination host.
dport = 22              # Default destination port.
BUFFER_SIZE = 4096      # Default buffer size.
fake_websocket_reply = False

# Setting up the logger
fmt = "%(asctime)s - [%(levelname)s]: %(message)s"
logging.basicConfig(level=logging.DEBUG, format=fmt)
logger = logging.getLogger(__file__)

# Change the default event loop!
selector = selectors.SelectSelector()
loop = asyncio.SelectorEventLoop(selector)
asyncio.set_event_loop(loop)


async def websocket_upgrade(client):
    """return a fake websocket reply"""
    loop = asyncio.get_event_loop()

    buffer = await loop.sock_recv(client, BUFFER_SIZE)
    if buffer:
        await loop.sock_sendall(
            client, "HTTP/1.1 101 Switching Protocols (Python)\r\nContent-Length: 1048576000000\r\n\r\n".encode('utf-8'))
        logger.info('Websocket upgraded!')


async def tunnel(src, dst):
    loop = asyncio.get_event_loop()
    while True:
        buffer = await loop.sock_recv(src, BUFFER_SIZE)
        if buffer:
            await loop.sock_sendall(dst, buffer)
        else:
            break
    logger.info('Connection terminated!')


async def accept(server):
    '''Accept server connection'''
    loop = asyncio.get_event_loop()

    client, addr = await loop.sock_accept(server)
    client.setblocking(False)
    # Establishing a cennection to destination.
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.setblocking(False)
    await loop.sock_connect(conn, (dhost, dport))

    logger.info(
        f'Connection established: {client.getsockname()} -> ? -> {conn.getpeername()}')

    # Fake Websocket upgrade
    websocket_handshake = False
    if fake_websocket_reply and not websocket_handshake:
        await websocket_upgrade(client)
        websocket_handshake = True

    # piping data
    loop.create_task(tunnel(client, conn))
    loop.create_task(tunnel(conn, client))


async def server(lhost, lport, dhost, dport):
    loop = asyncio.get_event_loop()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.setblocking(False)
        server.bind((lhost, lport))
        server.listen()

        logger.info(f'Server started on {lhost}:{lport}')
        while True:
            try:
                while True:
                    await accept(server)

            except ConnectionRefusedError:
                logger.error('Destination connection refused.')
            except OSError:
                logger.error('socket.connect() error!')
                logger.error(traceback.format_exc())
            except Exception:
                logger.error(traceback.format_exc())


if __name__ == '__main__':
    # Get arguments from terminal.
    parser = argparse.ArgumentParser(
        description="A Simple and Great Port forwarding script :D",
        usage=f"%(prog)s --server {lport} --target {dhost}:{dport}"
    )
    parser.add_argument('--server', metavar='', required=True,
                        help='A port, for a server to liston on.', default=f'{lhost}:{lport}')

    parser.add_argument('--target', metavar='', required=True,
                        help='Distination, e.g: 127.0.0.1:20 or 10.0.0.5:3306')
    parser.add_argument('--fake-ws-reply', action='store_true',
                        help='return "HTTP/1.1 101 Switching Protocol" for a fake Websocket upgrade reply\n (useful for HTTP Custom & HTTP Injector)!')

    args = parser.parse_args()

    # Override default params
    if ':' in args.server:
        shost, sport = args.server.split(':')
        lhost = shost if shost else lhost
        lport = int(sport) if sport else lport
    else:
        lport = int(args.server)

    if ':' in args.target:
        host, port = args.target.split(':')
        dhost = host if host else dhost
        dport = int(port) if port else dport
    else:
        dport = int(args.target)

    fake_websocket_reply = args.fake_ws_reply

    logger.info(f"tunnel: {lhost}:{lport} --> {dhost}:{dport}")
    try:
        # start a server.
        asyncio.run(server(lhost, lport, dhost, dport))
    except KeyboardInterrupt:
        logger.info('Server closed')

#!/usr/bin/env python3

import socket
import argparse
import threading
import logging


lhost = '0.0.0.0'		# Default server host (to bind)
lport = 9090 			# Default server port.
dhost = '127.0.0.1' 	# Default destination host.
dport = 22 				# Default destination port.
BUFFER_SIZE = 4096 		# Default buffer size.

threads_list = set()  	# Save all theads

# Setting up the logger
fmt = "%(asctime)s - [%(levelname)s]: %(message)s"
logging.basicConfig(level=logging.DEBUG, format=fmt)
logger = logging.getLogger(__file__)


def forward(src, dst):
    while True:
        #logger.info('Threads:', threading.enumerate()[1:])
        buffer = src.recv(BUFFER_SIZE)
        if buffer:
            dst.sendall(buffer)
        else:
            break

    # Close socket connections
    try:
        src.shutdown(socket.SHUT_RDWR)
        src.close()

        dst.shutdown(socket.SHUT_RDWR)
        dst.close()

        logger.info('Connection closed.')
    except OSError:
        pass  # Connection already shutdown
    finally:
        threads_list.remove(threading.current_thread())


def server(lhost, lport, dhost, dport):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((lhost, lport))
        server.listen()

        logger.info(f'Server started on {lhost}:{lport}')

        try:
            while True:
                try:
                    client, src_addr = server.accept()
                    # Establishing a cennection to destination.
                    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    conn.connect((dhost, dport))
                    logger.info(
                        f'Connection established: {client.getsockname()} -> ? -> {conn.getpeername()}')

                    t1 = threading.Thread(
                        target=forward, args=(client, conn), daemon=True)
                    t2 = threading.Thread(
                        target=forward, args=(conn, client), daemon=True)

                    t1.start()
                    t2.start()

                    # Add new threads to the list
                    threads_list.add(t1)
                    threads_list.add(t2)

                except Exception as e:
                    logger.error(e)
        except KeyboardInterrupt:
            logger.info('Server closed')


if __name__ == '__main__':
    # Get arguments from terminal.
    parser = argparse.ArgumentParser(
        description="A Simple and Great Port forwarding script :D")
    parser.add_argument(
        '--server', metavar='', required=True, help='A port, for a server to liston on.', default=f'{lhost}:{lport}')

    parser.add_argument('--target', metavar='', required=True,
                        help='Distination, e.g: 127.0.0.1:20 or 10.0.0.5:3306')

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

    logger.info(f"tunnel: {lhost}:{lport} --> {dhost}:{dport}")
    # start a server.
    server(lhost, lport, dhost, dport)

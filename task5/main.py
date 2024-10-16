import argparse
import logging
import socket

import select

from network import ProxyClient


def setup_socket() -> socket.socket:
    sock = socket.socket(
        family=socket.AF_INET,
        type=socket.SOCK_STREAM,  # socket type (stream/datagram)
        proto=socket.IPPROTO_TCP  # protocol
    )

    # http://man.he.net/?topic=setsockopt&section=all
    # Set socket address to be reusable for testing purposes
    sock.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    sock.setblocking(False)
    sock.settimeout(60)

    return sock


if __name__ == "__main__":
    logging.basicConfig(
        format="[%(levelname)s]: %(message)s",
        level=logging.DEBUG
    )

    parser = argparse.ArgumentParser(
        prog="Task 5",
        description="SOCKS5 Proxy for Networking Sem.5"
    )

    parser.add_argument("port", type=int, default=5123)
    args = parser.parse_args()

    logging.info(f"Starting proxy on port {args.port}")

    server_socket = setup_socket()
    server_socket.bind(("0.0.0.0", args.port))
    server_socket.listen(0)

    logging.info("Proxy started.")

    proxy_clients = list()
    try:
        while True:
            potential_readers = [server_socket] + \
                                list(
                                    map(
                                        lambda x: x.proxy_server_socket,
                                        filter(
                                            lambda x: x.is_alive,
                                            proxy_clients
                                        )
                                    )
                                ) + \
                                list(
                                    filter(
                                        lambda x: x is not None,
                                        map(
                                            lambda x: x.proxy_destination_socket,
                                            filter(
                                                lambda x: x.is_alive,
                                                proxy_clients
                                            )
                                        )
                                    )
                                )
            readable_sockets, _, __ = select.select(
                potential_readers, [], []
            )

            # Add new clients
            if server_socket in readable_sockets:
                connection = server_socket.accept()
                client_socket, (cl_host, cl_port) = connection
                proxy_clients.append(
                    ProxyClient(client_socket, cl_host, cl_port)
                )
                logging.info(f"New client added. {cl_host}:{cl_port}")

            # Serve all clients
            to_be_removed = list()
            for proxy_client in proxy_clients:
                if not proxy_client.is_alive:
                    to_be_removed.append(proxy_client)
                    continue
                if proxy_client.proxy_server_socket in readable_sockets:
                    proxy_client.serve()
                if proxy_client.proxy_destination_socket in readable_sockets:
                    proxy_client.resend()

            for proxy_client in to_be_removed:
                proxy_clients.remove(proxy_client)

    except KeyboardInterrupt:
        logging.info("Stopping proxy.")
    finally:
        server_socket.close()
        for proxy_client in proxy_clients:
            proxy_client.close()
    logging.info("App has been stopped.")

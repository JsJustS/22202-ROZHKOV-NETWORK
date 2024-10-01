import argparse
from server import Server
from client import Client


def parse():
    parser = argparse.ArgumentParser(
        prog="Task 1",
        description="First Task for Networking Sem.5"
    )

    parser.add_argument('-i', '--ip', type=str, default="0.0.0.0")
    parser.add_argument('-p', '--port', type=int, default=5123)
    parser.add_argument('-f', '--file', type=str, default=None)
    return parser.parse_args()


def main():
    args = parse()
    if args.file is not None:
        app = Client(args.ip, args.port, input("Enter filepath: "))
    else:
        app = Server(args.port)
    app.start()


if __name__ == "__main__":
    main()

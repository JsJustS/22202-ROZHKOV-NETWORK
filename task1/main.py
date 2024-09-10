import time

from network import App
import threading


def receiver(this_app: App, this_observed: set, this_table: dict):
    while True:
        packet = app.receive_packet()
        this_table[packet.uuid] = time.time_ns()
        if packet.alive:
            if packet.uuid not in this_observed:
                print("+", packet.uuid)
                this_observed.add(packet.uuid)
        else:
            if packet.uuid == this_app.uuid:
                return
            if packet.uuid in this_observed:
                print("-", packet.uuid)
                this_observed.remove(packet.uuid)


def beacon_checker(this_app: App, this_observed: set, this_table: dict):
    timer = threading.Timer(this_app.delay * this_app.delay_modifier, beacon_checker, args=(this_app, this_observed, this_table))
    timer.start()

    current_ns = time.time_ns()
    to_be_removed = set()
    for uuid, last_packet_ns in this_table.items():
        died = current_ns - last_packet_ns > this_app.delay * 10e9
        if died:
            if uuid == this_app.uuid:
                timer.cancel()
                return
            print("-", uuid)
            to_be_removed.add(uuid)

    for uuid in to_be_removed:
        this_observed.remove(uuid)
        this_table.pop(uuid)


app = App()
app.start()

observed = set()
table = dict()

receiver_thread = threading.Thread(target=receiver, name="receiver-thread", args=(app, observed, table))
receiver_thread.start()
beacon_checker(app, observed, table)

while input() != "q":
    print("enter \"q\" to exit...")

app.die()

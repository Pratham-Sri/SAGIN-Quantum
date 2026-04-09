"""
Base controller module for SAGIN Simulator.
Provides connection and state parsing utilities.
"""

import socket
import time
import random

HOST = "127.0.0.1"
PORT = 9001
MAX_SPEED = 10.0

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

print("SAGIN Base Controller - Waiting for simulator...")

while True:
    try:
        s.connect((HOST, PORT))
        break
    except Exception:
        time.sleep(1)

print("Connected to simulator")

while True:
    try:
        data = s.recv(4096).decode()
    except Exception:
        print("Connection closed")
        break

    if not data:
        continue

    lines = data.strip().split("\n")

    for line in lines:
        if not line.startswith("STATE"):
            continue

        parts = line.split()

        t = float(parts[1])
        x = float(parts[2])
        y = float(parts[3])
        queue = int(parts[4])
        route = int(parts[5])

        print(f"State: t={t:.1f} x={x:.0f} y={y:.0f} "
              f"queue={queue} route={route}")

        # Simple proportional control
        dx = (500 - x) * 0.05
        dy = (500 - y) * 0.05
        dx = max(min(dx, MAX_SPEED), -MAX_SPEED)
        dy = max(min(dy, MAX_SPEED), -MAX_SPEED)

        s.send(f"MOVE {dx:.2f} {dy:.2f}\n".encode())

        # Route based on queue
        if queue > 20:
            s.send(b"ROUTE 1\n")
        else:
            s.send(b"ROUTE 0\n")

s.close()

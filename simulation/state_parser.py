"""
Shared utilities for all SAGIN controllers:
  - parse_state(): parse STATE message from ns-3
  - connect_to_sim(): robust connection with retry
  - recv_state(): blocking recv that reassembles partial messages
"""

import socket
import time
import numpy as np

STATE_DIM = 16


def parse_state(data: str):
    """
    Parse a STATE message. Returns float32 array (STATE_DIM,) or None.

    STATE token layout (space-separated):
      [0]STATE [1]time [2]x [3]y [4]queue [5]routeId [6]energy
      [7]load0 [8]load1 [9]load2 [10]load3 [11]load4 [12]load5
      [13]throughput [14]avgLatency [15]speed
    """
    for line in data.strip().split("\n"):
        if not line.startswith("STATE"):
            continue
        p = line.split()
        state = np.zeros(STATE_DIM, dtype=np.float32)
        if len(p) >= 16:
            state[0]  = float(p[2])    # x
            state[1]  = float(p[3])    # y
            state[2]  = float(p[4])    # queue
            state[3]  = float(p[6])    # energy
            state[4]  = float(p[7])    # load0  (UAV)
            state[5]  = float(p[8])    # load1
            state[6]  = float(p[9])    # load2
            state[7]  = float(p[10])   # load3
            state[8]  = float(p[11])   # load4
            state[9]  = float(p[12])   # load5
            state[10] = float(p[13])   # throughput
            state[11] = float(p[14])   # avg_latency
            state[12] = float(p[15])   # speed
            state[13] = float(p[5])    # routeId
            state[14] = float(p[1])    # time
            state[15] = 0.0
            return state
        elif len(p) >= 6:              # legacy short format
            state[0]  = float(p[2])
            state[1]  = float(p[3])
            state[2]  = float(p[4])
            state[13] = float(p[5])
            return state
    return None


def connect_to_sim(host="127.0.0.1", port=9001):
    """Connect to simulator with retries. Returns socket."""
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))
            s.settimeout(10.0)   # 10 s recv timeout — prevents hanging
            print("Connected to simulator")
            return s
        except OSError:
            try:
                s.close()
            except Exception:
                pass
            time.sleep(1)


def recv_state(sock):
    """
    Receive bytes from socket and return decoded string.
    Returns None on closed connection or timeout.
    """
    try:
        data = sock.recv(4096)
        if not data:
            return None
        return data.decode("utf-8", errors="ignore")
    except socket.timeout:
        return ""        # empty string → caller should retry
    except OSError:
        return None      # connection gone

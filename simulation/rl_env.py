import socket
import time
import numpy as np


class SaginEnv:
    """
    SAGIN Simulation Environment.
    Connects to the ns-3 simulator via TCP and provides
    an RL-compatible interface (state, action, reward).

    State vector (16 dims):
      [x, y, queue, energy, load0-5, throughput, avgLatency, speed, routeId]

    Actions:
      route_id (0-5): which node to route tasks to
      dx, dy: UAV velocity components
    """

    def __init__(self, host="127.0.0.1", port=9001):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        print("Waiting for simulator...")
        while True:
            try:
                self.sock.connect((self.host, self.port))
                break
            except Exception:
                time.sleep(1)

        print("Connected to simulator")

        self.prev_state = None
        self.prev_action = None
        self.episode_rewards = []

        # Normalization constants (for reward computation)
        self.L_MAX = 2.0       # max expected latency (s)
        self.T_MAX = 10.0      # max expected throughput (tasks/s)
        self.E_MAX = 5000.0    # max energy (J)

    def get_state(self):
        """Receive and parse expanded state from simulator."""
        try:
            data = self.sock.recv(4096).decode()
        except Exception:
            return None

        if not data:
            return None

        lines = data.strip().split("\n")

        for line in lines:
            if not line.startswith("STATE"):
                continue

            parts = line.split()

            if len(parts) < 16:
                # Backward compatibility with old format
                if len(parts) >= 6:
                    x = float(parts[2])
                    y = float(parts[3])
                    queue = int(parts[4])
                    route = int(parts[5])
                    state = np.array([
                        x, y, queue, 5000.0,
                        0, 0, 0, 0, 0, 0,
                        0, 0, 0, route,
                        0, 0
                    ], dtype=np.float32)
                    return state
                continue

            # Parse expanded state
            x = float(parts[2])
            y = float(parts[3])
            queue = int(parts[4])
            route = int(parts[5])
            energy = float(parts[6])
            load0 = float(parts[7])
            load1 = float(parts[8])
            load2 = float(parts[9])
            load3 = float(parts[10])
            load4 = float(parts[11])
            load5 = float(parts[12])
            throughput = float(parts[13])
            avg_latency = float(parts[14])
            speed = float(parts[15])

            state = np.array([
                x, y, queue, energy,
                load0, load1, load2, load3, load4, load5,
                throughput, avg_latency, speed, route,
                0, 0  # padding for 16 dims
            ], dtype=np.float32)

            return state

        return None

    def compute_reward(self, state):
        """
        Multi-objective normalized reward:
        R = -alpha * (latency/L_max) - beta * (1 - throughput/T_max)
            - gamma * (energy_consumed/E_max) + delta * deadline_factor
        """
        if state is None:
            return 0.0

        queue = state[2]
        energy = state[3]
        throughput = state[10]
        avg_latency = state[11]

        alpha = 0.4    # latency weight
        beta = 0.3     # throughput weight
        gamma = 0.2    # energy weight
        delta = 0.1    # queue penalty

        # Normalized latency penalty
        latency_penalty = alpha * min(avg_latency / self.L_MAX, 1.0)

        # Throughput reward (higher is better)
        throughput_reward = beta * min(throughput / self.T_MAX, 1.0)

        # Energy penalty (penalize energy consumption)
        energy_consumed = self.E_MAX - energy
        energy_penalty = gamma * min(energy_consumed / self.E_MAX, 1.0)

        # Queue penalty (penalize large queues)
        queue_penalty = delta * min(queue / 50.0, 1.0)

        reward = -latency_penalty + throughput_reward - energy_penalty - queue_penalty

        return reward

    def step(self, action):
        """
        Send action to simulator.
        action: (route_id, dx, dy)
        """
        route_id, dx, dy = action

        # Clamp velocity
        max_speed = 15.0
        dx = max(min(dx, max_speed), -max_speed)
        dy = max(min(dy, max_speed), -max_speed)

        try:
            move_cmd = f"MOVE {dx:.2f} {dy:.2f}\n"
            self.sock.send(move_cmd.encode())

            route_cmd = f"ROUTE {int(route_id)}\n"
            self.sock.send(route_cmd.encode())
        except Exception as e:
            print(f"Failed to send action: {e}")

    def close(self):
        self.sock.close()

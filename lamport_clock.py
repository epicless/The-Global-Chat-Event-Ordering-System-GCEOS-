class LamportClock:
    def __init__(self):
        self.time = 0  # Start at 0 as per Lamport's algorithm

    def increment(self):
        # Increment clock for local events (sending messages)
        self.time += 1
        return self.time

    def update(self, received_time):
        # Update clock when receiving messages: max(local, received) + 1
        self.time = max(self.time, received_time) + 1
        return self.time

    def get_time(self):
        return self.time
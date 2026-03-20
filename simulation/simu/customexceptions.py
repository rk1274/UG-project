class SimulationError(Exception):
    def __init__(self, message):
        super().__init__(message)

class FaultBlockingError(Exception):
    def __init__(self, robot_name, blocked_name):
        super().__init__("%s has critically faulted and is blocking %s. Simulation cannot proceed." % (robot_name, blocked_name))

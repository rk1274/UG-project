import random

import udptransmit
import entitywithinventory
import math
import customexceptions
import utils

class Robot(entitywithinventory.InventoryEntity):
    CHARGE_TIME = 50
    HALT_THRESHOLD = 10

    def __init__(self, name: str, x: int, y: int, fault_rate: float, use_battery: bool):
        self._x, self._y = x, y
        self._home_x, self._home_y = x, y

        self.wait_steps = 0
        self.movement_path = []
        self.target = None
        self.steps_halted = 0

        self.assigned_order = None
        self.current_task_id = None
        self.prio = None
        self._goal_visit_flag = None

        self.battery_level = 100.0
        self.payload_weight = 0.0
        self.BASE_DRAIN = 0.1    
        self.WEIGHT_FACTOR = 0.2

        self._use_battery = use_battery
        self._charging = False
        self._was_charging_last_step = False
        self.apply_charge_wait_upon_reaching_home = False

        self_fault_rate = fault_rate
        self._actuator_overheat_prob = self_fault_rate * 0.5
        self._critical_fault_prob = self_fault_rate * 0.05

        self._just_critically_faulted = False
        self.critically_faulted = False  # Permanent death
        self.actuators_faulted = False    # Temporary stall

        self.status_history = []

        self.num_faults = 0

        super().__init__(name, 1)

    def start_charging(self):
        """Initiates the charge cycle."""
        print(f"CHARGING {self.get_name()}")
        udptransmit.transmit_battery_charging(self._name)

        self.apply_charge_wait_upon_reaching_home = False
        self.clear_inventory()
        self.add_wait_steps(self.CHARGE_TIME)
        self._charging = True

    def decrement_wait_steps(self):
        """
        Decrements wait time. 
        RETURNS: True if the robot just finished waiting and is ready for reassignment.
        """
        if self.wait_steps == math.inf:
            return False

        self.wait_steps -= 1

        if self.wait_steps == 0:
            self.actuators_faulted = False

            if self._charging:
                self._charging = False
                self.battery_level = 100
                self._was_charging_last_step = True
                print("CHARGING COMPLETE", self.get_name())
                udptransmit.transmit_battery_level(self._name, self.battery_level)

            return True
        
        return False
    
    def deplete_battery(self, distance=1):
        """Calculates and subtracts battery based on weight"""
        if self.critically_faulted or not self._use_battery:
            return

        drain = distance * (self.BASE_DRAIN + (self.payload_weight * self.WEIGHT_FACTOR))
        self.battery_level = max(0, self.battery_level - drain)

        if self.battery_level < utils.BATTERY_THRESHOLD:
            self.apply_charge_wait_upon_reaching_home = True

        if self.battery_level <= 0:
            self.critically_faulted = True
            udptransmit.robot_dead(self._name)
            self._just_critically_faulted = True
            self.wait_steps = math.inf

            print("BATTERY CRITICALLY FAULTED for robot %s" % self._name)

        udptransmit.transmit_battery_level(self._name, self.battery_level)

    def has_faulted(self): return self.critically_faulted or self.actuators_faulted

    def is_charging(self): return self._charging or self.apply_charge_wait_upon_reaching_home

    def set_flag(self, flag: str): self._goal_visit_flag = flag

    def consume_flag(self):
        return_val = self._goal_visit_flag
        self._goal_visit_flag = None
        return return_val

    def get_position(self): return self._x, self._y

    def add_wait_steps(self, amt): self.wait_steps += amt

    def set_position(self, x, y):
        if self.wait_steps != 0:
            raise customexceptions.SimulationError("Cannot move a robot that is waiting")
        
        dist = abs(self._x - x) + abs(self._y - y)
        self.deplete_battery(dist)
        
        self.steps_halted = 0
        self._x = x
        self._y = y

    def increment_steps_halted(self):
        self.steps_halted = self.steps_halted + 1
        if self.steps_halted > 10:
            self.steps_halted = 0

    def set_target(self, target):
        self.target = target
        if target is None:
            self.prio = None

    def get_target(self): return self.target

    def interact_with_target(self):
        if self.get_position() != self.target.get_position():
            message = "Robot %s tried to interact with object %s, when they were not occupying the same cell."
            raise customexceptions.SimulationError(message % (self._name, self.target.get_name()))

        self.target.interact(self)

        self.target = None

    def is_at_target(self):
        if self.target is None:
            return False

        target_x, target_y = self.target.get_position()
        if (self._x == target_x) and (self._y == target_y):
            return True
        else:
            return False

    def get_name(self): return self._name

    def transmit_creation(self):
        udptransmit.transmit_robot_creation(self._name, self._x, self._y)

    def check_for_actuator_fault(self):
        """Checks if motors overheat. Returns True if a new fault occurred."""
        if not self.actuators_faulted and not self.critically_faulted and random.random() < self._actuator_overheat_prob:
            print("FAULT %s ACTUATOR OVERHEAT" % self._name)
            self.actuators_faulted = True
            self.wait_steps += 10
            self._just_critically_faulted = True
            self.num_faults += 1
            udptransmit.robot_temp_fault(self._name)

    def check_for_critical_fault(self):
        """Checks if robot is permanently broken."""
        if not self.critically_faulted and random.random() < self._critical_fault_prob:
            print("FAULT %s CRITICAL" % self._name)
            self.wait_steps = math.inf
            self._just_critically_faulted = True
            self.critically_faulted = True
            udptransmit.robot_dead(self._name)

    def __repr__(self):
        return self._name

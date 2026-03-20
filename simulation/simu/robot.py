import random

import udptransmit
import entitywithinventory
import math
import shelf
import orderstation
import customexceptions
import utils

class Robot(entitywithinventory.InventoryEntity):
    CHARGE_TIME = 50
    HALT_THRESHOLD = 10

    def __init__(self, name: str, x: int, y: int, max_inv_size: int, fault_rates: list):
        self._x, self._y = x, y
        self._home_x, self._home_y = x, y

        self.wait_steps = 0
        self._movement_path = []
        self._current_target = None
        self._steps_halted = 0
        
        self._assigned_order = None
        self._current_task_id = None
        self._prio = None
        self._goal_visit_flag = None

        self._battery_level = 100.0
        self._payload_weight = 0.0
        self.BASE_DRAIN = 0.1    
        self.WEIGHT_FACTOR = 0.2

        self._just_faulted = False

        self._charging = False
        self._was_charging_last_step = False

        self.battery_faulted_critical = False  # Permanent death
        self.battery_faulted_low = False       # Needs recharge
        self.sensors_faulted = False           # Permanent degradation
        self.actuators_faulted = False         # Temporary stall
        self.apply_charge_wait_upon_reaching_home = False

        super().__init__(name, max_inv_size)

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
                self._battery_level = 100
                self._was_charging_last_step = True
                print("CHARGING COMPLETE", self.get_name())
                udptransmit.transmit_battery_level(self._name, self._battery_level)

            return True
        
        return False
    
    def deplete_battery(self, distance=1):
        """Calculates and subtracts battery based on weight"""
        if self.battery_faulted_critical:
            return

        drain = distance * (self.BASE_DRAIN + (self._payload_weight * self.WEIGHT_FACTOR))
        self._battery_level = max(0, self._battery_level - drain)

        if self._battery_level < utils.BATTERY_THRESHOLD:
            self.apply_charge_wait_upon_reaching_home = True

        if self._battery_level <= 0:
            self.battery_faulted_critical = True
            self._just_faulted = True
            self.wait_steps = math.inf

            print("BATTERY CRITICALLY FAULTED for robot %s" % self._name)

        udptransmit.transmit_battery_level(self._name, self._battery_level)

    def has_critically_faulted(self): return self.battery_faulted_critical

    def get_battery_level(self): return self._battery_level
    
    def set_payload_weight(self, weight): self._payload_weight = weight

    def is_charging(self): return self._charging or self.apply_charge_wait_upon_reaching_home

    def set_task_id(self, id): self._current_task_id = id
    
    def get_task_id(self): return self._current_task_id

    def set_assigned_order(self, id_num): self._assigned_order = id_num

    def get_assigned_order(self): return self._assigned_order

    def set_flag(self, flag: str): self._goal_visit_flag = flag

    def consume_flag(self):
        return_val = self._goal_visit_flag
        self._goal_visit_flag = None
        return return_val

    def get_assigned_order(self): return self._assigned_order

    def get_position(self): return self._x, self._y

    def set_prio(self, prio): self._prio = prio

    def get_prio(self): return self._prio

    def add_wait_steps(self, amt): self.wait_steps += amt

    def get_wait_steps(self): return self.wait_steps

    def set_position(self, x, y):
        if self.wait_steps != 0:
            raise customexceptions.SimulationError("Cannot move a robot that is waiting")
        
        dist = abs(self._x - x) + abs(self._y - y)
        self.deplete_battery(dist)
        
        self._steps_halted = 0
        self._x = x
        self._y = y

    def increment_steps_halted(self):
        self._steps_halted = self._steps_halted + 1
        if self._steps_halted > 10:
            self._steps_halted = 0

    def get_steps_halted(self): return self._steps_halted

    def set_movement_path(self, path): self._movement_path = path

    def get_movement_path(self): return self._movement_path

    def set_target(self, target):
        self._current_target = target
        if target is None:
            self._prio = None

    def get_target(self): return self._current_target

    def interact_with_target(self):
        if self.get_position() != self._current_target.get_position():
            message = "Robot %s tried to interact with object %s, when they were not occupying the same cell."
            raise customexceptions.SimulationError(message % (self._name, self._current_target.get_name()))

        self._current_target.interact(self)

        self._current_target = None

    def is_at_target(self):
        if self._current_target is None:
            return False

        target_x, target_y = self._current_target.get_position()
        if (self._x == target_x) and (self._y == target_y):
            return True
        else:
            return False

    def get_name(self): return self._name

    def transmit_creation(self):
        udptransmit.transmit_robot_creation(self._name, self._x, self._y)

    def maybe_introduce_fault(self):
        # Battery fault - 2 types:
        # Low battery - robot must return to its home and becomes unavailable for a certain number of steps
        # Battery failure - robot breaks unrecoverable.
        # Actuator fault - robot cannot move for a certain number of steps - Models overheating
        # Sensor fault - robot cannot determine what is around it - Is permanent
        # The robot cannot take any actions if the battery has failed
        f0, f1, f2, f3 = False, False, False, False
        if self.battery_faulted_critical:
            return []
        if random.random() < self._battery_critical_fault_rate:
            self.battery_faulted_critical = True
            #print("FAULT %s BATTERY CRITICAL" % self._name)
            f0 = True
        else:
            if random.random() < self._battery_low_fault_rate and not self.battery_faulted:
                #print("FAULT %s BATTERY RECHARGE" % self._name)
                self.battery_faulted = True
                f1 = True
            if random.random() < self._actuator_fault_rate and not self.actuators_faulted:
                self.actuators_faulted = True
                #print("FAULT %s ACTUATOR OVERHEAT" % self._name)
                f2 = True
            if random.random() < self._sensor_fault_rate and not self.sensors_faulted:
                self.sensors_faulted = True
                #print("FAULT %s SENSOR FAILURE" % self._name)
                f3 = True
        return [f0, f1, f2, f3]


    def __repr__(self):
        return self._name

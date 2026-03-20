class RobotHome:
    def __init__(self, home_name: str, robot_name: str, x: int, y: int):
        self._x = x
        self._y = y
        self._name = home_name
        self._robot_name = robot_name

    def interact(self, obj):
        if obj.apply_charge_wait_upon_reaching_home:
            obj.start_charging()

        obj.set_amount_of_items_to_transfer_next_time(None)
        return

    def get_robot_name(self):
        return self._robot_name

    def get_name(self):
        return self._name

    def get_position(self):
        return self._x, self._y


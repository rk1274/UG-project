import entitywithinventory
import customexceptions
import udptransmit
import math
import orderDAG

class OrderStation(entitywithinventory.InventoryEntity):
    def __init__(self, x_pos: int, y_pos: int, name: str, warehouse):
        self._x = x_pos
        self._y = y_pos
        self._warehouse_ref = warehouse
        self._active_order = None
        super().__init__(name)

    def set_active_order(self, order: orderDAG.OrderDAG):
        self._active_order = order

    def transmit_creation(self):
        udptransmit.transmit_goal_creation(self._name, self._x, self._y)

    def interact(self, obj):
        items = obj.transfer_inventory()
        taskID = obj.current_task_id

        obj.payload_weight = 0.0
        obj.current_task_id = None

        print("recieved:",taskID, "for order:",self._active_order.get_id(), "from:", obj.get_name())

        self.receive_inventory(items, taskID)

        if "large" in items[0].get_name():
            for item in self.report_inventory():
                if not "large" in item.get_name():
                    raise customexceptions.SimulationError(f"Added a large after a medium/small for order {self._active_order.get_id()}. {item.get_name()}")

        for item in items:
            self._active_order.mark_completed(taskID)

        self._warehouse_ref.get_scheduler().schedule()

        if self._active_order.is_finished():
            self._warehouse_ref.get_scheduler().handle_complete_order(self._active_order)
            self.clear_inventory()

        flag_maybe = obj.consume_flag()
        if flag_maybe is not None:
            self._warehouse_ref.get_scheduler().add_flag(flag_maybe)

    def get_position(self):
        return self._x, self._y

    def get_name(self):
        return self._name

    def __repr__(self):
        return self._name

import customexceptions
import entitywithinventory
import udptransmit
import math
import orderDAG


class OrderStation(entitywithinventory.InventoryEntity):
    def __init__(self, x_pos: int, y_pos: int, name: str, warehouse):
        self._x = x_pos
        self._y = y_pos
        self._warehouse_ref = warehouse
        self._active_order = None
        super().__init__(name, math.inf)

    def set_active_order(self, order: orderDAG.OrderDAG):
        self._active_order = order

    def transmit_creation(self):
        udptransmit.transmit_goal_creation(self._name, self._x, self._y)

    def interact(self, obj):
        #print("Robot %s interacting with order station %s" % (obj.get_name(), self._name))
        items = obj.transfer_inventory()
        taskID = obj.get_task_id()
        #print("Order station %s recieved %s" % (self.get_name(), received))
        #print("Already had %s" % self._inventory)

        # TODO probably dont need to recieve the inventory.
        print("ITEMS: ", items)
        self.receive_inventory(items, taskID)

        print("recieved:",taskID, "for order:",self._active_order.get_id(), "from robot:", obj.get_name())

        # TODO is there even multiple items?
        for item in items:
            self._active_order.mark_completed(taskID)

        self._warehouse_ref.get_scheduler().schedule(self._warehouse_ref.get_total_steps())

        if self._active_order.is_finished():
            self._warehouse_ref.get_scheduler().handle_complete_order(
                                                                        self._warehouse_ref.get_order_manager(),
                                                                        self._warehouse_ref.get_total_steps(),
                                                                        self._active_order)
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

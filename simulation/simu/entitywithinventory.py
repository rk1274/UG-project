import customexceptions
import item
import math

import udptransmit
import copy

# Models an entity with a LIFO stack inventory, where items within the stack must follow a dependency
class InventoryEntity:
    def __init__(self, name: str):
        self._name = name
        self._inventory = []
        self._amount_items_transfer_next_time = None

    def add_item_to_inventory(self, item_to_add: item.Item):
        # print("Adding item to inv,",item_to_add)
        self._inventory.append(item_to_add)

        udptransmit.transmit_item_gained(self._name, item_to_add.get_name())

    def pop_item_from_inventory(self) -> item.Item:
        if len(self._inventory) == 0:
            raise customexceptions.SimulationError("Tried to pop from an empty inventory")
        popped_item = self._inventory.pop()
        udptransmit.transmit_item_lost(self._name, popped_item.get_name())
        
        return popped_item

    def clear_inventory(self):
        self._inventory = []
        udptransmit.transmit_clear_inventory(self._name)

    def set_amount_of_items_to_transfer_next_time(self, num):
        self._amount_items_transfer_next_time = num

    def transfer_inventory(self):
        if len(self._inventory) == 0:
            raise customexceptions.SimulationError("Tried to transfer an empty inventory")

        if self._amount_items_transfer_next_time is None:
            inventory_copy = copy.deepcopy(self._inventory)
            self._inventory = []
            udptransmit.transmit_clear_inventory(self._name)
            return inventory_copy
        else:
            transfer_inv = []
            for i in range(self._amount_items_transfer_next_time):
                transfer_inv.append(self.pop_item_from_inventory())
            self._amount_items_transfer_next_time = None
            transfer_inv.reverse()
            return transfer_inv

    def receive_inventory(self, items, id):
        for itm in items:
            self.add_item_to_inventory(itm)

    def report_inventory(self):
        return copy.deepcopy(self._inventory)
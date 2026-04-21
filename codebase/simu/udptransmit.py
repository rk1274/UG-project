import socket
import os
IP = "127.0.0.1"
PORT = 35891
SOCK = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
commands = {}


def send_udp_message(message: str):
    if os.environ["ROBOTSIM_TRANSMIT"] == "True":
        print("sending")
        SOCK.sendto(bytes(message, "utf-8"), (IP, PORT))


def transmit_start():
    message = '{"command":"START"}'
    send_udp_message(message)


def transmit_warehouse_size(x: int, y: int):
    message = '{"command":"WAREHOUSESIZE", "posX":%s, "posY":%s}' % (x, y)
    send_udp_message(message)


def transmit_robot_position(name: str, x: int, y: int):
    message = '{"command":"MOVEROBOT", "posX":%s, "posY":%s, "objName":"%s"}' % (x, y, name)
    send_udp_message(message)


def transmit_robot_creation(name: str, x: int, y: int):
    message = '{"command":"CREATEROBOT", "posX":%s, "posY":%s, "objName":"%s"}' % (x, y, name)
    send_udp_message(message)


def transmit_shelf_creation(name: str, item: str, x: int, y: int):
    message = '{"command":"CREATESHELF", "posX":%s, "posY":%s, "objName":"%s", "itemName":"%s"}' % (x, y, name, item)
    send_udp_message(message)


def transmit_goal_creation(name: str, x: int, y: int):
    message = '{"command":"CREATEGOAL", "posX":%s, "posY":%s, "objName":"%s"}' % (x, y, name)
    send_udp_message(message)


def transmit_item_existence(name: str):
    message = '{"command":"ITEM", "itemName":"%s"}' % name
    send_udp_message(message)


def transmit_item_gained(objname: str, item_name: str):
    message = '{"command":"ITEMGAINED", "objName":"%s", "itemName":"%s"}' % (objname, item_name)
    send_udp_message(message)

def transmit_item_lost(objname: str, item_name: str):
    message = '{"command":"ITEMLOST", "objName":"%s", "itemName":"%s"}' % (objname, item_name)
    send_udp_message(message)

def transmit_clear_inventory(objname: str):
    message = '{"command":"CLEARINV", "objName":"%s"}' % objname
    send_udp_message(message)

def transmit_battery_level(robot_name: str, battery_level: float):
    message = '{"command":"BATTERYLEVEL", "objName":"%s", "batteryLevel":"%.2f"}' % (robot_name, battery_level)
    send_udp_message(message)

def transmit_battery_charging(robot_name: str):
    message = '{"command":"BATTERYCHARGING", "objName":"%s"}' % robot_name
    send_udp_message(message)

def robot_waiting(robot_name: str):
    message = '{"command":"ROBOTWAITING", "objName":"%s"}' % robot_name
    send_udp_message(message)
    
def robot_active(robot_name: str):
    message = '{"command":"ROBOTACTIVE", "objName":"%s"}' % robot_name
    send_udp_message(message)

def robot_dead(robot_name: str):
    message = '{"command":"ROBOTDEAD", "objName":"%s"}' % robot_name
    send_udp_message(message)

def robot_temp_fault(robot_name: str):
    message = '{"command":"ROBOTFAULT", "objName":"%s"}' % robot_name
    send_udp_message(message)

def transmit_num_orders(num_orders: int):
    message = '{"command":"NUMORDERS", "objName":"%s"}' % num_orders
    send_udp_message(message)

def transmit_order_complete():
    message = '{"command":"ORDERCOMPLETE"}'
    send_udp_message(message)

def transmit_step(step_num: int):
    message = '{"command":"STEPNUM", "objName":"%s"}' % step_num
    send_udp_message(message)




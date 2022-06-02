import asyncio
import json

import websockets
import websockets_routes
import pickle
import sys
import os
import glob

# ==============================================================================
# -- Find CARLA module ---------------------------------------------------------
# ==============================================================================
try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

# ==============================================================================
# -- Add PythonAPI for release mode --------------------------------------------
# ==============================================================================
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/carla')
except IndexError:
    pass

import carla
from carla import ColorConverter as cc

from agents.navigation.behavior_agent import BehaviorAgent  # pylint: disable=import-error
from agents.navigation.basic_agent import BasicAgent  # pylint: disable=import-error

router = websockets_routes.Router()
global server_agent

@router.route("/init")
async def init(websocket, path):
    async for message in websocket:
        dict_data = json.loads(message)
        past_steering = dict_data['past_steering']
        location = carla.Location(dict_data['location_x'], dict_data['location_y'], dict_data['location_z'])
        global server_agent
        server_agent = BehaviorAgent(past_steering, location, behavior="normal")
        # Set the agent destination

@router.route("/control")
async def control(websocket, path):
    async for message in websocket:
        dict_data = json.loads(message)
        print(message)
        vehicle_speed = dict_data['vehicle_speed']
        current_speed = vehicle_speed * 3.6
        speed_limit = dict_data['speed_limit']

        location = carla.Location(dict_data['location_x'], dict_data['location_y'], dict_data['location_z'])

        transform = carla.Transform()
        transform_location = carla.Location(dict_data['trans_location_x'], dict_data['trans_location_y'], dict_data['trans_location_z'])
        transform_rotation = carla.Rotation(dict_data['trans_rotation_pitch'], dict_data['trans_rotation_yaw'], dict_data['trans_rotation_roll'])
        transform.location = transform_location
        transform.rotation = transform_rotation

        global server_agent
        control = server_agent.run_step(location, vehicle_speed, current_speed, transform, speed_limit)
        # control = {"throttle": 0.5, "steer": 0.000000, "brake": 0.000000, "hand_brake": False, "reverse": False, "manual_gear_shift": False, "gear": 0}
        print(control)
        response_data = dict()
        response_data['throttle'] = control.throttle
        response_data['steer'] = control.steer
        response_data['brake'] = control.brake
        response_data['hand_brake'] = control.hand_brake
        response_data['reverse'] = control.reverse
        response_data['manual_gear_shift'] = control.manual_gear_shift
        response_data['gear'] = control.gear
        message = json.dumps(response_data)
        print(message)
        await websocket.send(message)


async def main():
    async with websockets.serve(lambda x, y: router(x, y), "127.0.0.1", 8765):
        print("======")
        await asyncio.Future()

if __name__ == '__main__':
    asyncio.run(main())
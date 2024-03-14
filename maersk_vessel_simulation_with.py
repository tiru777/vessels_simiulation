import simpy
import random

SIMULATION_TIME = 720  # Simulation time in minutes (24 hours)
NUM_TRUCKS = 3
NUM_BERTHS = 2
NUM_CRANES = 2
CONTAINERS_PER_VESSEL = 150
CONTAINER_MOVE_TIME = 3
TRUCK_MOVE_TIME = 6
BERTH_AVAILABLE = 1


class ContainerMaersk:

    def __init__(self, env):
        self.env = env
        self.berths = simpy.Resource(env, capacity=NUM_BERTHS)
        self.cranes = simpy.Resource(env, capacity=NUM_CRANES)
        self.trucks = simpy.Resource(env, capacity=NUM_TRUCKS)
        self.waiting_vessels = []

    def berth_vessel(self, vessel):
        global BERTH_AVAILABLE
        if BERTH_AVAILABLE <= 2:
            with self.berths.request() as berth:
                BERTH_AVAILABLE = BERTH_AVAILABLE + 1
                yield berth
                print(f"{self.env.now}: Vessel {vessel} berthed.")
        else:
            self.waiting_vessels.append(vessel)

    def move_container(self, crane, container_n, vessel_name, truck):
        yield self.env.timeout(CONTAINER_MOVE_TIME)
        print(
            f"{self.env.now}: Quay Crane {crane} moved a container {container_n + 1} from {vessel_name} to Truck {truck}.")

    def truck_move_container(self,cont_n,name):
        yield self.env.timeout(TRUCK_MOVE_TIME)
        print(f"{self.env.now}: Truck transported container {cont_n} from {name} to yard block.")


def vessel(env, name, maersk_terminal):
    global BERTH_AVAILABLE
    print(f"{env.now}: Vessel {name} arrived.")
    yield env.process(maersk_terminal.berth_vessel(name))

    with maersk_terminal.cranes.request() as crane:
        yield crane
        print(f"{env.now}: Quay Crane started working on Vessel {name}.")
        for cont_n in range(CONTAINERS_PER_VESSEL):
            with maersk_terminal.trucks.request() as truck:
                yield truck
                yield env.process(maersk_terminal.move_container(crane, cont_n, name, truck))
                yield env.process(maersk_terminal.truck_move_container(cont_n,name))

    print(f"{env.now}: Vessel {name} unloaded completely.")
    print(f"{env.now}: Vessel {name} left the berth.")
    BERTH_AVAILABLE = BERTH_AVAILABLE - 1


def vessel_generator(env, maersk_terminal):
    vessel_count = 0
    while True:
        yield env.timeout(random.expovariate(1 / 5))  # Exponential distribution for vessel arrival time
        vessel_count += 1
        name = f"Vessel_{vessel_count}"
        if BERTH_AVAILABLE <= 2 and len(maersk_terminal.waiting_vessels) == 0:  # Check if there's space in the berths
            env.process(vessel(env, name, maersk_terminal))
        elif len(maersk_terminal.waiting_vessels) > 0 and BERTH_AVAILABLE <= 2:
            name = maersk_terminal.waiting_vessels.pop(0)
            # print("name waiting vessel",name)
            env.process(vessel(env, name, maersk_terminal))
        else:
            print(f"{env.now}: Vessel {vessel} is waiting for a berth.")
            yield env.process(maersk_terminal.berth_vessel(name))
            # print(f"que of vessels {len(terminal.waiting_vessels)}")


env = simpy.Environment()
maersk_terminal = ContainerMaersk(env)
env.process(vessel_generator(env, maersk_terminal))
env.run(until=SIMULATION_TIME)

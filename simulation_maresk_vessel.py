import simpy
import random

SIMULATION_TIME = 1440  # Simulation time in minutes (24 hours)
NUM_TRUCKS = 3
NUM_BERTHS = 2
NUM_CRANES = 2
CONTAINERS_PER_VESSEL = 150
CONTAINER_MOVE_TIME = 3
TRUCK_MOVE_TIME = 6
BERTH_AVAILABLE = 1


class ContainerMaersk:
    """
    This Class will handle berth of vessel request, crane request and truck request
    """

    def __init__(self, env):
        self.env = env
        self.berths = simpy.Resource(env, capacity=NUM_BERTHS)
        self.cranes = simpy.Resource(env, capacity=NUM_CRANES)
        self.trucks = simpy.Resource(env, capacity=NUM_TRUCKS)
        self.waiting_vessels = []

    def berth_vessel(self, vessel):
        """
            This method will handle
             - if berths are available slot will allocate respective vessel based on BERTH AVAILABLE global variable
             - Lets Assume berth_available is 1: It means one more slot is available it will be allocated
                           berth_available is 2: It means all berths are allocated,if any berth requested
                                                it will be added in que

        """
        global BERTH_AVAILABLE
        if BERTH_AVAILABLE <= 2:
            with self.berths.request() as berth:
                BERTH_AVAILABLE = BERTH_AVAILABLE + 1
                yield berth
                print(f"{self.env.now}: Vessel {vessel} berthed.")
        else:
            self.waiting_vessels.append(vessel)

    def move_container(self, crane, container_n, vessel_name, truck):
        """
        Requesting  crane to move container based on container move time
        """

        yield self.env.timeout(CONTAINER_MOVE_TIME)
        print(
            f"{self.env.now}: Quay Crane {crane} moved a container {container_n + 1} from {vessel_name} to Truck {truck}.")

    def truck_move_container(self,cont_n,name):
        """
        Requesting  tuck to move container based on tuck move time
        """
        yield self.env.timeout(TRUCK_MOVE_TIME)
        print(f"{self.env.now}: Truck transported container {cont_n} from {name} to yard block.")


def vessel(env, name, maersk_terminal):
    """
    This vessel function will request berths if berths are available otherwise it will send to que.
        Once berth allocated from that vessel will unload by requesting crane,truck.
        Once truck will unload container to yard it will release.
        If completely unloaded containers from vessel it will release berth and crane & update availability in berth available

    :param env: Environment object for events
    :param name: Vessel Name
    :param maersk_terminal: Terminal Object
    """
    global BERTH_AVAILABLE
    print(f"{env.now}: Vessel {name} arrived.")
    berth_request = yield env.process(maersk_terminal.berth_vessel(name))

    crane_request = maersk_terminal.cranes.request()
    yield crane_request

    print(f"{env.now}: Quay Crane started working on Vessel {name}.")
    for cont_n in range(CONTAINERS_PER_VESSEL):
        truck_request = maersk_terminal.trucks.request()
        yield truck_request
        yield env.process(maersk_terminal.move_container(crane_request, cont_n, name, truck_request))
        yield env.process(maersk_terminal.truck_move_container(cont_n, name))
        maersk_terminal.trucks.release(truck_request)

    maersk_terminal.cranes.release(crane_request)
    maersk_terminal.berths.release(berth_request)
    print(f"{env.now}: Vessel {name} unloaded completely.")
    print(f"{env.now}: Vessel {name} left the berth.")
    BERTH_AVAILABLE = BERTH_AVAILABLE - 1


def vessel_generator(env, maersk_terminal):
    """
    This vessel generator function will generates events handle exponential distribution for vessel arrival and
        processes the various events like berth request,truck request,crane request etc.
        Ex: if   -> berth available is less than are equal to 2 and waiting vessels are zeros
                    then berths available it will request vessels
            elif -> berth available is less than are equal to 2 and waiting vessels are greater than 0
                    then pick waiting vessels from que
            else -> berths are not available and moved to que

    :param env: Execution environment for an event-based simulation. The passing of time
        is simulated by stepping from event to event.
    :param maersk_terminal: Object of Maresk Terminal class which contains berth,truck,crane requests
    """
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

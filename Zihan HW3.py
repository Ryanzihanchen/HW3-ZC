from numpy import random, mean

"""
Homework 3: Modify the Agent Based Model from class.

1. Add the following things to the #params dict, and make the program use those
   settings: A boolean(logic, TRUE FALSE AND OR) for whether or not to print results to the screen, a
   boolean for whether or not to save results to file, and a setting for the
   location to write the output to on your computer.

2. The current move method lets agents look through all vacant patches, and then
   picks the first one that makes them happy.  Write a new move method, or modify
   the existing one, so that you have the option of simply moving the agent to a
   random free location without first checking happiness.  Add a parameter that
   switches between these two move processes.

3. It is currently hard-coded that there are two types of agents, each of whom
   make up half of the population and have the same preference for similar
   neighbors.  Change it so that the proportion of reds and blues is adjustable,
   and each one should be able to have a different same_pref.  Change the
   report method to show results split by color.
"""


# note: update out_path to point to somewhere on your computer
params = {
    "out_path": "output.csv",
    "world_size": (20, 20),
    "num_agents": 380,
    "same_pref": {"red": 0.4, "blue": 0.6},
    "print_screen": True,
    "save_local": True,
    "agent_ratio": 0.6,
}


class Agent:
    def __init__(self, world, kind, same_pref):
        self.world = world
        self.kind = kind
        self.same_pref = same_pref
        self.location = None

    def move(self, indifferent=False):
        # handle each agent's turn in the model iteration
        # returns 0 for happy, 1 for unhappy but moved, and 2 for unhappy and couldn't move
        happy = self.am_i_happy()

        if not happy:
            vacancies = self.world.find_vacant(return_all=True)
            i_moved = False
            for patch in vacancies:
                will_i_like_it = self.am_i_happy(loc=patch)
                if will_i_like_it is True or indifferent:
                    self.world.grid[self.location] = None  # move out of current patch
                    self.location = patch  # assign new patch to myself
                    self.world.grid[patch] = self  # update the grid
                    i_moved = True
                    # break
                    return 1
            #             if not i_moved:
            if i_moved is False:
                return 2
        else:
            return 0

    def am_i_happy(self, loc=False, neighbor_check=False):
        # this should return a boolean for whether or not an agent is happy at a location
        # if loc is False, use current location, else use specified location

        if not loc:
            starting_loc = self.location
        else:
            starting_loc = loc

        neighbor_patches = self.world.locate_neighbors(starting_loc)
        neighbor_agents = [self.world.grid[patch] for patch in neighbor_patches]
        neighbor_kinds = [agent.kind for agent in neighbor_agents if agent is not None]
        num_like_me = sum([kind == self.kind for kind in neighbor_kinds])

        # for reporting purposes, allow checking of the current number of similar neighbors
        if neighbor_check:
            return [kind == self.kind for kind in neighbor_kinds]

        # if an agent is in a patch with no neighbors at all, treat it as unhappy
        if len(neighbor_kinds) == 0:
            return False

        perc_like_me = num_like_me / len(neighbor_kinds)

        if perc_like_me < self.same_pref:
            return False
        else:
            return True


class World:
    def __init__(self, params):
        assert (
            params["world_size"][0] * params["world_size"][1] > params["num_agents"]
        ), "Grid too small for number of agents."
        self.params = params
        self.reports = {}
        self.grid = self.build_grid(params["world_size"])
        self.agents = self.build_agents(
            params["num_agents"], params["same_pref"], params["agent_ratio"]
        )
        self.init_world()

    def build_grid(self, world_size):
        # create the world that the agents can move around on
        locations = [(i, j) for i in range(world_size[0]) for j in range(world_size[1])]
        return {l: None for l in locations}

    def build_agents(self, num_agents, same_pref, agent_ratio):
        # generate a list of Agents that can be iterated over
        num_red = round(agent_ratio * num_agents)

        def _kind_picker(i):
            if i < num_red:
                return "red"
            else:
                return "blue"

        agents = [
            Agent(self, _kind_picker(i), self.params["same_pref"][_kind_picker(i)])
            for i in range(num_agents)
        ]
        random.shuffle(agents)
        return agents

    def init_world(self):
        # a method for all the steps necessary to create the starting point of the model

        for agent in self.agents:
            # while True:
            #     x = random.randint(0, self.params['world_size'][0])
            #     y = random.randint(0, self.params['world_size'][1])

            #     if self.grid[(x,y)] is None:
            #         self.grid[(x,y)] = agent
            #         agent.location = (x,y)
            #         break
            loc = self.find_vacant()
            self.grid[loc] = agent
            agent.location = loc

        assert all(
            [agent.location is not None for agent in self.agents]
        ), "Some agents don't have homes!"
        assert (
            sum([occupant is not None for occupant in self.grid.values()])
            == self.params["num_agents"]
        ), "Mismatch between number of agents and number of locations with agents."

        # set up some reporting dictionaries
        self.reports["integration"] = {"red": [], "blue": []}

    def find_vacant(self, return_all=False):
        # finds all empty patches on the grid and returns a random one, unless kwarg return_all==True,
        # then it returns a list of all empty patches

        empties = [loc for loc, occupant in self.grid.items() if occupant is None]
        if return_all:
            return empties
        else:
            choice_index = random.choice(range(len(empties)))
            return empties[choice_index]

    def locate_neighbors(self, loc):
        # given a location, return a list of all the patches that count as neighbors
        include_corners = True

        x, y = loc
        cardinal_four = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        if include_corners:
            corner_four = [
                (x + 1, y + 1),
                (x + 1, y - 1),
                (x - 1, y + 1),
                (x - 1, y - 1),
            ]
            neighbors = cardinal_four + corner_four
        else:
            neighbors = cardinal_four

        # handle patches that are at the edges, assuming a "torus" shape
        x_max = self.params["world_size"][0] - 1
        y_max = self.params["world_size"][1] - 1

        def _edge_fixer(loc):
            x, y = loc
            if x < 0:
                x = x_max
            elif x > x_max:
                x = 0

            if y < 0:
                y = y_max
            elif y > y_max:
                y = 0

            return (x, y)

        neighbors = [_edge_fixer(loc) for loc in neighbors]
        return neighbors

    def report_integration(self, kind):
        diff_neighbors = []
        for agent in self.agents:
            if agent.kind == kind:
                diff_neighbors.append(
                    sum([not a for a in agent.am_i_happy(neighbor_check=True)])
                )
        self.reports["integration"][kind].append(round(mean(diff_neighbors), 2))

    def run(self):
        # handle the iterations of the model
        log_of_happy = {"red": [], "blue": []}
        log_of_moved = {"red": [], "blue": []}
        log_of_stay = {"red": [], "blue": []}

        def report_by_kind(kind):
            self.report_integration(kind)
            log_of_happy[kind].append(
                sum([a.am_i_happy() for a in self.agents if a.kind == kind])
            )  # starting happiness
            log_of_moved[kind].append(0)  # no one moved at startup
            log_of_stay[kind].append(0)  # no one stayed at startup

        report_by_kind("red")
        report_by_kind("blue")

        def log_by_kind(move_results, kind):
            self.report_integration(kind)
            num_happy_at_start = sum(
                [
                    r == 0
                    for i, r in enumerate(move_results)
                    if self.agents[i].kind == kind
                ]
            )
            num_moved = sum(
                [
                    r == 1
                    for i, r in enumerate(move_results)
                    if self.agents[i].kind == kind
                ]
            )
            num_stayed_unhappy = sum(
                [
                    r == 2
                    for i, r in enumerate(move_results)
                    if self.agents[i].kind == kind
                ]
            )
            log_of_happy[kind].append(num_happy_at_start)
            log_of_moved[kind].append(num_moved)
            log_of_stay[kind].append(num_stayed_unhappy)

        def check_by_kind(iter, kind):
            if log_of_moved[kind][-1] == log_of_stay[kind][-1] == 0:
                print("Everyone is happy!  Stopping after iteration {}.".format(iter))
                return False
            elif log_of_moved[kind][-1] == 0 and log_of_stay[kind][-1] > 0:
                print(
                    "Some agents are unhappy, but they cannot find anywhere to move to.  Stopping after iteration {}.".format(
                        iter
                    )
                )
                return False
            else:
                return True

        for iteration in range(self.params["max_iter"]):

            random.shuffle(self.agents)  # randomize agents before every iteration
            move_results = [agent.move() for agent in self.agents]

            log_by_kind(move_results, "red")
            log_by_kind(move_results, "blue")

            if not check_by_kind(iteration, "red") or not check_by_kind(
                iteration, "blue"
            ):
                break

        self.reports["log_of_happy"] = log_of_happy
        self.reports["log_of_moved"] = log_of_moved
        self.reports["log_of_stay"] = log_of_stay

        self.report()

    def report(self):
        # report final results after run ends
        reports = self.reports
        print("\nAll results begin at time=0 and go in order to the end.\n")
        print(
            "The average number of neighbors an agent has not like them:",
            reports["integration"]["red"],
            reports["integration"]["blue"],
        )
        print(
            "The number of happy agents:",
            reports["log_of_happy"]["red"],
            reports["log_of_happy"]["blue"],
        )
        print(
            "The number of moves per turn:",
            reports["log_of_moved"]["red"],
            reports["log_of_moved"]["blue"],
        )
        print(
            "The number of agents who failed to find a new home:",
            reports["log_of_stay"]["red"],
            reports["log_of_stay"]["blue"],
        )

        if self.params["save_local"]:
            out_path = self.params["out_path"]
            with open(out_path, "w") as f:
                headers = "turn,integration_r,num_happy_r,num_moved_r,num_stayed_r,integration_b,num_happy_b,num_moved_b,num_stayed_b\n"
                f.write(headers)
                for i in range(len(reports["log_of_happy"]["red"])):
                    line = ",".join(
                        [
                            str(i),
                            str(reports["integration"]["red"][i]),
                            str(reports["log_of_happy"]["red"][i]),
                            str(reports["log_of_moved"]["red"][i]),
                            str(reports["log_of_stay"]["red"][i]),
                            str(reports["integration"]["blue"][i]),
                            str(reports["log_of_happy"]["blue"][i]),
                            str(reports["log_of_moved"]["blue"][i]),
                            str(reports["log_of_stay"]["blue"][i]),
                            "\n",
                        ]
                    )
                    f.write(line)
            print("\nResults written to:", out_path)


import random

random.seed(10)
world = World(params)
world.run()

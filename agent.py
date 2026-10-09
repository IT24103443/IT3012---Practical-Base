# agent.py
from collections import deque
import heapq
import math
import random
from logic_engine import KnowledgeBase

class GreedyGridAgent:
    """A simple agent that tries to move around systematically to clear the grid."""

    def __init__(self):
        self.actions_pool = ['Up', 'Down', 'Left', 'Right']

    def sense_and_act(self, percept: dict) -> str:
        # If standing directly on food, or just wander / move towards coordinates
        pos = percept['agent_pos']
        # Simple heuristic or fallback random sweep
        return random.choice(self.actions_pool)


class SearchAgent:
    def __init__(self):
        self.plan = []
        self.active_algo = 'AStar'      # change to 'BFS','DFS','UCS' or 'AStar' 
        self.pos = (0, 0)
        self.facing = 'Up'

        self.kb = KnowledgeBase()
        # Rule 1: TargetVisible AND HasDust => SafeToEngage
        self.kb.tell_rule(['TargetVisible', 'HasDust'], 'SafeToEngage')
        # Rule 2: SafeToEngage AND BloodseekerMissing => Retreat
        self.kb.tell_rule(['SafeToEngage', 'BloodseekerMissing'], 'Retreat')

    def closest_food(self, all_food):
        if not all_food:
            return None
        x, y = self.pos
        return min(all_food, key=lambda f: abs(f[0] - x) + abs(f[1] - y))

    def directions_to_actions(self, directions):
        """Convert ['Up','Right',...] into TurnLeft/TurnRight/Forward commands."""
        left_order = ['Up', 'Left', 'Down', 'Right']
        actions = []
        facing = self.facing
        for d in directions:
            turns_left = (left_order.index(d) - left_order.index(facing)) % 4
            turns_right = (4 - turns_left) % 4
            if turns_left <= turns_right:
                actions += ['TurnLeft'] * turns_left
            else:
                actions += ['TurnRight'] * turns_right
            actions.append('Forward')
            facing = d
        return actions

    def apply_action(self, action):
        """Keep the internal position/facing in sync with what we just did."""
        left_order = ['Up', 'Left', 'Down', 'Right']
        right_order = ['Up', 'Right', 'Down', 'Left']
        if action == 'TurnLeft':
            self.facing = left_order[(left_order.index(self.facing) + 1) % 4]
        elif action == 'TurnRight':
            self.facing = right_order[(right_order.index(self.facing) + 1) % 4]
        elif action == 'Forward':
            dx, dy = self.MOVES[self.facing]
            self.pos = (self.pos[0] + dx, self.pos[1] + dy)

    def sense_and_act(self, percept):
        if not self.plan:
            goal = self.closest_food(percept['all_food'])
            if goal is None:
                return 'TurnLeft'
            walls = set(percept['walls'])
            grid_size = percept['grid_size']

            # per-tile facts the KB reasons over ({(x, y): [facts]})
            tile_facts = {
                (1, 0): ['TargetVisible', 'HasDust', 'BloodseekerMissing'],  # deduces Retreat: blocked
                (0, 1): ['TargetVisible', 'HasDust'],                        # SafeToEngage only: allowed
            }
            if self.active_algo == 'BFS':
                directions = self.bfs_search(self.pos, goal, walls, grid_size)
            elif self.active_algo == 'DFS':
                directions = self.dfs_search(self.pos, goal, walls, grid_size)
            elif self.active_algo == 'AStar':
                directions = self.astar_search(self.pos, goal, walls, grid_size,
                                               heuristic_type='manhattan', tile_facts=tile_facts)
                if not directions:
                    # nearest food is not feasibly reachable -> try the next nearest ones
                    x, y = self.pos
                    for food in sorted(percept['all_food'], key=lambda f: abs(f[0] - x) + abs(f[1] - y)):
                        directions = self.astar_search(self.pos, food, walls, grid_size,
                                                       heuristic_type='manhattan', tile_facts=tile_facts)
                        if directions:
                            break
            else:
                directions = self.ucs_search(self.pos, goal, walls, grid_size)
            self.plan = self.directions_to_actions(directions)

        if not self.plan:
            return 'TurnLeft'

        action = self.plan.pop(0)
        self.apply_action(action)
        return action    

    MOVES = {'Up': (0, 1), 'Down': (0, -1), 'Left': (-1, 0), 'Right': (1, 0)}

    def get_successors(self, state, walls, grid_size):
        """Return [(direction, next_state), ...] — legal moves from a cell."""
        width, height = grid_size
        x, y = state
        successors = []
        for direction, (dx, dy) in self.MOVES.items():
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in walls:
                successors.append((direction, (nx, ny)))
        return successors

    def bfs_search(self, start, goal, walls, grid_size):
        frontier = deque([(start, [])])
        reached = {start}
        while frontier:
            state, path = frontier.popleft()
            if state == goal:
                return path
            for direction, nxt in self.get_successors(state, walls, grid_size):
                if nxt not in reached:
                    reached.add(nxt)
                    frontier.append((nxt, path + [direction]))
        return []
    
    def dfs_search(self, start, goal, walls, grid_size):
        frontier = [(start, [])]
        reached = set()
        while frontier:
            state, path = frontier.pop()
            if state == goal:
                return path
            if state in reached:
                continue
            reached.add(state)
            for direction, nxt in self.get_successors(state, walls, grid_size):
                if nxt not in reached:
                    frontier.append((nxt, path + [direction]))
        return []

    def step_cost(self, state):
        return 1

    def ucs_search(self, start, goal, walls, grid_size):
        counter = 0
        frontier = [(0, counter, start, [])]
        reached = {start: 0}
        while frontier:
            cost, _, state, path = heapq.heappop(frontier)
            if state == goal:
                return path
            if cost > reached.get(state, float('inf')):
                continue
            for direction, nxt in self.get_successors(state, walls, grid_size):
                new_cost = cost + self.step_cost(nxt)
                if new_cost < reached.get(nxt, float('inf')):
                    reached[nxt] = new_cost
                    counter += 1
                    heapq.heappush(frontier, (new_cost, counter, nxt, path + [direction]))
        return []

    def manhattan_distance(self, pos, goal):
        return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])

    def euclidean_distance(self, pos, goal):
        return math.sqrt((pos[0] - goal[0]) ** 2 + (pos[1] - goal[1]) ** 2)

    def astar_search(self, start_pos, goal_pos, walls, grid_size, heuristic_type='manhattan', tile_facts=None):
        if tile_facts is None:
            tile_facts = {}

        def h(pos):
            if heuristic_type == 'euclidean':
                return self.euclidean_distance(pos, goal_pos)
            return self.manhattan_distance(pos, goal_pos)

        frontier = []
        reached_states = set()

        g_cost = 0
        f_cost = g_cost + h(start_pos)
        heapq.heappush(frontier, (f_cost, g_cost, start_pos, []))

        while frontier:
            f_cost, g_cost, current_pos, path_taken = heapq.heappop(frontier)

            if current_pos == goal_pos:
                return path_taken

            if current_pos in reached_states:
                continue
            reached_states.add(current_pos)

            for direction, neighbour in self.get_successors(current_pos, walls, grid_size):
                if neighbour in reached_states:
                    continue
                # Reachability (wall / off-grid) is already checked by get_successors().
                # Feasibility: ask the Knowledge Base before adding to the open list.
                self.kb.clear_facts()
                for fact in tile_facts.get(neighbour, []):
                    self.kb.tell_fact(fact)
                self.kb.forward_chain()
                if 'Retreat' in self.kb.facts:
                    continue   # Infeasible: physically reachable but logically unsafe -> skip
                g_new = g_cost + 1
                f_new = g_new + h(neighbour)
                heapq.heappush(frontier, (f_new, g_new, neighbour, path_taken + [direction]))

        return []

    

# if __name__ == "__main__":
#     a = SearchAgent()
#     print(a.manhattan_distance((0, 0), (3, 4)))   # 7
#     print(a.euclidean_distance((0, 0), (3, 4)))   # 5.0
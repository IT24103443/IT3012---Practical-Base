# visual_grid_game.py
import random
import tkinter as tk
from agent import SearchAgent

class VisualGridHuntGame:
    """A flexible Pacman-style grid environment with support for configurable opponents and larger scales."""

    def __init__(self, width=10, height=10, num_food=10, num_opponents=4, num_traps=5, custom_walls=None):
        self.width = width
        self.height = height
        self.agent_pos = [0, 0]  # Starting position (x, y)
        self.facing = 'Up' #Default facing diraction

        if custom_walls is not None:
            self.walls = set(custom_walls)
        else:
            # Generate some default scattered walls for a larger grid
            self.walls = {(2, 2), (2, 3), (5, 5), (6, 5), (3, 7)}

        # Dynamically generate random food positions avoiding walls and agent start
        self.food_positions = set()
        while len(self.food_positions) < num_food:
            fx = random.randint(0, self.width - 1)
            fy = random.randint(0, self.height - 1)
            pos_tuple = (fx, fy)
            if pos_tuple != (0, 0) and pos_tuple not in self.walls:
                self.food_positions.add(pos_tuple)

        # Generate adversarial opponents
        self.opponents = []
        while len(self.opponents) < num_opponents:
            ox = random.randint(0, self.width - 1)
            oy = random.randint(0, self.height - 1)
            op_pos = [ox, oy]
            if tuple(op_pos) != (0, 0) and tuple(op_pos) not in self.walls and tuple(op_pos) not in self.food_positions:
                self.opponents.append(op_pos)

        #trap collection attribute
        self.toxic_traps = set()
        while len(self.toxic_traps) < num_traps:
            tx = random.randint(0, self.width - 1)                    
            ty = random.randint(0, self.height - 1)
            trap_tuple = (tx, ty)
            if (
                trap_tuple != (0, 0) 
                and tuple(trap_tuple) not in self.walls 
                and tuple(trap_tuple) not in self.food_positions):
                    self.toxic_traps.add(trap_tuple)

        self.score = 0
        self.steps = 0
        self.collision = False

    def get_percept(self) -> dict:
        # Determine the cell directly in front of the agent
        x, y = self.agent_pos

        if self.facing == 'Up':
            front = (x, y + 1)
        elif self.facing == 'Down':
            front = (x, y - 1)
        elif self.facing == 'Left':
            front = (x - 1, y)
        else:
            front = (x + 1, y)

        wall_ahead = (
            front[0] < 0 or front[0] >= self.width or
            front[1] < 0 or front[1] >= self.height or
            front in self.walls
        )

        opponent_ahead = any(tuple(op) == front for op in self.opponents)

        return {
            'wall_ahead': wall_ahead,
            'food_ahead': front in self.food_positions,
            'toxin_ahead': front in self.toxic_traps,
            'opponent_ahead': opponent_ahead,
            'collision': self.collision,
            'score': self.score,
            'grid_size': (self.width, self.height),
            'walls': list(self.walls),
            'all_food': list(self.food_positions)
        }

    def execute_action(self, action: str):
        self.steps += 1

        if action == 'TurnLeft':
            directions = ['Up', 'Left', 'Down', 'Right']
            idx = directions.index(self.facing)
            self.facing = directions[(idx + 1) % 4]
            return

        elif action == 'TurnRight':
            directions = ['Up', 'Right', 'Down', 'Left']
            idx = directions.index(self.facing)
            self.facing = directions[(idx + 1) % 4]
            return

        new_pos = list(self.agent_pos)

        if action == 'Forward':

            if self.facing == 'Up':
                new_pos[1] = min(self.height - 1, new_pos[1] + 1)

            elif self.facing == 'Down':
                new_pos[1] = max(0, new_pos[1] - 1)

            elif self.facing == 'Left':
                new_pos[0] = max(0, new_pos[0] - 1)

            elif self.facing == 'Right':
                new_pos[0] = min(self.width - 1, new_pos[0] + 1)

        if tuple(new_pos) in self.walls:
            self.score -= 5
        else:
            self.agent_pos = new_pos

        tuple_pos = tuple(self.agent_pos)
        if tuple_pos in self.food_positions:
            self.food_positions.remove(tuple_pos)
            self.score += 20

        tuple_trap = tuple_pos
        if tuple_trap in self.toxic_traps:
            self.score -= 15

        for op in self.opponents:
            move = random.choice(['Up', 'Down', 'Left', 'Right', 'Stay'])
            if move == 'Up' and op[1] < self.height - 1:
                op[1] += 1
            elif move == 'Down' and op[1] > 0:
                op[1] -= 1
            elif move == 'Left' and op[0] > 0:
                op[0] -= 1
            elif move == 'Right' and op[0] < self.width - 1:
                op[0] += 1

            if op == self.agent_pos:
                self.score -= 50
                self.collision = True

    def is_done(self) -> bool:
        return len(self.food_positions) == 0 or self.steps >= 60 or self.collision


class SimpleReflexAgent:
    def sense_and_act(self, percept):

        if percept['food_ahead']:
            return 'Forward'

        elif percept['wall_ahead']:
            return 'TurnLeft'

        elif percept['opponent_ahead']:
            return 'TurnLeft'

        elif percept['toxin_ahead']:
            return 'TurnRight'

        else:
            return 'Forward'

class ModelBasedAgent:
    def __init__(self):
        self.visited_cells = {(0, 0)} #internal memory
        self.obstacles = set()        # Internal map of known walls/toxins
        self.current_pos = (0, 0) #relative position estimate
        self.last_action = None
        self.facing = 'Up'

    def update_state(self):
        x, y = self.current_pos

        if self.last_action == 'Forward':
            if self.facing == 'Up':
                y += 1
            elif self.facing == 'Down':
                y -= 1
            elif self.facing == 'Left':
                x -= 1
            elif self.facing == 'Right':
                x += 1

        elif self.last_action == "TurnLeft":
            directions = ['Up', 'Left', 'Down', 'Right']
            idx = directions.index(self.facing)
            self.facing = directions[(idx + 1) % 4]
            
        elif self.last_action == "TurnRight":
            directions = ['Up', 'Right', 'Down', 'Left']
            idx = directions.index(self.facing)
            self.facing = directions[(idx + 1) % 4]

        self.current_pos = (x, y)
        self.visited_cells.add(self.current_pos)

    def sense_and_act(self, percept):
        self.update_state()
        x, y = self.current_pos

        # Calculate the cell to the agent's RELATIVE left and right
        if self.facing == 'Up':
            front = (x, y + 1)
            left = (x - 1, y)
            right = (x + 1, y)
        elif self.facing == 'Down':
            front = (x, y - 1)
            left = (x + 1, y)
            right = (x - 1, y)
        elif self.facing == 'Left':
            front = (x - 1, y)
            left = (x, y - 1)
            right = (x, y + 1)
        elif self.facing == 'Right':
            front = (x + 1, y)
            left = (x, y + 1)
            right = (x, y - 1)

        if percept['wall_ahead'] or percept['toxin_ahead']:
            self.obstacles.add(front)

        known_bad = self.visited_cells.union(self.obstacles)

        if percept['opponent_ahead']:
            left_bad = left in known_bad
            right_bad = right in known_bad

            if left_bad and not right_bad:
                action = 'TurnRight'
            elif right_bad and not left_bad:
                action = 'TurnLeft'
            else:
                action = 'TurnRight'

        if percept['wall_ahead'] or percept['toxin_ahead']:
            # Check if left or right lead to known bad spaces (visited cells OR walls)
            left_bad = left in known_bad
            right_bad = right in known_bad

            if left_bad and not right_bad:
                action = 'TurnRight'
            elif right_bad and not left_bad:
                action = 'TurnLeft'
            else:
                action = 'TurnRight' 

        elif percept['food_ahead']:
            action = 'Forward'

        else:
            action = 'Forward'

        self.last_action = action
        return action


class GridGameGUI:
    """Tkinter wrapper that dynamically scales cell sizes to keep larger grids on screen."""

    def __init__(self, root, width=10, height=10, num_food=12, num_opponents=4, num_traps=5,walls=None):
        self.root = root
        self.root.title("SE3062 - Scalable Multi-Agent Grid Hunt")
        self.agent = SearchAgent()

        self.env = VisualGridHuntGame(width=width, height=height, num_food=num_food, num_opponents=num_opponents, num_traps=num_traps,
                                                            custom_walls=walls)

        # Dynamically calculate cell size so the total canvas fits nicely within a 600x600 window ceiling
        max_canvas_dim = 600
        self.cell_size = max(20, min(max_canvas_dim // self.env.width, max_canvas_dim // self.env.height))

        canvas_w = self.env.width * self.cell_size
        canvas_h = self.env.height * self.cell_size

        self.canvas = tk.Canvas(root, width=canvas_w, height=canvas_h, bg="white")
        self.canvas.pack()

        self.label = tk.Label(root, text="Score: 0 | Steps: 0", font=("Arial", 14))
        self.label.pack(pady=10)

        self.btn = tk.Button(root, text="Start Simulation", command=self.run_loop, font=("Arial", 12), bg="#000066",
                             fg="white")
        self.btn.pack(pady=5)

        self.draw_grid()

    def draw_grid(self):
        self.canvas.delete("all")

        for x in range(self.env.width):
            for y in range(self.env.height):
                x1 = x * self.cell_size
                y1 = (self.env.height - 1 - y) * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                color = "#f1f5f9" if (x, y) not in self.env.walls else "#64748b"
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#cbd5e1")

                # Only draw text if cell is large enough
                if self.cell_size >= 40 and (x, y) in self.env.walls:
                    self.canvas.create_text(x1 + self.cell_size / 2, y1 + self.cell_size / 2, text="W", fill="white",
                                            font=("Arial", 8, "bold"))

        for fx, fy in self.env.food_positions:
            offset = self.cell_size * 0.25
            x1 = fx * self.cell_size + offset
            y1 = (self.env.height - 1 - fy) * self.cell_size + offset
            self.canvas.create_oval(x1, y1, x1 + self.cell_size * 0.5, y1 + self.cell_size * 0.5, fill="#f59e0b",
                                    outline="#d97706")

        for ox, oy in self.env.opponents:
            offset = self.cell_size * 0.2
            x1 = ox * self.cell_size + offset
            y1 = (self.env.height - 1 - oy) * self.cell_size + offset
            self.canvas.create_rectangle(x1, y1, x1 + self.cell_size * 0.6, y1 + self.cell_size * 0.6, fill="#990000",
                                    outline="#7a0000")

        for tx, ty in self.env.toxic_traps:
            offset = self.cell_size * 0.25
            x1 = tx * self.cell_size + offset
            y1 = (self.env.height - 1 - ty) * self.cell_size + offset
            self.canvas.create_oval(x1, y1, x1 + self.cell_size * 0.5, y1 + self.cell_size * 0.5, fill="#a30bf5",
                                    outline="#a30bf5")

        ax, ay = self.env.agent_pos
        offset = self.cell_size * 0.15
        x1 = ax * self.cell_size + offset
        y1 = (self.env.height - 1 - ay) * self.cell_size + offset
        self.canvas.create_oval(x1, y1, x1 + self.cell_size * 0.7, y1 + self.cell_size * 0.7, fill="#000066",
                                outline="#1e3a8a")

    def run_loop(self):
        self.btn.config(state="disabled")

        def step():
            if not self.env.is_done():
                percept = self.env.get_percept()
                action = self.agent.sense_and_act(percept)

                self.env.execute_action(action)

                self.draw_grid()
                self.label.config(text=f"Score: {self.env.score} | Steps: {self.env.steps} | Action: {action}")
                self.root.after(250, step)
            else:
                end_text = f"Collision! Game Over! Final Score: {self.env.score}" if self.env.collision else f"Finished! Final Score: {self.env.score}"
                self.label.config(text=end_text)
                self.btn.config(state="normal")

        step()


if __name__ == "__main__":
    root = tk.Tk()
    # Try a larger grid size like 12x12 with 15 food and 3 opponents!
    app = GridGameGUI(root, width=12, height=12, num_food=15, num_opponents=4)
    root.mainloop()
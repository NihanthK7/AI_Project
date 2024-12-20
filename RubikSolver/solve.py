from collections import namedtuple
import time
import matplotlib.pyplot as plt
import numpy as np
import torch
from tqdm import tqdm
from cube_env import CubeEnv
from dueling_dqn import DuelingDQN

Solve = namedtuple('Solve', ['solved', 'scramble', 'solution',
                             'solution_length'])


class Solver:
    def __init__(self, device, model, env):
        self.device = device
        self.model = model
        self.env = env

    def solve_cube(self, observation, max_step_count) -> tuple[bool, str, int]:
        """
        Attempt to solve a given cube within the given number of steps.

        Returns whether the cube was solved, the moves made, and the number of
        moves.
        """
        # Store the previous states to check for duplicates.
        previous_states = []
        moves = []
        solved = False
        for _ in range(max_step_count):
            # The cube state must be converted to a PyTorch tensor before it
            # can be fed into the model.
            cube_state = torch.as_tensor(observation['cube_state'],
                                         dtype=torch.float, device=self.device)
            action_mask = observation['action_mask']
            # torch.no_grad() is used because the model is not being trained.
            with torch.no_grad():
                # Unsqueeze the state tensor to add a batch dimension. The
                # batch size is 1.
                q_values = self.model(cube_state.unsqueeze(0)).squeeze()
            q_values[~action_mask] = float('-inf')
            # Sort the possible actions in descending order by their Q-values,
            # so that each action can be checked for validity in order.
            _, actions = torch.sort(q_values, descending=True)
            actions = [action.item() for action in actions.squeeze()]
            action = None
            done = False
            for action in actions:
                observation, _, done, _ = self.env.step(action)
                cube_state = torch.as_tensor(observation['cube_state'],
                                             dtype=torch.float,
                                             device=self.device)
                # If the cube state has already been reached, undo the action
                # and try the next action.
                if any(torch.equal(cube_state, previous_state)
                       for previous_state in previous_states):
                    self.env.step(self.env.get_undoing_action(action))
                    continue
                break
            previous_states.append(cube_state)
            moves.append(self.env.moves[action])
            if done:
                solved = True
                break
        solution = ' '.join(moves)
        solution_length = len(moves)
        return solved, solution, solution_length

    def solve_random_cubes(self, solve_count, scramble_length,
                           max_step_count) -> tuple[int, list[Solve]]:
        """
        Solve a given number of randomly scrambled cubes.

        Returns the number of cubes solved and the list of solves with
        information including the scramble, solution, and solution length.
        """
        solved_count = 0
        solves = []
        for _ in tqdm(range(solve_count)):
            observation, info = self.env.reset(
                return_info=True, options={'scramble_length': scramble_length})
            scramble = info['scramble']
            solved, solution, solution_length = self.solve_cube(
                observation, max_step_count)
            if solved:
                solved_count += 1
            solves.append(Solve(solved, scramble, solution, solution_length))
        return solved_count, solves

    def evaluate_model(self, cube_count, scramble_length, max_step_count):
        """
        Evaluate a trained model by solving a given number of randomly
        scrambled cubes. Print the number of cubes solved and plot the
        distribution of solution lengths.
        """
        solved_count, solves = self.solve_random_cubes(
            cube_count, scramble_length, max_step_count)
        print_solves(solves, print_type='all')
        print(f'{solved_count}/{cube_count} ({solved_count / cube_count:.2%}) '
              f'solved')
        plot_solution_lengths(solves)


def print_solves(solves, print_type='all'):
    """
    Format and print a given list of solves.

    print_type determines which of the solves are printed. It can be one of
    "all", "solved", or "unsolved".
    """
    for solve in solves:
        if (print_type == 'all'
                or (print_type == 'solved' and solve.solved)
                or (print_type == 'unsolved' and not solve.solved)):
            print(f'Solved: {solve.solved}, scramble: {solve.scramble}, '
                  f'solution: {solve.solution}')


def plot_solution_lengths(solves):
    """Plot the distribution of solution lengths for a given list of solves."""
    solution_lengths = [solve.solution_length for solve in solves
                        if solve.solved]
    # Do not plot if no cubes were solved.
    if not solution_lengths:
        return
    fig, ax = plt.subplots(figsize=(12.8, 7.2))
    # Set the bins so that the solution lengths are in the middle of the bins.
    ax.hist(solution_lengths, bins=np.arange(0.5, max(solution_lengths) + 1.5),
            align='mid')
    # Only allow integer ticks for the x-axis.
    ax.xaxis.get_major_locator().set_params(integer=True)
    ax.set_xlabel('Moves', fontsize=20)
    ax.set_ylabel('Count', fontsize=20)
    ax.tick_params(labelsize=12)
    fig.tight_layout()
    fig.show()


def get_solver(run_id) -> Solver:
    """Initialize a solver with a given run id."""
    # torch.equal in Solver.solve_cube is very slow on a GPU, so use the CPU.
    device = torch.device('cpu')
    print(f'Using device: {device}.')
    model = DuelingDQN().to(device)
    model.load_state_dict(torch.load(f'training-runs/{run_id}/state_dict.pt', map_location=torch.device('cpu')))
    # Set the model to evaluation mode so that the batch normalization layers
    # are not updated.
    model.eval()
    env = CubeEnv()
    return Solver(device, model, env)


def evaluate_model():
    """
    Evaluate a trained model by solving a given number of randomly scrambled
    cubes. Print the number of cubes solved and plot the distribution of
    solution lengths.
    """
    # Set these variables before running the function.
    run_id = '20240512'
    cube_count = 1000
    scramble_length = 14
    max_step_count = 20

    solver = get_solver(run_id)
    solver.evaluate_model(cube_count, scramble_length, max_step_count)


def solve_scramble():
    """
    Use a trained model to solve a given scramble. Display the cube before and
    after solving.
    """
    # Set these variables before running the function.
    run_id = '20240512'
    scramble = "R2 F' R2 U' F R2 U' R' F R F'"
    max_step_count = 20

    solver = get_solver(run_id)
    solver.env.cube.apply_moves(scramble)
    observation = solver.env.get_observation()
    # Display the scrambled cube.
    solver.env.render()
    time.sleep(10)
    solved, solution, solution_length = solver.solve_cube(observation,
                                                          max_step_count)
    print(f'Solved: {solved}\nScramble: {scramble}\nSolution: {solution} '
          f'({solution_length} quarter turns)')
    # Display the solved cube, or the cube in its final state if it was not
    # solved.
    solver.env.render()
    # time.sleep(10)


if __name__ == '__main__':
    # Call evaluate_model or solve_scramble after setting the configuration
    # variables inside the function.
    evaluate_model()
    #solve_scramble()

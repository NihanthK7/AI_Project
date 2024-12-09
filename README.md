# 2x2x2 Rubik's Cube Solver

A Reinforcement learning agent that solves a 2x2x2 Rubik's cube, implemented
with a Dueling Double Deep Q-Network.

## Description

Inside the RubikSolver we have the cube.py, cube_env.py which defines the Rubik
Inside the `2x2-cube-solver` directory, `cube.py` and `cube_env.py` define the
2x2 Rubik's cube and its Gym environment. dueling_dqn.py is a simple 4 -layer dueling dqn model implemented
with sepeartae outputs for state value which is V(s) and A(s,a) 

Training the model is done using `train.py`, and the trained model can be used
to solve cubes through `solve.py`.

## Usage

### Training

To train a model, set the configuration variables in `config.py` and
run `train.py`.

Resuming a previous training run can be done by setting the `RESUME_RUN_ID`
configuration variable.

### Solving

Two ways of solving cubes using a trained model are available in `solve.py`.

The first method uses the `evaluate_model` function and solves a large number
of randomly scrambled cubes. Solve results and a plot of the solution length
distribution are displayed with total proportion being correct.

The second method uses the `solve_scramble` function and solves a single cube
scrambled according to a given scramble. This can be used to examine a model's
performance for a specific scramble of interest.

For solving, the configuration variables must be set inside the respective
functions before calling them in `solve.py` like scramble length, Moves and the runid on which you want to run on

For evaluating comment out  `solve_scramble()` function and uncomment the `evaluate_model`.. 


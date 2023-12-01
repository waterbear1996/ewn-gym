from envs import EinsteinWuerfeltNichtEnv, MinimaxEnv, Player
from typing import Tuple, Optional
import numpy as np
from tqdm import tqdm


class ExpectiMinimaxAgent:
    def __init__(self, max_depth, env):
        self.max_depth = max_depth
        self.env = env

    def expectiminimax(self, depth: int, player: Player,
                       parent: Player | str, alpha: int, beta: int):
        if self.env.check_win() or depth == 0:
            return self.env.evaluate(), None

        # Maximizing player
        if player == self.env.agent_player:
            best_val = -float('inf')
            best_action = None
            legal_actions = self.env.get_legal_actions(player)
            curr_dice_roll = self.env.dice_roll
            for action in legal_actions:
                self.env.set_dice_roll(curr_dice_roll)
                self.env.make_simulated_action(player, action)
                val, _ = self.expectiminimax(
                    depth - 1, 'chance', player, alpha, beta)
                self.env.undo_simulated_action()
                if val > best_val:
                    best_val = val
                    best_action = action
                alpha = max(alpha, best_val)
                if beta <= alpha:
                    break
            return best_val, best_action
        # Minimizing player
        elif player == self.env.get_opponent(self.env.agent_player):
            worst_val = float('inf')
            worst_action = None
            legal_actions = self.env.get_legal_actions(player)
            curr_dice_roll = self.env.dice_roll
            for action in legal_actions:
                self.env.set_dice_roll(curr_dice_roll)
                self.env.make_simulated_action(player, action)
                val, _ = self.expectiminimax(
                    depth - 1, 'chance', player, alpha, beta)
                self.env.undo_simulated_action()
                if val < worst_val:
                    worst_val = val
                    worst_move = action
                beta = min(beta, worst_val)
                if beta <= alpha:
                    break
            return worst_val, worst_action
        # Chance node
        elif player == 'chance':
            expected_val = 0
            next_player = self.env.agent_player if parent == self.env.get_opponent(
                self.env.agent_player) else self.env.get_opponent(self.env.agent_player)
            for dice_roll in range(1, 7):
                self.env.set_dice_roll(dice_roll)
                val, _ = self.expectiminimax(
                    depth - 1, next_player, player, alpha, beta)
                expected_val += val / 6
            return expected_val, None

    def restore_env_with_obs(self, obs):
        self.env.dice_roll = obs['dice_roll']
        self.env.board[:] = obs['board']

        for i in range(self.env.cube_num * 2):
            self.env.cube_pos[i] = np.ma.masked
        for i in range(self.env.board.shape[0]):
            for j in range(self.env.board.shape[1]):
                cube = self.env.board[i, j]
                if cube > 0:
                    self.env.cube_pos[cube - 1] = (i, j)
                elif cube < 0:
                    self.env.cube_pos[cube] = (i, j)

    def predict(self, obs, **kwargs):
        self.restore_env_with_obs(obs)
        _, chosen_action = self.expectiminimax(
            self.max_depth, self.env.agent_player, None, -float('inf'), float('inf'))
        return chosen_action, None


if __name__ == "__main__":

    num_simulations = 1000
    cube_layer = 3
    board_size = 5

    env = EinsteinWuerfeltNichtEnv(
        # render_mode="ansi",
        # render_mode="rgb_array",
        # render_mode="human",
        cube_layer=cube_layer,
        board_size=board_size,
        # opponent_policy="models/5x5/1"
    )

    minimax_env = MinimaxEnv(cube_layer=cube_layer, board_size=board_size)
    agent = ExpectiMinimaxAgent(max_depth=3, env=minimax_env)

    win_count = 0
    for seed in tqdm(range(num_simulations)):
        obs, _ = env.reset(seed=seed)
        states = []

        while True:
            states.append(env.render())
            action, _state = agent.predict(obs)
            obs, reward, done, trunc, info = env.step(action)
            if done:
                if info['message'] == 'You won!':
                    win_count += 1
                if info['message'] != 'You won!' and info['message'] != 'You lost!':
                    win_count += 1
                # print(info['message'])
                break

    print(f'win rate: {win_count / num_simulations * 100:.2f}%')


#!/usr/bin/env python

import os
import sys
import argparse
import time
import numpy as np

import pygame
from pygame.locals import *


lib_path = os.path.abspath(os.path.join('..', 'first-ai-planning-agent-sol'))
sys.path.append(lib_path)

lib_path = os.path.abspath(os.path.join('/', 'vagrant', 'first-ai-planning-agent-dev'))
sys.path.append(lib_path)

import search_agent as sa
import search_functions_dev
import search_functions_sol

import threading


def load_world_settings(path):
    f = open(path, 'r')
    grid_components = f.readlines()
    f.close()
    return np.array(map(lambda x: list(x[:-1] if '\n' in x else x), grid_components))


def where_element(X, e):
    pos = np.where(X == e)
    return pos[0][0], pos[1][0]


def is_in_grid(pos, grid_size):
        return (pos[0] >= 0 and pos[0] < grid_size[0]) and (pos[1] >= 0 and pos[1] < grid_size[1])


def move(pos, direction):
        if direction == 'UP':
            return pos[0]-1, pos[1]
        elif direction == 'DOWN':
            return pos[0]+1, pos[1]
        elif direction == 'LEFT':
            return pos[0], pos[1]-1
        elif direction == 'RIGHT':
            return pos[0], pos[1]+1
        else:
            return pos


def elem_rules_trans(e, earth_mode):
    if e == 'H':
        return 'L'
    if e == 'L':
        return 'E' if earth_mode else 'L'
    if e == 'R':
        return 'R'
    if e == 'E':
        return 'E'
    raise AttributeError("Unknown Element: %s\nElements must be in ['H','L','E','R']" % e)


class GameState():
    def __init__(self, path=None, grid=None, mower_pos=None, earth_mode=False, under_mower='L', nb_propellers=3, bonus_mow=500, living_penalty=1, earth_mow_penalty=200, lose_propeller=10000, score=0, penalties=None):
        if grid is None:
            grid = load_world_settings(path)
            self._mower_pos = where_element(grid, 'M')
            grid[self._mower_pos] = under_mower
            self._grid = grid
        else:
            self._mower_pos = mower_pos
            self._grid = grid

        self._earth_mode = earth_mode
        self._nb_propellers = nb_propellers
        self._bonus_mow = bonus_mow
        self._score = score
        if penalties is None:
            self._penalties = {'living': living_penalty, 'mow_to_earth': earth_mow_penalty, 'lose_propeller': lose_propeller}
        else:
            self._penalties = penalties

    def get_grid_size(self):
        return self._grid.shape

    def is_game_over(self):
        return self._nb_propellers == 0

    def is_win(self):
        return 'H' not in self._grid

    def execute_action(self, action):

        pos = self._mower_pos
        grid = self._grid.copy()
        nb_propellers = self._nb_propellers
        bonus_mow = self._bonus_mow
        earth_mode = self._earth_mode
        next_pos = move(pos, action)
        score = self._score
        penalties = self._penalties.copy()

        if action != 'STOP':
            if is_in_grid(next_pos, self._grid.shape):
                next_e = grid[next_pos[0], next_pos[1]]

                if next_e == 'R':
                    nb_propellers = max(nb_propellers - 1, 0)
                    score -= penalties['lose_propeller']
                if next_e == 'H':
                    score += bonus_mow
                if (next_e == 'L') and self._earth_mode:
                    score -= penalties['mow_to_earth']

                grid[next_pos[0], next_pos[1]] = elem_rules_trans(next_e, earth_mode)
                pos = next_pos

        score -= penalties['living']

        return GameState(grid=grid, mower_pos=pos, earth_mode=earth_mode, bonus_mow=bonus_mow, nb_propellers=nb_propellers, score=score, penalties=penalties)


class Block:
    def __init__(self, name, img_path, block_size):
        self.name = name
        b = pygame.image.load(img_path).convert_alpha()
        self.block = pygame.transform.scale(b, block_size)


def get_component_filename(x):
    if x == 'H':
        return "images/hight-grass.jpg"
    if x == 'L':
        return "images/low-grass.jpg"
    elif x == 'R':
        return "images/rocks.jpg"
    elif x == 'M':
        return "images/roomba.png"
    else:
        return "images/earth.jpg"


def init_blocks(block_size):
    elements = ['H', 'L', 'R', 'M', 'E']
    blocks = {}
    for e in elements:
        img_path = get_component_filename(e)
        blocks[e] = Block(e, img_path, block_size)
    return blocks


def get_block_pos(i, j, block_size):
    x_pos = block_size[1]*i
    y_pos = block_size[0]*j
    return y_pos, x_pos


def text_infos(gameState, window, font):
    color = (255, 255, 255)
    scoretext = font.render("Score: %d" % gameState._score, True, color)
    propollerstext = font.render("Number of Propellers: %d" % gameState._nb_propellers, True, color)
    window.blit(scoretext, (10, 10))
    window.blit(propollerstext, (10, 40))
    pygame.display.update()


def game_over(window, window_size):
    font = pygame.font.SysFont("monospace", 70)
    text = font.render("GAME OVER", True, (255, 0, 0))
    window.blit(text, (max(0, window_size[0]/2. - 150), max(0, window_size[1]/2 - 70)))
    pygame.display.update()


def you_win(window, window_size):
    font = pygame.font.SysFont("monospace", 70)
    text = font.render("YOU WIN", True, (255, 0, 0))
    window.blit(text, (max(0, window_size[0]/2. - 150), max(0, window_size[1]/2 - 70)))
    pygame.display.update()


def draw_world(window, blocks, block_size, gameState, font, window_size):
    grid_size = gameState.get_grid_size()
    for i in range(grid_size[0]):
        for j in range(grid_size[1]):
            xypos = get_block_pos(i, j, block_size)
            e = gameState._grid[i, j]
            block = blocks[e].block
            window.blit(block, xypos)

            if (i, j) == gameState._mower_pos:
                block = blocks['M'].block
                window.blit(block, xypos)

    pygame.display.flip()
    text_infos(gameState, window, font)

    if gameState.is_game_over():
        game_over(window, window_size)
    if gameState.is_win():
        you_win(window, window_size)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--agent', default=None)
    parser.add_argument('--heuristic', default='null_heuristic')
    parser.add_argument('--world', default='1')
    parser.add_argument('--solution', action='store_const', const=True, default=False)
    parser.add_argument('--check_frontier', action='store_const', const=True, default=False)
    parser.add_argument('--earth_mode', action='store_const', const=True, default=False)
    parser.add_argument('--edge_size', default=None, type=int)

    args = parser.parse_args()

    pygame.font.init()
    font = pygame.font.SysFont("monospace", 30)
    path = 'worlds/bonus.txt' if args.world == 'bonus' else 'worlds/world-%s.txt' % args.world
    gameState = GameState(path, earth_mode=args.earth_mode)
    grid_size = gameState.get_grid_size()
    ratio = grid_size[0]*1./grid_size[1]

    xw = args.edge_size if args.edge_size else (200 if args.world == 'bonus' else 700)
    window_size = (int(xw/ratio), xw)
    actions_mapping = {K_DOWN: 'DOWN', K_UP: 'UP', K_RIGHT: 'RIGHT', K_LEFT: 'LEFT'}

    block_size = (window_size[0] / grid_size[1], window_size[1] / grid_size[0])
    window_size = (grid_size[1]*block_size[0], grid_size[0]*block_size[1])

    pygame.init()
    window = pygame.display.set_mode(window_size)
    blocks = init_blocks(block_size)

    draw_world(window, blocks, block_size, gameState, font, window_size)

    if args.agent is not None:
            search_fun = getattr(search_functions_sol if args.solution else search_functions_dev, args.agent)
            heur = getattr(search_functions_sol if args.solution else search_functions_dev, args.heuristic)
            prob = sa.MowSearchProblem(gameState)
            agent = sa.SearchAgent(problem=prob, search_fun=search_fun, heuristic=heur, check_frontier=args.check_frontier)

    init_agent = True
    continuer = 1
    timelapse = 0.07
    start = time.time()
    while continuer:
        if init_agent and (args.agent is not None):
            threading.Thread(target=agent.plan).start()
            init_agent = False

        t = time.time()
        if t - start >= timelapse:
            action = "STOP"
            for event in pygame.event.get():
                if event.type == QUIT:
                    continuer = 0
                if args.agent is None:
                    if event.type == KEYDOWN:
                        action = actions_mapping.get(event.key)

            if (not init_agent) and (threading.active_count() == 1) and args.agent is not None:
                action = agent.get_action()

            if not (gameState.is_win() or gameState.is_game_over()):
                gameState = gameState.execute_action(action)
            draw_world(window, blocks, block_size, gameState, font, window_size)
            start = time.time()


if __name__ == '__main__':
    main()


from pacman.maze import Maze
from pacman.ghost import Ghost


class Level:
	def __init__(self, maze: Maze):
		self.maze = maze
		self.width = maze.width
		self.height = maze.height

		self.pacgums: set[tuple[int, int]] = set()
		self.superpacgums: set[tuple[int, int]] = set()

		self.ghosts: list[Ghost] = []

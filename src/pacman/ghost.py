

from enum import Enum


class GhostMode(Enum):
	CHASE = "chase"
	SCATTER = "scatter"
	FRIGHTENED = "frightened"


class Ghost:
	def __init__(self, name: str, color: str, position: tuple[int, int]):
		self.name = name
		self.color = color
		self.position = position
		self.mode = GhostMode.SCATTER

	def move(self, ...):
		# Implement ghost movement logic here
		pass

	TODO: add method to calculate current difficulty level based on level


class Blinky(Ghost):
	def __init__(self, position: tuple[int, int]):
		super().__init__("Blinky", "Red", position)


class Pinky(Ghost):
	def __init__(self, position: tuple[int, int]):
		super().__init__("Pinky", "Pink", position)


class Inky(Ghost):
	def __init__(self, position: tuple[int, int]):
		super().__init__("Inky", "Cyan", position)


class Clyde(Ghost):
	def __init__(self, position: tuple[int, int]):
		super().__init__("Clyde", "Orange", position)


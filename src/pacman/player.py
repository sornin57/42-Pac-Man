

class Player:
    def __init__(self, name: str, position: tuple[int, int]):
        self.name = name
        self.position = position
        self.score = 0
        self.lives = 3
        self.powered_up = False  # TODO: maybe should be a timer


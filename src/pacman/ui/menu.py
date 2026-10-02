from enum import Enum


class MenuAction(Enum):
    PLAY = "play"
    HIGHSCORES = "highscores"
    INSTRUCTIONS = "instructions"
    QUIT = "quit"


class Menu:
    ACTIONS = tuple(MenuAction)

    def __init__(self) -> None:
        self.selected_index = 0

    @property
    def selected_action(self) -> MenuAction:
        return self.ACTIONS[self.selected_index]

    def move_down(self) -> None:
        self.selected_index += 1

        if self.selected_index == len(self.ACTIONS):
            self.selected_index = 0

    def move_up(self) -> None:
        if self.selected_index == 0:
            self.selected_index = len(self.ACTIONS) - 1
        else:
            self.selected_index -= 1

    def select(self) -> MenuAction:
        return self.selected_action


if __name__ == "__main__":
    menu = Menu()

    assert menu.selected_action == MenuAction.PLAY

    menu.move_up()
    assert menu.selected_action == MenuAction.QUIT

    menu.move_down()
    assert menu.selected_action == MenuAction.PLAY

    menu.move_down()
    assert menu.selected_action == MenuAction.HIGHSCORES

    menu.move_down()
    assert menu.selected_action == MenuAction.INSTRUCTIONS

    menu.move_up()
    assert menu.selected_action == MenuAction.HIGHSCORES

    assert menu.select() == MenuAction.HIGHSCORES

    print("Tous les tests du menu sont passés.")

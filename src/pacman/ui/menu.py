from enum import Enum


class MenuAction(Enum):
    """Define the available main menu actions."""
    PLAY = "play"
    HIGHSCORES = "highscores"
    INSTRUCTIONS = "instructions"
    QUIT = "quit"


class Menu:
    """Manage main menu navigation and selection."""
    ACTIONS = tuple(MenuAction)

    def __init__(self) -> None:
        """Initialize the menu with the first action selected."""
        self.selected_index = 0

    @property
    def selected_action(self) -> MenuAction:
        """Return the currently highlighted menu action."""
        return self.ACTIONS[self.selected_index]

    def move_down(self) -> None:
        """Select the next action, wrapping to the first."""
        self.selected_index += 1

        if self.selected_index == len(self.ACTIONS):
            self.selected_index = 0

    def move_up(self) -> None:
        """Select the previous action, wrapping to the last."""
        if self.selected_index == 0:
            self.selected_index = len(self.ACTIONS) - 1
        else:
            self.selected_index -= 1

    def select(self) -> MenuAction:
        """Return the action chosen by the player."""
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

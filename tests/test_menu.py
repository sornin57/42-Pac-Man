from pacman.ui.menu import Menu, MenuAction


def test_menu_starts_on_play() -> None:
    """Select Play when the menu opens."""
    menu = Menu()
    assert menu.selected_action == MenuAction.PLAY


def test_move_down_visits_each_action_and_wraps() -> None:
    """Cycle downward through every menu action and wrap to Play."""
    menu = Menu()
    visited = []
    for _ in range(4):
        menu.move_down()
        visited.append(menu.selected_action)

    assert visited == [
        MenuAction.HIGHSCORES,
        MenuAction.INSTRUCTIONS,
        MenuAction.QUIT,
        MenuAction.PLAY,
    ]


def test_move_up_wraps_to_quit() -> None:
    """Wrap from Play to Quit when moving upward."""
    menu = Menu()

    menu.move_up()

    assert menu.selected_action == MenuAction.QUIT


def test_select_returns_current_action() -> None:
    """Return the currently highlighted action on selection."""
    menu = Menu()
    menu.move_down()

    assert menu.select() == MenuAction.HIGHSCORES

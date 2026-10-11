from pacman.ui.menu import Menu, MenuAction


def test_menu_starts_on_play() -> None:
    menu = Menu()
    assert menu.selected_action == MenuAction.PLAY


def test_move_down_visits_each_action_and_wraps() -> None:
    menu = Menu()

    menu.move_down()
    assert menu.selected_action == MenuAction.HIGHSCORES

    menu.move_down()
    assert menu.selected_action == MenuAction.INSTRUCTIONS

    menu.move_down()
    assert menu.selected_action == MenuAction.QUIT

    menu.move_down()
    assert menu.selected_action == MenuAction.PLAY


def test_move_up_wraps_to_quit() -> None:
    menu = Menu()

    menu.move_up()

    assert menu.selected_action == MenuAction.QUIT


def test_select_returns_current_action() -> None:
    menu = Menu()
    menu.move_down()

    assert menu.select() == MenuAction.HIGHSCORES

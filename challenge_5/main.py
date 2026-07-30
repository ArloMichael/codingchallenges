import questionary
from pathlib import Path
from random import choices

DEFAULT_DATABASE_PATH = Path("db.txt")
STARTING_MONEY = 100
CARDS = [
    ("Ace", 1), ("Two", 2), ("Three", 3), ("Four", 4), ("Five", 5),
    ("Six", 6), ("Seven", 7), ("Eight", 8), ("Nine", 9),
    ("Ten", 10), ("Jack", 10), ("Queen", 10), ("King", 10),
]


def select(message, options):
    return questionary.select(message, choices=options, erase_when_done=True).ask()


def draw(count=1):
    return choices(CARDS, k=count)


def names(hand):
    return ", ".join(card[0] for card in hand)


def load_highest_win(database_path):
    try:
        return int(database_path.read_text().splitlines()[0])
    except (FileNotFoundError, IndexError, ValueError):
        return 0


def save_highest_win(database_path, highest_win):
    database_path.write_text(str(highest_win))


def score(hand):
    value = sum(card[1] for card in hand)
    aces = sum(1 for card in hand if card[0] == "Ace")

    while aces and value + 10 <= 21:
        value += 10
        aces -= 1

    return value


def play_player_hand(player_name, hand, dealer):
    while (total := score(hand)) <= 21:
        print(f"{player_name}'s hand: {names(hand)} ({total})")
        print(f"Dealer shows: {dealer[0][0]}")

        choice = select(
            f"{player_name}, hit or stand?",
            [
                "Hit",
                "Stand",
            ],
        )

        if choice == "Hit":
            hand.extend(draw())
        elif choice in ("Stand", None):
            break


def settle_bet(player_score, dealer_score, bet):
    if player_score > 21 or (dealer_score <= 21 and player_score < dealer_score):
        return "LOSE", -bet
    if player_score == dealer_score:
        return "PUSH", 0
    return "WIN", bet


def play_round(bets):
    dealer = draw(2)
    hands = {player_name: draw(2) for player_name in bets}

    for player_name, hand in hands.items():
        print()
        play_player_hand(player_name, hand, dealer)

    if any(score(hand) <= 21 for hand in hands.values()):
        while score(dealer) < 17:
            dealer.extend(draw())

    dealer_score = score(dealer)
    print(f"Dealer hand: {names(dealer)} ({dealer_score})")

    winnings = {}

    for player_name, hand in hands.items():
        player_score = score(hand)
        result, player_winnings = settle_bet(player_score, dealer_score, bets[player_name])
        winnings[player_name] = player_winnings

        print(f"{player_name}'s hand: {names(hand)} ({player_score})")
        if result == "PUSH":
            print(f"{player_name} PUSH")
        else:
            print(f"{player_name} {result}: ${abs(player_winnings)}")

    return winnings


def main(database_path=DEFAULT_DATABASE_PATH):
    if not database_path.exists():
        option = select("The database file does not exist.", ["Create one", "Pick a file", "Exit"])

        if option == "Create one":
            database_path.touch()
        elif option == "Pick a file":
            selected_path = questionary.path(
                "What is the filepath?",
                validate=lambda x: (
                    x != ""
                    and Path(x).expanduser().exists()
                    and Path(x).expanduser().suffix == ".txt"
                ),
            ).ask()

            if selected_path is None:
                raise SystemExit

            database_path = Path(selected_path).expanduser()
        else:
            raise SystemExit

    players = {
        "Player 1": STARTING_MONEY,
        "Player 2": STARTING_MONEY,
    }
    highest_win = load_highest_win(database_path)

    while True:
        choice = select("Blackjack", ["Play", "Exit"])

        match choice:
            case "Play":
                mode = select("Choose game mode", ["Single player", "Two players"])

                if mode is None:
                    continue

                selected_players = {"Player 1": players["Player 1"]} if mode == "Single player" else players.copy()
                active_players = {name: money for name, money in selected_players.items() if money > 0}

                if not active_players:
                    print("Selected player is out of money.")
                    continue

                bets = {}

                for player_name, money in active_players.items():
                    def validate_bet(value):
                        value = value.strip()

                        if not value.isdigit():
                            return "Enter a whole dollar amount."

                        bet = int(value)

                        if bet <= 0:
                            return "Bet must be greater than 0."

                        if bet > money:
                            return f"You only have ${money}."

                        return True

                    bet = questionary.text(
                        f"{player_name}, you have ${money}. How much do you want to bet?",
                        validate=validate_bet,
                    ).ask()

                    if bet is None:
                        break

                    bets[player_name] = int(bet.strip())

                if len(bets) != len(active_players):
                    continue

                winnings = play_round(bets)

                for player_name, amount in winnings.items():
                    players[player_name] += amount
                    current_winnings = players[player_name] - STARTING_MONEY

                    if current_winnings > highest_win:
                        highest_win = current_winnings
                        save_highest_win(database_path, highest_win)
                        print(f"New highest win saved: ${highest_win}")

                for player_name in selected_players:
                    print(f"{player_name} money: ${players[player_name]}")
                print(f"Highest win: ${highest_win}")

                if all(players[player_name] <= 0 for player_name in active_players):
                    print("Selected player is out of money.")
                    break

            case "Exit" | None:
                break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass

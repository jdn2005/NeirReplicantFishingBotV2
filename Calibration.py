import json
import os


def prompt_selection(message, options, default=None):
    prompt = f"{message}"
    if default is not None:
        prompt += f" [default: {default}]"
    prompt += ": "

    while True:
        print(prompt)
        for i, option in enumerate(options, start=1):
            print(f"{i}. {option}")

        choice = input("Enter the number of your choice: ").strip()

        if choice == "":
            if default is not None:
                choice = str(default)
            else:
                print("Input is required.\n")
                continue

        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(options):
                return options[index]

        print("Invalid input. Please enter a valid number.\n")


def prompt_integer(message, default=None, min_value=None, max_value=None):
    prompt = f"{message}"
    if default is not None:
        prompt += f" [default: {default}]"
    prompt += ": "

    while True:
        user_input = input(prompt).strip()

        if user_input == "":
            if default is not None:
                return default
            else:
                print("Input is required.\n")
                continue

        try:
            value = int(user_input)
            if (min_value is not None and value < min_value) or \
               (max_value is not None and value > max_value):
                print(f"Please enter a number between {min_value} and {max_value}.\n")
                continue
            return value
        except ValueError:
            print("Invalid input. Please enter a valid integer.\n")


def run_calibration():
    """Run the calibration prompts and save results to config.json."""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

    print("This program expect Neir Replicant to be run in Borderless Window mode.")

    selection = prompt_selection(
        "Please select an aspect ratio for both the screen and the game",
        ["16:9", "16:10", "21:9"], 1
    )

    aspectRatio = 0
    if selection == "16:9":
        aspectRatio = 16 / 9.0
    elif selection == "16:10":
        aspectRatio = 16 / 10.0
    elif selection == "21:9":
        aspectRatio = 21 / 9.0

    selection = prompt_selection(
        "Please select a screen resolution",
        ["1080", "1440", "4k"]
    )

    if selection == "1080":
        screen_height = 1080
    elif selection == "1440":
        screen_height = 1440
    elif selection == "4k":
        screen_height = 2160
    screen_width = int(aspectRatio * screen_height)

    selection = prompt_selection(
        "Please select a game resolution",
        ["1080", "1440", "4k"]
    )

    if selection == "1080":
        game_height = 1080
    elif selection == "1440":
        game_height = 1440
    elif selection == "4k":
        game_height = 2160
    game_width = int(aspectRatio * game_height)

    bait_number = prompt_integer(
        "Please select how far down in the bait menu you want to go; 0 is the first bait", 0
    )

    number_of_attempts = prompt_integer(
        "Please select the number of attempts to do; -1 means don't stop", -1
    )

    config = {
        "screen_resolution": [screen_width, screen_height],
        "game_resolution": [game_width, game_height],
        "bait_number": bait_number,
        "number_of_attempts": number_of_attempts
    }

    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)

    print(f"\nConfiguration saved to {config_path}")
    print()
    return config


if __name__ == "__main__":
    run_calibration()

import sys
import time
import os
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom

from blessed import Terminal

from four_souls_mpc_formatter.version import APP_NAME, get_header_text
from four_souls_mpc_formatter.config import (
    default_config,
    load_config,
    reset_config_file,
    export_json,
)


if getattr(sys, "frozen", False):
    # If the application is running as stand-alone program
    working_dir = Path(os.getcwd())
else:
    # If the application is running as a script
    working_dir = Path(__file__).parent

config = default_config

config_path = working_dir / "config.json"
cards_path = Path("./cards")
card_back_path = cards_path / "card_backs"
expansion_path = cards_path / "expansions"
single_cards_path = expansion_path / "Singles"
orders_path = Path(config.get("orders_dir", "./orders"))

combine_card_types = config.get("combine_card_types", True)

# Image file extensions accepted by MakePlayingCards
card_img_exts = {".jpg", ".bmp", ".png", ".gif", ".tiff", ".pdf"}

# Vanilla Four Souls card types
base_card_types = {
    "bonus_soul",
    "character",
    "loot",
    "monster",
    "room",
    "starting_item",
    "treasure",
}

term = Terminal()

menu_items = [
    "Generate MakePlayingCards Order Files",
    "Reset Config File to Default",
    "Create Working Directories",
    "Exit",
]
selected_index = 0


class Card:
    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.file_name = self.path.name

    def to_dict(self):
        return {
            "name": self.name,
            "path": str(self.path.resolve()),
            "file_name": self.file_name,
        }

    def __repr__(self):
        return f"<Four Souls Card - {self.name}>"


class Expansion:
    def __init__(self, name):
        self.name = name
        self.formatted_name = format_card_type(self.name)
        self.card_types = {}

    def to_dict(self):
        return {
            "name": self.name,
            "formatted_name": self.formatted_name,
            "card_types": self.card_types,
        }

    def create_card_type(self, card_type_name):
        formatted_name = format_card_type(card_type_name)
        if formatted_name not in self.card_types:
            self.card_types[formatted_name] = CardType(card_type_name)
        return self

    def has_card_type(self, card_type_name):
        return format_card_type(card_type_name) in self.card_types

    def add_card_type(self, card_type):
        if not type(card_type) == CardType:
            print(f"Expected a CardType, recieved {type(card_type)}.")
            return self
        if not self.has_card_type(card_type.formatted_name):
            self.card_types[card_type.formatted_name] = card_type
        return self

    def get_total_cards(self):
        total = 0
        for card_type in self.card_types:
            total += len(self.card_types[card_type].cards)
        return total

    def __repr__(self):
        return f"<Expansion - {self.name} ({self.get_total_cards()})>"


class CardType:
    def __init__(self, name):
        self.name = name
        self.cards = []
        self.formatted_name = format_card_type(name)
        self.card_back_path = ""

    def to_dict(self):
        dict = {
            "name": self.name,
            "formatted_name": self.formatted_name,
            "cards": self.cards,
        }
        if str(self.card_back_path) != "":
            dict["card_back_path"] = str(self.card_back_path.resolve())
        return dict

    def set_card_back(self, path):
        self.card_back_path = path
        return self

    def add_cards(self, cards):
        if not isinstance(cards, list):
            cards = [cards]
        for card in cards:
            self.cards.append(card)
        return self

    def clear_cards(self):
        self.cards = []
        return self

    def __repr__(self):
        return f"<CardType - {self.name} ({len(self.cards)})>"


def expansions_to_dict(expansions):
    return {name: expansion.to_dict() for name, expansion in expansions.items()}


def create_xml(expansion, card_type_name, output_path, card_back_file):
    card_type = expansion.card_types[card_type_name]

    # Don't create the file if there's no cards
    if not card_type.cards:
        return

    filename = f"order_{expansion.name.replace(' ', '_')}_{card_type.name.replace(' ', '_')}.xml"

    output_path.mkdir(parents=True, exist_ok=True)

    root = ET.Element("order")

    details = ET.SubElement(root, "details")
    ET.SubElement(details, "quantity").text = str(len(card_type.cards))
    ET.SubElement(details, "bracket").text = str(get_deck_size(len(card_type.cards)))
    ET.SubElement(details, "stock").text = "(M31) Linen"
    ET.SubElement(details, "foil").text = "false"

    fronts = ET.SubElement(root, "fronts")
    slot_index = 0

    for card in card_type.cards:
        card_front = ET.SubElement(fronts, "cards")
        ET.SubElement(card_front, "id").text = str(card.path.resolve())
        ET.SubElement(card_front, "slots").text = str(slot_index)
        ET.SubElement(card_front, "name").text = card.file_name
        ET.SubElement(card_front, "query").text = card.name

        slot_index += 1

    ET.SubElement(root, "cardback").text = str(card_back_file.resolve())

    file_path = output_path / filename
    xml_string = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    pretty_xml = minidom.parseString(xml_string).toprettyxml(indent="    ")
    with file_path.resolve().open("w", encoding="utf-8") as f:
        f.write(pretty_xml)
    print(f"Exported {expansion} :: {card_type} to {file_path.resolve()}")

    return


def get_deck_size(number_of_cards):
    deck_sizes = [
        18,
        36,
        55,
        72,
        90,
        108,
        126,
        144,
        162,
        180,
        198,
        216,
        234,
        396,
        504,
        612,
    ]
    for size in deck_sizes:
        if number_of_cards <= size:
            return size
    return deck_sizes[-1]


def assert_base_card_backs():
    for card_type in config["card_backs"]:
        if not Path(config["card_backs"][card_type]).is_file():
            raise FileNotFoundError(
                f'Card back for card type, {card_type}, not found: {Path(config["card_backs"][card_type]).resolve()}'
            )


def assert_single_card_back(dir):
    return len(get_valid_cards(dir)) == 1


def assert_valid_image_extension(file):
    return file.suffix in card_img_exts


def assert_unique_dir_names(dirs):
    formatted_names = set()
    for dir in dirs.iterdir():
        if dir.is_dir():
            formatted_name = format_card_type(dir.name)
            if formatted_name in formatted_names:
                return False
            formatted_names.add(formatted_name)
    return True


def assert_unique_card_names(expansions):
    seen_cards = set()
    duplicates = []

    for expansion_name, expansion in expansions.items():
        for card_type_name, card_type in expansion.card_types.items():
            for card in card_type.cards:
                if card.file_name in seen_cards:
                    duplicates.append(card.file_name)
                    pass
                else:
                    seen_cards.add(card.file_name)

    return duplicates


def assert_card_back_dir(dir):
    if not type(dir) == Path:
        dir = Path(dir)
    if not dir.is_dir():
        return False
    if format_card_type(dir.name) != "card_back":
        return False
    cards = get_valid_cards(dir)
    if len(cards) != 1:
        return False
    return True


def format_card_type(card_type):
    return card_type.strip().lower().replace(" ", "_")


def get_valid_images(dir):
    return [x for x in dir.iterdir() if assert_valid_image_extension(x)]


def get_valid_cards(dir):
    return [Card(x.stem, x) for x in get_valid_images(dir)]


def create_directories():
    directories = [
        cards_path,
        card_back_path,
        expansion_path,
        single_cards_path,
        orders_path,
    ]
    new_dir_created = False
    for directory in directories:
        if not directory.is_dir():
            directory.mkdir()
            try:
                get_path = directory.relative_to(working_dir)
            except ValueError:
                get_path = directory.resolve()
            print(f"Created directory: {get_path}")
            new_dir_created = True
    if not new_dir_created:
        print("All working directories already exist.")
    wait_for_anykey()


def menu_reset_config():
    reset_config_file(config_path)
    print(f"Config JSON file saved to: {config_path.resolve()}")
    wait_for_anykey()


def format_cards():
    assert_base_card_backs()

    cards = {"expansions": {}}

    # OS should handle unique names, but check just in case
    if False in [
        assert_unique_dir_names(single_cards_path),
        assert_unique_dir_names(expansion_path),
    ]:
        print(
            f"<WARNING> Not all expansion folders have unique names.\nExpansions with the same formatted names will be combined."
        )

    # Process expansions
    for expansion_dir in expansion_path.iterdir():
        if not expansion_dir.is_dir():
            continue

        if not assert_unique_dir_names(expansion_dir):
            print(
                f"<WARNING> {expansion_dir.name} expansion - not all card type folders have a unique name."
            )

        expansion = Expansion(expansion_dir.name)
        is_singles = expansion.formatted_name == "singles"
        add_expansion = False

        for card_type_dir in expansion_dir.iterdir():
            if not card_type_dir.is_dir():
                continue

            valid_cards = get_valid_cards(card_type_dir)
            if valid_cards:
                add_expansion = True
                card_type = CardType(card_type_dir.name)
                is_base_card_type = card_type.formatted_name in base_card_types

                # Handle singles-specific logic
                if is_singles and not is_base_card_type:
                    card_back_dir = card_type_dir / "card_back"

                    if not card_back_dir.is_dir():
                        print(
                            f'<WARNING> Missing "card_back" folder in {expansion.name} {card_type}.'
                        )
                        continue

                    card_back_files = get_valid_images(card_back_dir)
                    if not card_back_files:
                        print(f"<WARNING> No card back files found in {card_back_dir}.")
                        continue

                    if len(card_back_files) != 1:
                        print(
                            f"<WARNING> Only a single card back file is required, found {len(card_back_files)} files."
                        )
                        continue

                    # Should only be one card back per card type
                    card_type.set_card_back(Path(card_back_files[0]))

            # Add expansion if it contains cards
            if add_expansion:
                card_type.add_cards(valid_cards)
                expansion.add_card_type(card_type)
                cards["expansions"][expansion.formatted_name] = expansion

    # Export all expansions to JSON file
    # export_json(cards, "expansions.json")

    # Consolidate base cards types for fewer XML files
    if combine_card_types:
        base_expansion = Expansion("Base Card Types")
        for expansion_name, expansion in list(cards["expansions"].items()):
            if expansion_name == "base_card_types":
                continue

            for card_type_name, card_type in list(expansion.card_types.items()):
                # Only work with base card types
                if card_type_name not in base_card_types:
                    continue

                # Create a Base Card Types Expansion if it doesn't exist
                if not base_expansion.has_card_type(card_type_name):
                    base_expansion.create_card_type(card_type.name)

                base_expansion.card_types[card_type_name].add_cards(card_type.cards)

                del expansion.card_types[card_type_name]

        if base_expansion.get_total_cards():
            cards["expansions"]["base_card_types"] = base_expansion

    # Loop over the expansions and create the XML files
    for expansion_name, expansion in cards["expansions"].items():
        for card_type_name, card_type in expansion.card_types.items():
            if card_type.formatted_name in base_card_types:
                card_back_file = Path(config["card_backs"][card_type.formatted_name])
            elif hasattr(card_type, "card_back_path"):
                card_back_file = Path(card_type.card_back_path)
            else:
                print(
                    f'<WARNING> {expansion.name} {card_type.name} is missing "card_back_path" attribute.'
                )

            create_xml(
                expansion,
                card_type_name,
                orders_path,
                card_back_file,
            )

    # Print card count summary
    # print_card_count_summary(cards["expansions"])

    # Check for duplicate card names
    duplicates = assert_unique_card_names(cards["expansions"])
    if duplicates:
        print(f"\n<WARNING> Found duplicate card file names: {', '.join(duplicates)}")
        print(
            "    There may be an issue with mpc-autofill assigning these cards to card slots."
        )
        print(
            "    Make sure to review your cards after the mpc-autofill program completes.\n"
        )


def print_card_count_summary(expansions):
    # Print out summary of card expansions
    print("\nCard Count Summary:")
    summary = {}

    for expansion_name, expansion in expansions.items():
        total_cards = sum(
            len(card_list.cards) for card_list in expansion.card_types.values()
        )
        summary[expansion_name] = total_cards

    for expansion_name, count in summary.items():
        print(f"  - {expansion_name}: {count} cards")

    print("-" * 30)
    print(f"Total Cards: {sum(summary.values())}")
    print("")


def main_menu():
    global selected_index

    blessed_draw_menu()
    key = term.inkey()

    if key.code == term.KEY_UP:
        selected_index = max((selected_index - 1), 0)
    elif key.code == term.KEY_DOWN:
        selected_index = min(len(menu_items) - 1, selected_index + 1)
    elif key.code == term.KEY_ENTER:
        item = menu_items[selected_index]
        if item == "Generate MakePlayingCards Order Files":
            format_cards()
            wait_for_anykey()
        elif item == "Reset Config File to Default":
            menu_reset_config()
        elif item == "Create Working Directories":
            create_directories()
        elif item == "Exit":
            program_end()
    elif key.code == term.KEY_ESCAPE:
        if menu_items[selected_index] == "Exit":
            program_end()
        else:
            selected_index = len(menu_items) - 1


def program_end():
    header()
    print(f"Thanks for using {APP_NAME}!\n\nExiting program.")
    time.sleep(1)
    sys.exit()


def blessed_draw_menu():
    header()
    for i, item in enumerate(menu_items):
        if i == selected_index:
            print(term.reverse(item))
        else:
            print(item)
    print("")


def wait_for_anykey():
    print("\nPress any key to continue.\n")
    term.inkey()


def header():
    print(f"{term.clear}{term.bold(get_header_text())}\n")


def main():
    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        load_config(config_path)
        while True:
            main_menu()


if __name__ == "__main__":
    main()

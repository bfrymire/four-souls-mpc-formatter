import json
from pathlib import Path


default_config = {
    "card_backs": {
        "bonus_soul": "./cards/card_backs/bonus_soul_card_back.jpg",
        "character": "./cards/card_backs/character_card_back.jpg",
        "loot": "./cards/card_backs/loot_card_back.jpg",
        "monster": "./cards/card_backs/monster_card_back.jpg",
        "room": "./cards/card_backs/room_card_back.jpg",
        "starting_item": "./cards/card_backs/starting_item_card_back.jpg",
        "treasure": "./cards/card_backs/treasure_card_back.jpg",
    },
    "orders_dir": "./orders",
    "combine_card_types": True,
}


class ExportEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        return super().default(obj)


def load_config(config_path):
    print(f"Looking for config file at: {config_path}")
    config_path = Path(config_path)
    if config_path.is_file():
        with open(config_path, "r") as file:
            config = json.load(file)
    else:
        print(
            f"<WARNING> Config file not found. Creating default config file at: {config_path}"
        )
        reset_config_file(config_path)
        config = default_config


def reset_config_file(path):
    with open(path, "w") as f:
        json.dump(default_config, f, indent=2)


def export_json(data, file_path):
    if type(file_path) == str:
        file_path = Path(file_path)
    with file_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, cls=ExportEncoder, ensure_ascii=False, indent=4)
    print(f"Cards exported to JSON file {file_path.resolve()}")

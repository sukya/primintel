import os
cow_root = os.path.abspath(os.path.join(os.getcwd(), "channel", "web", "..", ".."))
print(f"COW_ROOT: {cow_root}")

name = "bing-image-creator"
config_path = os.path.join(cow_root, "workspace", "skills", name, "resources", "config.json")
print(f"PATH: {config_path}")
print(f"EXISTS: {os.path.exists(config_path)}")

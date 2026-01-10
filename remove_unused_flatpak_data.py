# Copyright (C) 2026 Maryam Sheikh (Mahid Sheikh)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from pathlib import Path
import shutil

FLATPAK_SYSTEM_INSTALL = Path("/", "var", "lib", "flatpak", "app")
FLATPAK_LOCAL_INSTALL = Path(Path.home(), ".local", "share", "flatpak", "app")
FLATPAK_APP_CONFIG_DIR = Path(Path.home(), ".var", "app")

def main() -> None:
    list_of_apps: tuple[str, ...] = ()

    if FLATPAK_SYSTEM_INSTALL.exists():
        list_of_apps += tuple(dir.name for dir in FLATPAK_SYSTEM_INSTALL.iterdir())
    if FLATPAK_LOCAL_INSTALL.exists():
        list_of_apps += tuple(dir.name for dir in FLATPAK_LOCAL_INSTALL.iterdir())

    flatpak_config_dirs: tuple[Path, ...] = tuple(FLATPAK_APP_CONFIG_DIR.iterdir())
    leftover_directories: list[Path] = []

    for config_dir in flatpak_config_dirs:
        if config_dir.is_symlink():
            continue
        if (Path(config_dir, "cache").exists()
            and Path(config_dir, "config").exists()
            and Path(config_dir, "data").exists()
            and " " not in config_dir.name
            and config_dir.name not in list_of_apps
            and config_dir not in leftover_directories):
                leftover_directories.append(config_dir)

    if len(leftover_directories):
        for directory in leftover_directories:
            inputted = False
            remove = True

            while not inputted:
                user_input = input(f"Do you want to delete the following folder? [Y/n]: {str(directory)} ")
                if user_input.lower() in ('y', 'n', ''):
                    inputted = True
                    remove = user_input.lower == 'y' or user_input == ''

            if not remove:
                continue

            print(f"Removing {str(directory)}...")
            shutil.rmtree(directory)
    else:
        print("No directories to clean!")

if __name__ == "__main__":
    main()

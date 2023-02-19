import os.path
import shutil
from pathlib import Path
from typing import List

trash_files_list = [
    "__pycache__",
    ".pytest_cache",
]


def collect_trash() -> List[Path]:
    cur_path = Path(".")
    remove_list = []
    for trash in trash_files_list:
        remove_list += list(cur_path.rglob(f"./*{trash}"))
    return remove_list


def get_yes_no_input(msg: str) -> bool:
    ans = input(f"{msg} [Y/n]: ").lower() or 'y'
    if ans not in ['y', 'n']:
        raise ValueError("Incorrect response")
    print(ans, ans == 'y')
    return ans == 'y'


def remove_trash(trash_list: List[Path]):
    for trash in trash_list:
        if os.path.isfile(trash):
            os.remove(trash)
        elif os.path.isdir(trash):
            shutil.rmtree(trash)
        else:
            print(f"Warning: skip {trash}")


if __name__ == '__main__':
    remove_list = collect_trash()
    if not remove_list:
        print("Nothing to do here")
        exit(0)

    remove_list_str = list(map(lambda path: str(path), remove_list))
    to_remove = get_yes_no_input(f"The following files will be removed:\n{remove_list_str}\nContinue?")
    if not to_remove:
        print(f"Nothing to do here")
        exit(0)

    remove_trash(remove_list)
    print("Done")

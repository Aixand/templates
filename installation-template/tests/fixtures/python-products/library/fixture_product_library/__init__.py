from importlib.resources import files


def message():
    return files(__package__).joinpath("message.txt").read_text().strip()

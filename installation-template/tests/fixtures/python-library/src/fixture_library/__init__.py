from importlib.resources import files


def greet(name):
    template = files(__package__).joinpath("greeting.txt").read_text().strip()
    return template.format(name=name)

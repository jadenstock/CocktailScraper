import tomllib

def load_config(path="./etc/config.toml"):
    with open(path, "rb") as f:
        return tomllib.load(f)

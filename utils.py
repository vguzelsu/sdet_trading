import yaml


CONFIG_FILE = "config.yaml"
ENDPOINTS_FILE = "endpoints.yaml"


def read_yaml(yaml_fpath):
    with open(yaml_fpath, "r") as yamlfile:
        data = yaml.load(yamlfile, Loader=yaml.FullLoader)
        return data


def get_config():
    return read_yaml(CONFIG_FILE)


def get_endpoints():
    return read_yaml(ENDPOINTS_FILE)

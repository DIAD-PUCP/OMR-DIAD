import sys

from form import Form


def main(args):
    config_file = args[1]
    config = None
    with open(config_file) as f:
        json_config = f.read()
        config = Form.model_validate_json(json_config)
    print(config)


if __name__ == "__main__":
    main(sys.argv)
    exit(0)

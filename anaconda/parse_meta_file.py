# Copyright 2020-2021 The MathWorks, Inc.

# This file contains code used to publish the repository to Anaconda

from ruamel.yaml import YAML
from jupyter_matlab_proxy.jupyter_config import config


yaml = YAML()


def read_yaml_file(file_path):
    """Reads contents of yaml file

    Args:
        file_path (str): Path to the yaml file

    Returns:
        [str]: Text representing yaml content
    """
    with open(file_path) as f:
        file_content = f.readlines()
    return file_content


def filter_content(content):
    """Filters and seperates jinja text from yaml content

    Args:
        content (str): Text representing yaml content

    Returns:
        list: Containing jinja_text and yaml_text
    """
    jinja_text = content[:2]
    yaml_text = content[2:]

    return jinja_text, yaml_text


def modify_python_version(yaml_content):
    """Modifies python version in yaml_content.

    Args:
        yaml_content (str): Text representing yaml_content

    Returns:
        [str]: yaml content with updated python version
    """
    fields = ["host", "run"]

    for field in fields:
        try:
            python_index = yaml_content["requirements"][field].index("python")
            yaml_content["requirements"][field][python_index] = "python >=3.6"
        except ValueError:
            pass

    return yaml_content


def modify_about_section(yaml_content):
    """Modifies the about section.

    Args:
        yaml_content (str): Text representing yaml_content

    Returns:
        str: yaml_content with modified data
    """
    yaml_content["about"]["license_file"] = "../../LICENSE.md"
    yaml_content["about"]["doc_url"] = config["doc_url"]
    yaml_content["about"]["dev_url"] = config["doc_url"]

    return yaml_content


def modify_extra_section(yaml_content):
    """Modifies extra's section of the yaml_content.

    Args:
        yaml_content (str): Text representing yaml content

    Returns:
        [str]: yaml_content with extra's section modified
    """
    yaml_content["extra"]["recipe-maintainers"] = ["prabhakk-mw", "diningPhilosopher64"]
    return yaml_content


def write_modified_yaml(jinja_text, yaml_content, yaml_file_path):
    """This method dumps jinja content as well as the modified yaml content

    Args:
        jinja_text (str): Text containing jinja templating
        yaml_content (str): Text containing yaml content
        yaml_file_path (str): Path to the file where jinja_text and yaml_content will be written to
    """
    with open(yaml_file_path, "w") as f:
        f.write("".join(jinja_text))
        f.write("\n")

    with open(yaml_file_path, "a") as f:
        yaml.dump(yaml_content, f)


if __name__ == "__main__":
    content = read_yaml_file("jupyter-matlab-proxy/meta.yaml")
    jinja_text, yaml_text = filter_content(content)

    yaml_content = yaml.load("".join(yaml_text))
    yaml_content = modify_python_version(yaml_content)
    yaml_content = modify_about_section(yaml_content)
    yaml_content = modify_extra_section(yaml_content)

    yaml_file_path = "jupyter-matlab-proxy/meta.yaml"
    write_modified_yaml(jinja_text, yaml_content, yaml_file_path)

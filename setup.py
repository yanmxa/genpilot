from setuptools import setup, find_packages
import io
import os


def read(*paths, **kwargs):
    """Read the contents of a text file safely.
    >>> read("project_name", "VERSION")
    '0.1.0'
    >>> read("README.md")
    ...
    """

    content = ""
    with io.open(
        os.path.join(os.path.dirname(__file__), *paths),
        encoding=kwargs.get("encoding", "utf8"),
    ) as open_file:
        content = open_file.read().strip()
    return content


setup(
    name="zen-agent",
    version="0.1.7",
    packages=find_packages(),
    description="ZenAgent facilitates the creation of AI assistant and the development of advanced multi-agent system.",
    author="Meng Yan",
    author_email="yanmxa@gmail.com",
    include_package_data=True,
    package_data={"": ["prompt/*"]},
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    install_requires=["boto3"],
    url="https://github.com/yanmxa/zen-agent",
)

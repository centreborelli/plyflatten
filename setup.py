import os
import subprocess
from codecs import open

from setuptools import setup
from setuptools.command import build_py, develop

here = os.path.abspath(os.path.dirname(__file__))

package = "plyflatten"

about = {}
with open(os.path.join(here, package, "__about__.py"), "r", "utf-8") as f:
    exec(f.read(), about)


def readme():
    with open(os.path.join(here, "README.md"), "r", "utf-8") as f:
        return f.read()


class CustomDevelop(develop.develop):
    """
    Class needed for "pip install -e ."
    """

    def run(self):
        subprocess.check_call("make lib", shell=True)
        super(CustomDevelop, self).run()


class CustomBuildPy(build_py.build_py):
    """
    Class needed for "pip install plyflatten"
    """

    def run(self):
        super(CustomBuildPy, self).run()
        subprocess.check_call("make lib", shell=True)
        subprocess.check_call("cp -r lib build/lib/", shell=True)


install_requires = ["affine", "numpy", "plyfile", "pyproj"]

extras_require = {"dev": ["bump2version", "pre-commit"], "test": ["pytest", "pytest-cov"]}

setup(
    name=about["__title__"],
    version=about["__version__"],
    description=about["__description__"],
    long_description=readme(),
    long_description_content_type="text/markdown",
    url=about["__url__"],
    author=about["__author__"],
    author_email=about["__author_email__"],
    packages=[package],
    install_requires=install_requires,
    extras_require=extras_require,
    entry_points="""
          [console_scripts]
          plyflatten=plyflatten.cli:main
      """,
    cmdclass={"develop": CustomDevelop, "build_py": CustomBuildPy},
)

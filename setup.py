from setuptools import setup

setup(
    name="slash_cog",
    version="0.0.3",
    description="A drop-in vanilla discord.py cog to add slash command support with little to no code modifications",
    url="https://github.com/CortexPE/slash_cog",
    author="CortexPE",
    license="MIT",
    packages=["slash_cog"],
    zip_safe=False,
    install_requires=["discord.py @ git+github.com/Rapptz/discord.py@master", "docstring-parser==0.14.1"],
    python_requires=">=3.6",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 1 - Planning",
        "Framework :: AsyncIO",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Communications :: Chat",
        "Topic :: Internet",
        "Typing :: Typed",
    ]
)

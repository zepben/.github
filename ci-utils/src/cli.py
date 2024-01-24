import os
import sys

import click


class Environment:
    def __init__(self):
        self.verbose = False
        self.home = os.getcwd()

    def info(self, msg, *args):
        """Logs a message to stderr."""
        if args:
            msg %= args
        click.echo(msg, file=sys.stderr)

    def debug(self, msg, *args):
        """Logs a message to stderr only if verbose is enabled."""
        if self.verbose:
            self.log(msg, *args)

    def err(self, msg, *args):
        """ Logs an error to stdout """
        click.echo(msg, *args)

    def warn(self, msg, *args):
        """ Logs an warning to stdout """
        print(" ctx.warn is not implemented yet!")
        pass


pass_environment = click.make_pass_decorator(Environment, ensure=True)
cmd_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "commands"))


class ComplexCLI(click.Group):
    def list_commands(self, ctx):
        rv = []
        for filename in os.listdir(cmd_folder):
            if filename.endswith(".py") and filename.startswith("cmd_"):
                rv.append(filename[4:-3])
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        try:
            mod = __import__(f"src.commands.cmd_{name}", None, None, ["cli"])
        except ImportError:
            return
        return mod.cli


@click.command(cls=ComplexCLI)
@click.option("-v", "--version", is_flag=True, help="Show version")
@pass_environment
def cli(ctx, version):
    """Zepben CI utilities"""
    click.echo("Let's go")

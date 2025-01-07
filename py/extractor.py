from word_extractor import process as word_extractor_process
import click

@click.group()
def cli():
    """Archive extractor CLI tool"""
    pass

@cli.command()
@click.argument('path', type=click.Path(exists=True))
def docx_convert(path: str):
    out_path = word_extractor_process(path)
    click.echo(f"Converted file saved to: {out_path}")

if __name__ == "__main__":
    cli()
    
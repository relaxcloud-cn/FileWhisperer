import click
import grpc
import file_whisper_pb2
import file_whisper_pb2_grpc

@click.group()
def cli():
    """Archive extractor CLI tool"""
    pass

@cli.command()
@click.option('--host', default='localhost', help='gRPC server host')
@click.option('--port', default=50051, help='gRPC server port')
@click.argument('path', type=click.Path(exists=True))
def run(host, port, path):
    with grpc.insecure_channel(f'{host}:{port}') as channel:
        stub = file_whisper_pb2_grpc.WhisperStub(channel)
        response = stub.Whispering(file_whisper_pb2.WhisperRequest(path=path))
        
    print(response)


if __name__ == "__main__":
    run()
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
@click.option('--binary', is_flag=True, help='Send file as binary content instead of path')
@click.argument('path', type=click.Path(exists=True))
def run(host, port, binary, path):
    with grpc.insecure_channel(f'{host}:{port}') as channel:
        stub = file_whisper_pb2_grpc.WhisperStub(channel)
        
        if binary:
            with open(path, 'rb') as f:
                file_content = f.read()
            request = file_whisper_pb2.WhisperRequest(file_content=file_content)
        else:
            request = file_whisper_pb2.WhisperRequest(file_path=path)
            
        response = stub.Whispering(request)
        
    print(response)

if __name__ == "__main__":
    cli()
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
        
        for node in response.tree:
            print(f"Node ID: {node.id}")
            print(f"Parent ID: {node.parent_id}")
            print(f"Children: {node.children}")
            
            if node.HasField('file'):
                file = node.file
                print(f"File: {file.path}")
                print(f"Name: {file.name}")
                print(f"Size: {file.size}")
                print(f"MIME Type: {file.mime_type}")
                print(f"Extension: {file.extension}")
                print(f"MD5: {file.md5}")
                print(f"SHA256: {file.sha256}")
                if file.HasField('content'):
                    print(f"Content length: {len(file.content)}")
            elif node.HasField('data'):
                data = node.data
                print(f"Data type: {data.type}")
                print(f"Content length: {len(data.content)}")
            
            if node.HasField('meta'):
                meta = node.meta
                if meta.map_string:
                    print("Meta Strings:")
                    for key, value in meta.map_string.items():
                        print(f"  {key}: {value}")
                if meta.map_number:
                    print("Meta Numbers:")
                    for key, value in meta.map_number.items():
                        print(f"  {key}: {value}")
                if meta.map_bool:
                    print("Meta Booleans:")
                    for key, value in meta.map_bool.items():
                        print(f"  {key}: {value}")
            
            print("---")

if __name__ == "__main__":
    cli()
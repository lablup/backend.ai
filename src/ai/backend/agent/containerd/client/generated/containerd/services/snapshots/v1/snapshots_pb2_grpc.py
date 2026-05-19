"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings
from .....containerd.services.snapshots.v1 import snapshots_pb2 as containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
GRPC_GENERATED_VERSION = '1.80.0'
GRPC_VERSION = grpc.__version__
_version_not_supported = False
try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True
if _version_not_supported:
    raise RuntimeError(f'The grpc package installed is at version {GRPC_VERSION},' + ' but the generated code in containerd/services/snapshots/v1/snapshots_pb2_grpc.py depends on' + f' grpcio>={GRPC_GENERATED_VERSION}.' + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}' + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.')

class SnapshotsStub(object):
    """Snapshot service manages snapshots
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Prepare = channel.unary_unary('/containerd.services.snapshots.v1.Snapshots/Prepare', request_serializer=containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.PrepareSnapshotRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.PrepareSnapshotResponse.FromString, _registered_method=True)
        self.View = channel.unary_unary('/containerd.services.snapshots.v1.Snapshots/View', request_serializer=containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.ViewSnapshotRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.ViewSnapshotResponse.FromString, _registered_method=True)
        self.Mounts = channel.unary_unary('/containerd.services.snapshots.v1.Snapshots/Mounts', request_serializer=containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.MountsRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.MountsResponse.FromString, _registered_method=True)
        self.Commit = channel.unary_unary('/containerd.services.snapshots.v1.Snapshots/Commit', request_serializer=containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.CommitSnapshotRequest.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, _registered_method=True)
        self.Remove = channel.unary_unary('/containerd.services.snapshots.v1.Snapshots/Remove', request_serializer=containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.RemoveSnapshotRequest.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, _registered_method=True)
        self.Stat = channel.unary_unary('/containerd.services.snapshots.v1.Snapshots/Stat', request_serializer=containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.StatSnapshotRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.StatSnapshotResponse.FromString, _registered_method=True)
        self.Update = channel.unary_unary('/containerd.services.snapshots.v1.Snapshots/Update', request_serializer=containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.UpdateSnapshotRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.UpdateSnapshotResponse.FromString, _registered_method=True)
        self.List = channel.unary_stream('/containerd.services.snapshots.v1.Snapshots/List', request_serializer=containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.ListSnapshotsRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.ListSnapshotsResponse.FromString, _registered_method=True)
        self.Usage = channel.unary_unary('/containerd.services.snapshots.v1.Snapshots/Usage', request_serializer=containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.UsageRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.UsageResponse.FromString, _registered_method=True)
        self.Cleanup = channel.unary_unary('/containerd.services.snapshots.v1.Snapshots/Cleanup', request_serializer=containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.CleanupRequest.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, _registered_method=True)

class SnapshotsServicer(object):
    """Snapshot service manages snapshots
    """

    def Prepare(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def View(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Mounts(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Commit(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Remove(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Stat(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Update(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def List(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Usage(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Cleanup(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_SnapshotsServicer_to_server(servicer, server):
    rpc_method_handlers = {'Prepare': grpc.unary_unary_rpc_method_handler(servicer.Prepare, request_deserializer=containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.PrepareSnapshotRequest.FromString, response_serializer=containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.PrepareSnapshotResponse.SerializeToString), 'View': grpc.unary_unary_rpc_method_handler(servicer.View, request_deserializer=containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.ViewSnapshotRequest.FromString, response_serializer=containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.ViewSnapshotResponse.SerializeToString), 'Mounts': grpc.unary_unary_rpc_method_handler(servicer.Mounts, request_deserializer=containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.MountsRequest.FromString, response_serializer=containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.MountsResponse.SerializeToString), 'Commit': grpc.unary_unary_rpc_method_handler(servicer.Commit, request_deserializer=containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.CommitSnapshotRequest.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString), 'Remove': grpc.unary_unary_rpc_method_handler(servicer.Remove, request_deserializer=containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.RemoveSnapshotRequest.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString), 'Stat': grpc.unary_unary_rpc_method_handler(servicer.Stat, request_deserializer=containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.StatSnapshotRequest.FromString, response_serializer=containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.StatSnapshotResponse.SerializeToString), 'Update': grpc.unary_unary_rpc_method_handler(servicer.Update, request_deserializer=containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.UpdateSnapshotRequest.FromString, response_serializer=containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.UpdateSnapshotResponse.SerializeToString), 'List': grpc.unary_stream_rpc_method_handler(servicer.List, request_deserializer=containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.ListSnapshotsRequest.FromString, response_serializer=containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.ListSnapshotsResponse.SerializeToString), 'Usage': grpc.unary_unary_rpc_method_handler(servicer.Usage, request_deserializer=containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.UsageRequest.FromString, response_serializer=containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.UsageResponse.SerializeToString), 'Cleanup': grpc.unary_unary_rpc_method_handler(servicer.Cleanup, request_deserializer=containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.CleanupRequest.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString)}
    generic_handler = grpc.method_handlers_generic_handler('containerd.services.snapshots.v1.Snapshots', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('containerd.services.snapshots.v1.Snapshots', rpc_method_handlers)

class Snapshots(object):
    """Snapshot service manages snapshots
    """

    @staticmethod
    def Prepare(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.snapshots.v1.Snapshots/Prepare', containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.PrepareSnapshotRequest.SerializeToString, containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.PrepareSnapshotResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def View(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.snapshots.v1.Snapshots/View', containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.ViewSnapshotRequest.SerializeToString, containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.ViewSnapshotResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Mounts(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.snapshots.v1.Snapshots/Mounts', containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.MountsRequest.SerializeToString, containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.MountsResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Commit(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.snapshots.v1.Snapshots/Commit', containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.CommitSnapshotRequest.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Remove(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.snapshots.v1.Snapshots/Remove', containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.RemoveSnapshotRequest.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Stat(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.snapshots.v1.Snapshots/Stat', containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.StatSnapshotRequest.SerializeToString, containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.StatSnapshotResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Update(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.snapshots.v1.Snapshots/Update', containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.UpdateSnapshotRequest.SerializeToString, containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.UpdateSnapshotResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def List(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_stream(request, target, '/containerd.services.snapshots.v1.Snapshots/List', containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.ListSnapshotsRequest.SerializeToString, containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.ListSnapshotsResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Usage(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.snapshots.v1.Snapshots/Usage', containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.UsageRequest.SerializeToString, containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.UsageResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Cleanup(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.snapshots.v1.Snapshots/Cleanup', containerd_dot_services_dot_snapshots_dot_v1_dot_snapshots__pb2.CleanupRequest.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)
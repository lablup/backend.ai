"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings
from .....containerd.services.tasks.v1 import tasks_pb2 as containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2
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
    raise RuntimeError(f'The grpc package installed is at version {GRPC_VERSION},' + ' but the generated code in containerd/services/tasks/v1/tasks_pb2_grpc.py depends on' + f' grpcio>={GRPC_GENERATED_VERSION}.' + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}' + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.')

class TasksStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Create = channel.unary_unary('/containerd.services.tasks.v1.Tasks/Create', request_serializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.CreateTaskRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.CreateTaskResponse.FromString, _registered_method=True)
        self.Start = channel.unary_unary('/containerd.services.tasks.v1.Tasks/Start', request_serializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.StartRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.StartResponse.FromString, _registered_method=True)
        self.Delete = channel.unary_unary('/containerd.services.tasks.v1.Tasks/Delete', request_serializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.DeleteTaskRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.DeleteResponse.FromString, _registered_method=True)
        self.DeleteProcess = channel.unary_unary('/containerd.services.tasks.v1.Tasks/DeleteProcess', request_serializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.DeleteProcessRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.DeleteResponse.FromString, _registered_method=True)
        self.Get = channel.unary_unary('/containerd.services.tasks.v1.Tasks/Get', request_serializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.GetRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.GetResponse.FromString, _registered_method=True)
        self.List = channel.unary_unary('/containerd.services.tasks.v1.Tasks/List', request_serializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.ListTasksRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.ListTasksResponse.FromString, _registered_method=True)
        self.Kill = channel.unary_unary('/containerd.services.tasks.v1.Tasks/Kill', request_serializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.KillRequest.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, _registered_method=True)
        self.Exec = channel.unary_unary('/containerd.services.tasks.v1.Tasks/Exec', request_serializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.ExecProcessRequest.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, _registered_method=True)
        self.ResizePty = channel.unary_unary('/containerd.services.tasks.v1.Tasks/ResizePty', request_serializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.ResizePtyRequest.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, _registered_method=True)
        self.CloseIO = channel.unary_unary('/containerd.services.tasks.v1.Tasks/CloseIO', request_serializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.CloseIORequest.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, _registered_method=True)
        self.Pause = channel.unary_unary('/containerd.services.tasks.v1.Tasks/Pause', request_serializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.PauseTaskRequest.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, _registered_method=True)
        self.Resume = channel.unary_unary('/containerd.services.tasks.v1.Tasks/Resume', request_serializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.ResumeTaskRequest.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, _registered_method=True)
        self.ListPids = channel.unary_unary('/containerd.services.tasks.v1.Tasks/ListPids', request_serializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.ListPidsRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.ListPidsResponse.FromString, _registered_method=True)
        self.Checkpoint = channel.unary_unary('/containerd.services.tasks.v1.Tasks/Checkpoint', request_serializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.CheckpointTaskRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.CheckpointTaskResponse.FromString, _registered_method=True)
        self.Update = channel.unary_unary('/containerd.services.tasks.v1.Tasks/Update', request_serializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.UpdateTaskRequest.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, _registered_method=True)
        self.Metrics = channel.unary_unary('/containerd.services.tasks.v1.Tasks/Metrics', request_serializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.MetricsRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.MetricsResponse.FromString, _registered_method=True)
        self.Wait = channel.unary_unary('/containerd.services.tasks.v1.Tasks/Wait', request_serializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.WaitRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.WaitResponse.FromString, _registered_method=True)

class TasksServicer(object):
    """Missing associated documentation comment in .proto file."""

    def Create(self, request, context):
        """Create a task.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Start(self, request, context):
        """Start a process.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Delete(self, request, context):
        """Delete a task and on disk state.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def DeleteProcess(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Get(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def List(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Kill(self, request, context):
        """Kill a task or process.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Exec(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ResizePty(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def CloseIO(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Pause(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Resume(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ListPids(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Checkpoint(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Update(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Metrics(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Wait(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_TasksServicer_to_server(servicer, server):
    rpc_method_handlers = {'Create': grpc.unary_unary_rpc_method_handler(servicer.Create, request_deserializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.CreateTaskRequest.FromString, response_serializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.CreateTaskResponse.SerializeToString), 'Start': grpc.unary_unary_rpc_method_handler(servicer.Start, request_deserializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.StartRequest.FromString, response_serializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.StartResponse.SerializeToString), 'Delete': grpc.unary_unary_rpc_method_handler(servicer.Delete, request_deserializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.DeleteTaskRequest.FromString, response_serializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.DeleteResponse.SerializeToString), 'DeleteProcess': grpc.unary_unary_rpc_method_handler(servicer.DeleteProcess, request_deserializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.DeleteProcessRequest.FromString, response_serializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.DeleteResponse.SerializeToString), 'Get': grpc.unary_unary_rpc_method_handler(servicer.Get, request_deserializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.GetRequest.FromString, response_serializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.GetResponse.SerializeToString), 'List': grpc.unary_unary_rpc_method_handler(servicer.List, request_deserializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.ListTasksRequest.FromString, response_serializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.ListTasksResponse.SerializeToString), 'Kill': grpc.unary_unary_rpc_method_handler(servicer.Kill, request_deserializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.KillRequest.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString), 'Exec': grpc.unary_unary_rpc_method_handler(servicer.Exec, request_deserializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.ExecProcessRequest.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString), 'ResizePty': grpc.unary_unary_rpc_method_handler(servicer.ResizePty, request_deserializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.ResizePtyRequest.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString), 'CloseIO': grpc.unary_unary_rpc_method_handler(servicer.CloseIO, request_deserializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.CloseIORequest.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString), 'Pause': grpc.unary_unary_rpc_method_handler(servicer.Pause, request_deserializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.PauseTaskRequest.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString), 'Resume': grpc.unary_unary_rpc_method_handler(servicer.Resume, request_deserializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.ResumeTaskRequest.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString), 'ListPids': grpc.unary_unary_rpc_method_handler(servicer.ListPids, request_deserializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.ListPidsRequest.FromString, response_serializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.ListPidsResponse.SerializeToString), 'Checkpoint': grpc.unary_unary_rpc_method_handler(servicer.Checkpoint, request_deserializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.CheckpointTaskRequest.FromString, response_serializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.CheckpointTaskResponse.SerializeToString), 'Update': grpc.unary_unary_rpc_method_handler(servicer.Update, request_deserializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.UpdateTaskRequest.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString), 'Metrics': grpc.unary_unary_rpc_method_handler(servicer.Metrics, request_deserializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.MetricsRequest.FromString, response_serializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.MetricsResponse.SerializeToString), 'Wait': grpc.unary_unary_rpc_method_handler(servicer.Wait, request_deserializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.WaitRequest.FromString, response_serializer=containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.WaitResponse.SerializeToString)}
    generic_handler = grpc.method_handlers_generic_handler('containerd.services.tasks.v1.Tasks', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('containerd.services.tasks.v1.Tasks', rpc_method_handlers)

class Tasks(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def Create(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.tasks.v1.Tasks/Create', containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.CreateTaskRequest.SerializeToString, containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.CreateTaskResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Start(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.tasks.v1.Tasks/Start', containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.StartRequest.SerializeToString, containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.StartResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Delete(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.tasks.v1.Tasks/Delete', containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.DeleteTaskRequest.SerializeToString, containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.DeleteResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def DeleteProcess(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.tasks.v1.Tasks/DeleteProcess', containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.DeleteProcessRequest.SerializeToString, containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.DeleteResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Get(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.tasks.v1.Tasks/Get', containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.GetRequest.SerializeToString, containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.GetResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def List(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.tasks.v1.Tasks/List', containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.ListTasksRequest.SerializeToString, containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.ListTasksResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Kill(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.tasks.v1.Tasks/Kill', containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.KillRequest.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Exec(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.tasks.v1.Tasks/Exec', containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.ExecProcessRequest.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def ResizePty(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.tasks.v1.Tasks/ResizePty', containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.ResizePtyRequest.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def CloseIO(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.tasks.v1.Tasks/CloseIO', containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.CloseIORequest.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Pause(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.tasks.v1.Tasks/Pause', containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.PauseTaskRequest.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Resume(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.tasks.v1.Tasks/Resume', containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.ResumeTaskRequest.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def ListPids(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.tasks.v1.Tasks/ListPids', containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.ListPidsRequest.SerializeToString, containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.ListPidsResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Checkpoint(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.tasks.v1.Tasks/Checkpoint', containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.CheckpointTaskRequest.SerializeToString, containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.CheckpointTaskResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Update(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.tasks.v1.Tasks/Update', containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.UpdateTaskRequest.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Metrics(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.tasks.v1.Tasks/Metrics', containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.MetricsRequest.SerializeToString, containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.MetricsResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Wait(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.tasks.v1.Tasks/Wait', containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.WaitRequest.SerializeToString, containerd_dot_services_dot_tasks_dot_v1_dot_tasks__pb2.WaitResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)
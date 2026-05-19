"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings
from .....containerd.services.images.v1 import images_pb2 as containerd_dot_services_dot_images_dot_v1_dot_images__pb2
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
    raise RuntimeError(f'The grpc package installed is at version {GRPC_VERSION},' + ' but the generated code in containerd/services/images/v1/images_pb2_grpc.py depends on' + f' grpcio>={GRPC_GENERATED_VERSION}.' + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}' + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.')

class ImagesStub(object):
    """Images is a service that allows one to register images with containerd.

    In containerd, an image is merely the mapping of a name to a content root,
    described by a descriptor. The behavior and state of image is purely
    dictated by the type of the descriptor.

    From the perspective of this service, these references are mostly shallow,
    in that the existence of the required content won't be validated until
    required by consuming services.

    As such, this can really be considered a "metadata service".
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Get = channel.unary_unary('/containerd.services.images.v1.Images/Get', request_serializer=containerd_dot_services_dot_images_dot_v1_dot_images__pb2.GetImageRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_images_dot_v1_dot_images__pb2.GetImageResponse.FromString, _registered_method=True)
        self.List = channel.unary_unary('/containerd.services.images.v1.Images/List', request_serializer=containerd_dot_services_dot_images_dot_v1_dot_images__pb2.ListImagesRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_images_dot_v1_dot_images__pb2.ListImagesResponse.FromString, _registered_method=True)
        self.Create = channel.unary_unary('/containerd.services.images.v1.Images/Create', request_serializer=containerd_dot_services_dot_images_dot_v1_dot_images__pb2.CreateImageRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_images_dot_v1_dot_images__pb2.CreateImageResponse.FromString, _registered_method=True)
        self.Update = channel.unary_unary('/containerd.services.images.v1.Images/Update', request_serializer=containerd_dot_services_dot_images_dot_v1_dot_images__pb2.UpdateImageRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_images_dot_v1_dot_images__pb2.UpdateImageResponse.FromString, _registered_method=True)
        self.Delete = channel.unary_unary('/containerd.services.images.v1.Images/Delete', request_serializer=containerd_dot_services_dot_images_dot_v1_dot_images__pb2.DeleteImageRequest.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, _registered_method=True)

class ImagesServicer(object):
    """Images is a service that allows one to register images with containerd.

    In containerd, an image is merely the mapping of a name to a content root,
    described by a descriptor. The behavior and state of image is purely
    dictated by the type of the descriptor.

    From the perspective of this service, these references are mostly shallow,
    in that the existence of the required content won't be validated until
    required by consuming services.

    As such, this can really be considered a "metadata service".
    """

    def Get(self, request, context):
        """Get returns an image by name.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def List(self, request, context):
        """List returns a list of all images known to containerd.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Create(self, request, context):
        """Create an image record in the metadata store.

        The name of the image must be unique.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Update(self, request, context):
        """Update assigns the name to a given target image based on the provided
        image.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Delete(self, request, context):
        """Delete deletes the image by name.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_ImagesServicer_to_server(servicer, server):
    rpc_method_handlers = {'Get': grpc.unary_unary_rpc_method_handler(servicer.Get, request_deserializer=containerd_dot_services_dot_images_dot_v1_dot_images__pb2.GetImageRequest.FromString, response_serializer=containerd_dot_services_dot_images_dot_v1_dot_images__pb2.GetImageResponse.SerializeToString), 'List': grpc.unary_unary_rpc_method_handler(servicer.List, request_deserializer=containerd_dot_services_dot_images_dot_v1_dot_images__pb2.ListImagesRequest.FromString, response_serializer=containerd_dot_services_dot_images_dot_v1_dot_images__pb2.ListImagesResponse.SerializeToString), 'Create': grpc.unary_unary_rpc_method_handler(servicer.Create, request_deserializer=containerd_dot_services_dot_images_dot_v1_dot_images__pb2.CreateImageRequest.FromString, response_serializer=containerd_dot_services_dot_images_dot_v1_dot_images__pb2.CreateImageResponse.SerializeToString), 'Update': grpc.unary_unary_rpc_method_handler(servicer.Update, request_deserializer=containerd_dot_services_dot_images_dot_v1_dot_images__pb2.UpdateImageRequest.FromString, response_serializer=containerd_dot_services_dot_images_dot_v1_dot_images__pb2.UpdateImageResponse.SerializeToString), 'Delete': grpc.unary_unary_rpc_method_handler(servicer.Delete, request_deserializer=containerd_dot_services_dot_images_dot_v1_dot_images__pb2.DeleteImageRequest.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString)}
    generic_handler = grpc.method_handlers_generic_handler('containerd.services.images.v1.Images', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('containerd.services.images.v1.Images', rpc_method_handlers)

class Images(object):
    """Images is a service that allows one to register images with containerd.

    In containerd, an image is merely the mapping of a name to a content root,
    described by a descriptor. The behavior and state of image is purely
    dictated by the type of the descriptor.

    From the perspective of this service, these references are mostly shallow,
    in that the existence of the required content won't be validated until
    required by consuming services.

    As such, this can really be considered a "metadata service".
    """

    @staticmethod
    def Get(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.images.v1.Images/Get', containerd_dot_services_dot_images_dot_v1_dot_images__pb2.GetImageRequest.SerializeToString, containerd_dot_services_dot_images_dot_v1_dot_images__pb2.GetImageResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def List(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.images.v1.Images/List', containerd_dot_services_dot_images_dot_v1_dot_images__pb2.ListImagesRequest.SerializeToString, containerd_dot_services_dot_images_dot_v1_dot_images__pb2.ListImagesResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Create(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.images.v1.Images/Create', containerd_dot_services_dot_images_dot_v1_dot_images__pb2.CreateImageRequest.SerializeToString, containerd_dot_services_dot_images_dot_v1_dot_images__pb2.CreateImageResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Update(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.images.v1.Images/Update', containerd_dot_services_dot_images_dot_v1_dot_images__pb2.UpdateImageRequest.SerializeToString, containerd_dot_services_dot_images_dot_v1_dot_images__pb2.UpdateImageResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Delete(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.images.v1.Images/Delete', containerd_dot_services_dot_images_dot_v1_dot_images__pb2.DeleteImageRequest.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)
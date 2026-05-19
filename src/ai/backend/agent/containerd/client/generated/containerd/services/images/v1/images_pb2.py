"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/services/images/v1/images.proto')
_sym_db = _symbol_database.Default()
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from google.protobuf import field_mask_pb2 as google_dot_protobuf_dot_field__mask__pb2
from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2
from .....containerd.types import descriptor_pb2 as containerd_dot_types_dot_descriptor__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n*containerd/services/images/v1/images.proto\x12\x1dcontainerd.services.images.v1\x1a\x1bgoogle/protobuf/empty.proto\x1a google/protobuf/field_mask.proto\x1a\x1fgoogle/protobuf/timestamp.proto\x1a!containerd/types/descriptor.proto"\x94\x02\n\x05Image\x12\x0c\n\x04name\x18\x01 \x01(\t\x12@\n\x06labels\x18\x02 \x03(\x0b20.containerd.services.images.v1.Image.LabelsEntry\x12,\n\x06target\x18\x03 \x01(\x0b2\x1c.containerd.types.Descriptor\x12.\n\ncreated_at\x18\x07 \x01(\x0b2\x1a.google.protobuf.Timestamp\x12.\n\nupdated_at\x18\x08 \x01(\x0b2\x1a.google.protobuf.Timestamp\x1a-\n\x0bLabelsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01"\x1f\n\x0fGetImageRequest\x12\x0c\n\x04name\x18\x01 \x01(\t"G\n\x10GetImageResponse\x123\n\x05image\x18\x01 \x01(\x0b2$.containerd.services.images.v1.Image"\x80\x01\n\x12CreateImageRequest\x123\n\x05image\x18\x01 \x01(\x0b2$.containerd.services.images.v1.Image\x125\n\x11source_date_epoch\x18\x02 \x01(\x0b2\x1a.google.protobuf.Timestamp"J\n\x13CreateImageResponse\x123\n\x05image\x18\x01 \x01(\x0b2$.containerd.services.images.v1.Image"\xb1\x01\n\x12UpdateImageRequest\x123\n\x05image\x18\x01 \x01(\x0b2$.containerd.services.images.v1.Image\x12/\n\x0bupdate_mask\x18\x02 \x01(\x0b2\x1a.google.protobuf.FieldMask\x125\n\x11source_date_epoch\x18\x03 \x01(\x0b2\x1a.google.protobuf.Timestamp"J\n\x13UpdateImageResponse\x123\n\x05image\x18\x01 \x01(\x0b2$.containerd.services.images.v1.Image"$\n\x11ListImagesRequest\x12\x0f\n\x07filters\x18\x01 \x03(\t"J\n\x12ListImagesResponse\x124\n\x06images\x18\x01 \x03(\x0b2$.containerd.services.images.v1.Image"n\n\x12DeleteImageRequest\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0c\n\x04sync\x18\x02 \x01(\x08\x121\n\x06target\x18\x03 \x01(\x0b2\x1c.containerd.types.DescriptorH\x00\x88\x01\x01B\t\n\x07_target2\x94\x04\n\x06Images\x12f\n\x03Get\x12..containerd.services.images.v1.GetImageRequest\x1a/.containerd.services.images.v1.GetImageResponse\x12k\n\x04List\x120.containerd.services.images.v1.ListImagesRequest\x1a1.containerd.services.images.v1.ListImagesResponse\x12o\n\x06Create\x121.containerd.services.images.v1.CreateImageRequest\x1a2.containerd.services.images.v1.CreateImageResponse\x12o\n\x06Update\x121.containerd.services.images.v1.UpdateImageRequest\x1a2.containerd.services.images.v1.UpdateImageResponse\x12S\n\x06Delete\x121.containerd.services.images.v1.DeleteImageRequest\x1a\x16.google.protobuf.EmptyB&Z$containerd/services/images/v1;imagesb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.services.images.v1.images_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z$containerd/services/images/v1;images'
    _globals['_IMAGE_LABELSENTRY']._loaded_options = None
    _globals['_IMAGE_LABELSENTRY']._serialized_options = b'8\x01'
    _globals['_IMAGE']._serialized_start = 209
    _globals['_IMAGE']._serialized_end = 485
    _globals['_IMAGE_LABELSENTRY']._serialized_start = 440
    _globals['_IMAGE_LABELSENTRY']._serialized_end = 485
    _globals['_GETIMAGEREQUEST']._serialized_start = 487
    _globals['_GETIMAGEREQUEST']._serialized_end = 518
    _globals['_GETIMAGERESPONSE']._serialized_start = 520
    _globals['_GETIMAGERESPONSE']._serialized_end = 591
    _globals['_CREATEIMAGEREQUEST']._serialized_start = 594
    _globals['_CREATEIMAGEREQUEST']._serialized_end = 722
    _globals['_CREATEIMAGERESPONSE']._serialized_start = 724
    _globals['_CREATEIMAGERESPONSE']._serialized_end = 798
    _globals['_UPDATEIMAGEREQUEST']._serialized_start = 801
    _globals['_UPDATEIMAGEREQUEST']._serialized_end = 978
    _globals['_UPDATEIMAGERESPONSE']._serialized_start = 980
    _globals['_UPDATEIMAGERESPONSE']._serialized_end = 1054
    _globals['_LISTIMAGESREQUEST']._serialized_start = 1056
    _globals['_LISTIMAGESREQUEST']._serialized_end = 1092
    _globals['_LISTIMAGESRESPONSE']._serialized_start = 1094
    _globals['_LISTIMAGESRESPONSE']._serialized_end = 1168
    _globals['_DELETEIMAGEREQUEST']._serialized_start = 1170
    _globals['_DELETEIMAGEREQUEST']._serialized_end = 1280
    _globals['_IMAGES']._serialized_start = 1283
    _globals['_IMAGES']._serialized_end = 1815
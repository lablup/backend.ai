from typing import Any, Dict, Mapping, Optional

import attrs

"""This file contains API templates for Python K8s Client.
Since I don't prefer using templates provided from vanila k8s client,
all API definitions for Backend.AI Agent will use needs to be defined here.
All API definitions defined here (especially for use with outside this file)
should implement to_dict() method, which returns complete definition in dictionary.
To pass API body from objects defined here, simply put return value of to_dict() method as a body:
e.g) await k8sCoreApi.create_persistent_volume(body=pv.to_dict())"""


class AbstractAPIObject:
    pass


@attrs.define(auto_attribs=True, slots=True)
class KubernetesVolumeMount:
    name: str
    mountPath: str
    subPath: Optional[str]
    readOnly: Optional[bool]


class KubernetesAbstractVolume:
    name: str


@attrs.define(auto_attribs=True, slots=True)
class KubernetesEmptyDirVolume(KubernetesAbstractVolume):
    name: str
    emptyDir: Mapping[str, Any] = {}


@attrs.define(auto_attribs=True, slots=True)
class KubernetesPVCVolume(KubernetesAbstractVolume):
    name: str
    persistentVolumeClaim: Mapping[str, str]


@attrs.define(auto_attribs=True, slots=True)
class KubernetesConfigMapVolume(KubernetesAbstractVolume):
    name: str
    configMap: Mapping[str, str]


@attrs.define(auto_attribs=True, slots=True)
class KubernetesHostPathVolume(KubernetesAbstractVolume):
    name: str
    hostPath: Mapping[str, str]


class ConfigMap(AbstractAPIObject):
    items: Dict[str, str] = {}

    def __init__(self, kernel_id, name: str):
        self.name = name
        self.labels = {"backend.ai/kernel-id": kernel_id}

    def put(self, key: str, value: str):
        self.items[key] = value

    def to_dict(self) -> dict:
        return {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": self.name,
                "labels": self.labels,
            },
            "data": self.items,
        }


class Service(AbstractAPIObject):
    def __init__(self, kernel_id: str, name: str, container_port: list, service_type="NodePort"):
        self.name = name
        self.deployment_name = f"kernel-{kernel_id}"
        self.container_port = container_port
        self.service_type = service_type
        self.labels = {"run": self.name, "backend.ai/kernel-id": kernel_id}

    def to_dict(self) -> dict:
        base: Dict[str, Any] = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": self.name,
                "labels": self.labels,
            },
            "spec": {
                "ports": [
                    {"targetPort": x[0], "port": x[0], "name": x[1]} for x in self.container_port
                ],
                "selector": {"run": self.deployment_name},
                "type": "",
            },
        }
        if self.service_type == "NodePort":
            base["spec"]["type"] = "NodePort"
        elif self.service_type == "LoadBalancer":
            base["spec"]["type"] = "LoadBalancer"
        return base


class NFSPersistentVolume(AbstractAPIObject):
    def __init__(self, server, name, capacity, path="/"):
        self.server = server
        self.path = path
        self.name = name
        self.capacity = capacity
        self.labels = {}
        self.options = []

    def label(self, k, v):
        self.labels[k] = v

    def to_dict(self) -> dict:
        return {
            "apiVersion": "v1",
            "kind": "PersistentVolume",
            "metadata": {
                "name": self.name,
                "labels": self.labels,
            },
            "spec": {
                "capacity": {
                    "storage": self.capacity + "Gi",
                },
                "accessModes": ["ReadWriteMany"],
                "nfs": {
                    "server": self.server,
                    "path": self.path,
                },
                "mountOptions": self.options,
            },
        }


class HostPathPersistentVolume(AbstractAPIObject):
    def __init__(self, path, name, capacity):
        self.path = path
        self.name = name
        self.capacity = capacity
        self.labels = {}
        self.options = []

    def label(self, k, v):
        self.labels[k] = v

    def to_dict(self) -> dict:
        return {
            "apiVersion": "v1",
            "kind": "PersistentVolume",
            "metadata": {
                "name": self.name,
                "labels": self.labels,
            },
            "spec": {
                "capacity": {
                    "storage": self.capacity + "Gi",
                },
                "accessModes": ["ReadWriteMany"],
                "hostPath": {
                    "path": self.path,
                },
                "mountOptions": self.options,
            },
        }


class PersistentVolumeClaim(AbstractAPIObject):
    def __init__(self, name, pv_name, capacity):
        self.name = name
        self.pv_name = pv_name
        self.capacity = capacity
        self.labels = {}

    def label(self, k, v):
        self.labels[k] = v

    def to_dict(self) -> dict:
        base = {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {
                "name": self.name,
                "labels": self.labels,
            },
            "spec": {
                "resources": {
                    "requests": {
                        "storage": self.capacity + "Gi",
                    },
                },
                "accessModes": ["ReadWriteMany"],
                "storageClassName": "",
            },
        }
        return base

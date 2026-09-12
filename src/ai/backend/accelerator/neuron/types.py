from ai.backend.agent.resources import AbstractComputeDevice
from ai.backend.common.types import DeviceId, DeviceName

__all__ = ("NeuronCoreDevice", "make_core_device_id")


class NeuronCoreDevice(AbstractComputeDevice):
    """
    One **NeuronCore**, which is the unit of allocation for this plugin.

    A Neuron *device* (``/dev/neuronN``) carries ``nc_count`` NeuronCores.  The
    device stays present as identity metadata (``serial``, ``hw_location``,
    ``neuron_device_index``) but is not the allocation key -- see the package
    README for the rationale.
    """

    model_name: str
    serial: str
    neuron_device_index: int
    core_index: int
    global_core_id: int
    arch_type: str

    def __init__(
        self,
        model_name: str,
        serial: str,
        neuron_device_index: int,
        core_index: int,
        global_core_id: int,
        arch_type: str,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.model_name = model_name
        self.serial = serial
        self.neuron_device_index = neuron_device_index
        self.core_index = core_index
        self.global_core_id = global_core_id
        self.arch_type = arch_type
        # Without this, AbstractComputeDevice.device_name would infer
        # "neuroncore" from the class name instead of the plugin's key.
        self._device_name = DeviceName("neuron")

    @property
    def device_node_path(self) -> str:
        """
        Host path of the character device carrying this core.

        Every core of one Neuron device shares a single device node, so cores of
        the same device map to the same path.
        """
        return f"/dev/neuron{self.neuron_device_index}"

    def __str__(self) -> str:
        return (
            f"NeuronCoreDevice <core {self.global_core_id} "
            f"(neuron{self.neuron_device_index}/nc{self.core_index}), {self.hw_location}, "
            f"Memory {self.memory_size}, NUMA Node #{self.numa_node}>"
        )

    def __repr__(self) -> str:
        return self.__str__()


def make_core_device_id(global_core_id: int) -> DeviceId:
    """
    The device ID of a core *is* its logical NeuronCore index.

    That is deliberate: the same integer is what ``NEURON_RT_VISIBLE_CORES``
    accepts, so the allocation key and the runtime's own addressing agree.
    """
    return DeviceId(str(global_core_id))

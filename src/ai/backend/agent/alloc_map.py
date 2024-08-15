from __future__ import annotations

import enum
import fnmatch
import itertools
import logging
import operator
from abc import ABCMeta, abstractmethod
from collections import defaultdict
from decimal import ROUND_DOWN, Decimal
from typing import (
    TYPE_CHECKING,
    FrozenSet,
    Iterable,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    TypeVar,
)

import attr
import more_itertools

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import DeviceId, DeviceName, SlotName, SlotTypes

from .affinity_map import AffinityHint, AffinityPolicy
from .exception import (
    InsufficientResource,
    InvalidResourceArgument,
    InvalidResourceCombination,
    NotMultipleOfQuantum,
    ResourceError,
)

if TYPE_CHECKING:
    from .resources import AbstractComputeDevice

log = BraceStyleAdapter(logging.getLogger(__spec__.name))
log_alloc_map: bool = False
T = TypeVar("T")


class AllocationStrategy(enum.Enum):
    FILL = 0
    EVENLY = 1


@attr.define()
class DeviceSlotInfo:
    slot_type: SlotTypes
    slot_name: SlotName
    amount: Decimal


def distribute(num_items: int, groups: Sequence[T]) -> Mapping[T, int]:
    base, extra = divmod(num_items, len(groups))
    return dict(
        zip(
            groups,
            ((base + (1 if i < extra else 0)) for i in range(len(groups))),
        )
    )


def round_down(from_dec: Decimal, with_dec: Decimal):
    remainder = from_dec.remainder_near(with_dec)
    if remainder < 0:
        remainder += with_dec
    return from_dec - remainder


class AbstractAllocMap(metaclass=ABCMeta):
    device_slots: Mapping[DeviceId, DeviceSlotInfo]
    device_mask: FrozenSet[DeviceId]
    exclusive_slot_types: Iterable[SlotName]
    allocations: MutableMapping[SlotName, MutableMapping[DeviceId, Decimal]]

    def __init__(
        self,
        *,
        device_slots: Optional[Mapping[DeviceId, DeviceSlotInfo]] = None,
        device_mask: Optional[Iterable[DeviceId]] = None,
        exclusive_slot_types: Optional[Iterable[SlotName]] = None,
    ) -> None:
        self.exclusive_slot_types = exclusive_slot_types or {}
        self.device_slots = device_slots or {}
        self.slot_types = {info.slot_name: info.slot_type for info in self.device_slots.values()}
        self.device_mask = frozenset(device_mask) if device_mask is not None else frozenset()
        self.allocations = defaultdict(lambda: defaultdict(Decimal))
        for dev_id, dev_slot_info in self.device_slots.items():
            self.allocations[dev_slot_info.slot_name][dev_id] = Decimal(0)

    def clear(self) -> None:
        self.allocations.clear()
        for dev_id, dev_slot_info in self.device_slots.items():
            self.allocations[dev_slot_info.slot_name][dev_id] = Decimal(0)

    def check_exclusive(self, a: SlotName, b: SlotName) -> bool:
        if not self.exclusive_slot_types:
            return False
        if a == b:
            return False
        a_in_exclusive_set = a in self.exclusive_slot_types
        b_in_exclusive_set = b in self.exclusive_slot_types
        if a_in_exclusive_set and b_in_exclusive_set:
            # fast-path for exact match
            return True
        for t in self.exclusive_slot_types:
            if "*" in t:
                a_in_exclusive_set = a_in_exclusive_set or fnmatch.fnmatchcase(a, t)
                b_in_exclusive_set = b_in_exclusive_set or fnmatch.fnmatchcase(b, t)
        return a_in_exclusive_set and b_in_exclusive_set

    def format_current_allocations(self) -> str:
        bufs = []
        for slot_name, per_device_alloc in self.allocations.items():
            bufs.append(f"slot[{slot_name}]:")
            for device_id, alloc in per_device_alloc.items():
                bufs.append(f"  {device_id}: {alloc}")
        return "\n".join(bufs)

    def get_current_allocations(
        self, affinity_hint: Optional[AffinityHint], slot_name: SlotName
    ) -> Sequence[tuple[DeviceId, Decimal]]:
        device_name = DeviceName(slot_name.partition(".")[0])
        if affinity_hint is None or not affinity_hint.devices:  # for legacy
            return sorted(
                self.allocations[slot_name].items(),  # k: slot_name, v: per-device alloc
                key=lambda pair: self.device_slots[pair[0]].amount - pair[1],
                reverse=True,
            )
        primary_sets, secondary_set = affinity_hint.affinity_map.get_distance_ordered_neighbors(
            affinity_hint.devices, device_name
        )

        def convert_to_sorted_dev_alloc(device_set: Iterable[AbstractComputeDevice]):
            device_ids = {d.device_id for d in device_set}
            return sorted(
                (
                    (device_id, alloc)
                    for device_id, alloc in self.allocations[slot_name].items()
                    if device_id in device_ids
                ),
                key=lambda pair: self.device_slots[pair[0]].amount - pair[1],
                reverse=True,
            )

        primary_sorted_dev_allocs = [
            convert_to_sorted_dev_alloc(primary_set) for primary_set in primary_sets
        ]
        secondary_sorted_dev_alloc = convert_to_sorted_dev_alloc(secondary_set)

        if not affinity_hint.devices:  # first-allocated device
            match affinity_hint.policy:
                case AffinityPolicy.PREFER_SINGLE_NODE:
                    return [
                        (device_id, alloc)
                        for device_id, alloc in itertools.chain(*primary_sorted_dev_allocs)
                    ]
                case AffinityPolicy.INTERLEAVED:
                    return [
                        (device_id, alloc)
                        for device_id, alloc in more_itertools.interleave_longest(
                            *primary_sorted_dev_allocs
                        )
                    ]
        else:
            return [
                *(
                    (device_id, alloc)
                    for device_id, alloc in more_itertools.interleave_longest(
                        *primary_sorted_dev_allocs
                    )
                ),
                *((device_id, alloc) for device_id, alloc in secondary_sorted_dev_alloc),
            ]

    @abstractmethod
    def allocate(
        self,
        slots: Mapping[SlotName, Decimal],
        *,
        affinity_hint: Optional[AffinityHint] = None,
        context_tag: Optional[str] = None,
    ) -> Mapping[SlotName, Mapping[DeviceId, Decimal]]:
        """
        Allocate the given amount of resources.

        For a slot type, there may be multiple different devices which can allocate resources
        in the given slot type.  An implementation of alloc map finds suitable match from the
        remaining capacities of those devices.

        Returns a mapping from each requested slot to the allocations per device.
        """
        pass

    @abstractmethod
    def apply_allocation(
        self,
        existing_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> None:
        """
        Apply the given allocation restored from disk or other persistent storages.
        """
        pass

    @abstractmethod
    def free(
        self,
        existing_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> None:
        """
        Free the allocated resources using the token returned when the allocation
        occurred.
        """
        pass


class DiscretePropertyAllocMap(AbstractAllocMap):
    """
    An allocation map using discrete property.
    The user must pass a "property function" which returns a desired resource
    property from the device object.

    e.g., 1.0 means 1 device, 2.0 means 2 devices, etc.
    (no fractions allowed)
    """

    def __init__(
        self,
        *args,
        allocation_strategy: AllocationStrategy = AllocationStrategy.EVENLY,
        **kwargs,
    ) -> None:
        self.allocation_strategy = allocation_strategy
        self._allocate_impl = {
            AllocationStrategy.FILL: self._allocate_by_filling,
            AllocationStrategy.EVENLY: self._allocate_evenly,
        }
        super().__init__(*args, **kwargs)

    def allocate(
        self,
        slots: Mapping[SlotName, Decimal],
        *,
        affinity_hint: Optional[AffinityHint] = None,
        context_tag: Optional[str] = None,
    ) -> Mapping[SlotName, Mapping[DeviceId, Decimal]]:
        # prune zero alloc slots
        requested_slots = {k: v for k, v in slots.items() if v > 0}

        # check exclusive
        for slot_name_a in requested_slots.keys():
            for slot_name_b in requested_slots.keys():
                if self.check_exclusive(slot_name_a, slot_name_b):
                    raise InvalidResourceCombination(
                        f"Slots {slot_name_a} and {slot_name_b} cannot be allocated at the same"
                        " time."
                    )

        # check unique
        for slot_name, alloc in requested_slots.items():
            slot_type = self.slot_types.get(slot_name, SlotTypes.COUNT)
            if slot_type in (SlotTypes.COUNT, SlotTypes.BYTES):
                pass
            elif slot_type == SlotTypes.UNIQUE:
                if alloc != Decimal(1):
                    raise InvalidResourceArgument(
                        f"You may allocate only 1 for the unique-type slot {slot_name}",
                    )

        return self._allocate_impl[self.allocation_strategy](
            requested_slots,
            affinity_hint=affinity_hint,
            context_tag=context_tag,
        )

    def _allocate_by_filling(
        self,
        requested_slots: Mapping[SlotName, Decimal],
        *,
        affinity_hint: Optional[AffinityHint] = None,
        context_tag: Optional[str] = None,
    ) -> Mapping[SlotName, Mapping[DeviceId, Decimal]]:
        allocation: dict[SlotName, dict[DeviceId, Decimal]] = {}
        for slot_name, requested_alloc in requested_slots.items():
            slot_allocation: dict[DeviceId, Decimal] = {}
            sorted_dev_allocs = self.get_current_allocations(affinity_hint, slot_name)
            if log_alloc_map:
                log.debug(
                    "DiscretePropertyAllocMap(FILL): allocating {} {}", slot_name, requested_alloc
                )
                log.debug("DiscretePropertyAllocMap(FILL): current-alloc: {!r}", sorted_dev_allocs)

            total_allocatable = int(0)
            remaining_alloc = Decimal(requested_alloc).normalize()

            # fill up starting from the most free devices
            for dev_id, current_alloc in sorted_dev_allocs:
                current_alloc = self.allocations[slot_name][dev_id]
                assert slot_name == self.device_slots[dev_id].slot_name
                total_allocatable += int(self.device_slots[dev_id].amount - current_alloc)
            if total_allocatable < requested_alloc:
                raise InsufficientResource(
                    "DiscretePropertyAllocMap: insufficient allocatable amount!",
                    context_tag=context_tag,
                    slot_name=slot_name,
                    requested_alloc=requested_alloc,
                    total_allocatable=total_allocatable,
                    allocation=allocation,
                )
            for dev_id, current_alloc in sorted_dev_allocs:
                current_alloc = self.allocations[slot_name][dev_id]
                allocatable = self.device_slots[dev_id].amount - current_alloc
                if allocatable > 0:
                    allocated = Decimal(min(remaining_alloc, allocatable))
                    slot_allocation[dev_id] = allocated
                    self.allocations[slot_name][dev_id] += allocated
                    remaining_alloc -= allocated
                if remaining_alloc == 0:
                    break
            allocation[slot_name] = slot_allocation

        return allocation

    def _allocate_evenly(
        self,
        requested_slots: Mapping[SlotName, Decimal],
        *,
        affinity_hint: Optional[AffinityHint] = None,
        context_tag: Optional[str] = None,
    ) -> Mapping[SlotName, Mapping[DeviceId, Decimal]]:
        allocation: dict[SlotName, dict[DeviceId, Decimal]] = {}

        for slot_name, requested_alloc in requested_slots.items():
            new_alloc: MutableMapping[DeviceId, Decimal] = defaultdict(Decimal)
            remaining_alloc = int(Decimal(requested_alloc))
            if log_alloc_map:
                log.debug(
                    "DiscretePropertyAllocMap(EVENLY): allocating {} {}", slot_name, requested_alloc
                )

            repeats = 0
            while remaining_alloc > 0:
                # prevent infinite loop
                if repeats >= 100:
                    raise ResourceError("too many repeats until allocation")

                # calculate remaining slots per device
                total_allocatable = int(
                    sum(
                        self.device_slots[dev_id].amount - current_alloc - new_alloc[dev_id]
                        for dev_id, current_alloc in self.allocations[slot_name].items()
                    )
                )
                # if the sum of remaining slot is less than the remaining alloc, fail.
                if total_allocatable < remaining_alloc:
                    raise InsufficientResource(
                        "DiscretePropertyAllocMap: insufficient allocatable amount!",
                        context_tag=context_tag,
                        slot_name=slot_name,
                        requested_alloc=requested_alloc,
                        total_allocatable=total_allocatable,
                        allocation=allocation,
                    )

                sorted_dev_allocs = self.get_current_allocations(affinity_hint, slot_name)
                if log_alloc_map and repeats == 0:
                    log.debug(
                        "DiscretePropertyAllocMap(EVENLY): current-alloc: {!r}", sorted_dev_allocs
                    )

                # calculate the amount to spread out
                nonzero_devs = [
                    dev_id
                    for dev_id, current_alloc in sorted_dev_allocs
                    if self.device_slots[dev_id].amount - current_alloc - new_alloc[dev_id] > 0
                ]
                if len(nonzero_devs) == 0:
                    raise InsufficientResource(
                        "DiscretePropertyAllocMap: insufficient allocatable candidate devices!",
                        context_tag=context_tag,
                        slot_name=slot_name,
                        requested_alloc=requested_alloc,
                        total_allocatable=total_allocatable,
                        allocation=allocation,
                    )
                initial_diffs = distribute(remaining_alloc, nonzero_devs)
                diffs = {
                    dev_id: min(
                        int(self.device_slots[dev_id].amount - current_alloc - new_alloc[dev_id]),
                        initial_diffs.get(dev_id, 0),
                    )
                    for dev_id, current_alloc in self.allocations[slot_name].items()
                }

                # distribute the remainig alloc to the remaining slots.
                for dev_id, current_alloc in sorted_dev_allocs:
                    diff = diffs[dev_id]
                    new_alloc[dev_id] += diff
                    remaining_alloc -= diff
                    if remaining_alloc == 0:
                        break

                repeats += 1

            for dev_id, allocated in new_alloc.items():
                self.allocations[slot_name][dev_id] += allocated
            allocation[slot_name] = {k: v for k, v in new_alloc.items() if v > 0}
            if log_alloc_map:
                log.debug("DiscretePropertyAllocMap(EVENLY): new-alloc: {!r}", new_alloc)

        return allocation

    def apply_allocation(
        self,
        existing_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> None:
        for slot_name, per_device_alloc in existing_alloc.items():
            for device_id, alloc in per_device_alloc.items():
                self.allocations[slot_name][device_id] += alloc

    def free(
        self,
        existing_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> None:
        for slot_name, per_device_alloc in existing_alloc.items():
            for device_id, alloc in per_device_alloc.items():
                self.allocations[slot_name][device_id] -= alloc


class FractionAllocMap(AbstractAllocMap):
    def __init__(
        self,
        *args,
        allocation_strategy: AllocationStrategy = AllocationStrategy.EVENLY,
        quantum_size: Decimal = Decimal("0.01"),
        enforce_physical_continuity: bool = True,
        **kwargs,
    ) -> None:
        self.allocation_strategy = allocation_strategy
        self.quantum_size = quantum_size
        self.enforce_physical_continuity = enforce_physical_continuity
        self._allocate_impl = {
            AllocationStrategy.FILL: self._allocate_by_filling,
            AllocationStrategy.EVENLY: self._allocate_evenly,
        }
        super().__init__(*args, **kwargs)
        self.digits = Decimal(10) ** -2  # decimal points that is supported by agent
        self.powers = Decimal(100)  # reciprocal of self.digits

    def allocate(
        self,
        slots: Mapping[SlotName, Decimal],
        *,
        affinity_hint: Optional[AffinityHint] = None,
        context_tag: Optional[str] = None,
        min_memory: Decimal = Decimal("0.01"),
    ) -> Mapping[SlotName, Mapping[DeviceId, Decimal]]:
        # prune zero alloc slots
        requested_slots = {k: v for k, v in slots.items() if v > 0}

        # check exclusive
        for slot_name_a in requested_slots.keys():
            for slot_name_b in requested_slots.keys():
                if self.check_exclusive(slot_name_a, slot_name_b):
                    raise InvalidResourceCombination(
                        f"Slots {slot_name_a} and {slot_name_b} cannot be allocated at the same"
                        " time.",
                    )

        calculated_alloc_map = self._allocate_impl[self.allocation_strategy](
            requested_slots,
            affinity_hint=affinity_hint,
            context_tag=context_tag,
            min_memory=min_memory,
        )
        actual_alloc_map: dict[SlotName, dict[DeviceId, Decimal]] = {}
        for slot_name, alloc in calculated_alloc_map.items():
            actual_alloc: dict[DeviceId, Decimal] = {}
            for dev_id, val in alloc.items():
                self.allocations[slot_name][dev_id] = round_down(
                    self.allocations[slot_name][dev_id], self.quantum_size
                )
                actual_alloc[dev_id] = round_down(val, self.quantum_size)
            if sum(actual_alloc.values()) == 0 and requested_slots[slot_name] > 0:
                raise NotMultipleOfQuantum(
                    f"Requested resource amount for {slot_name} is"
                    f" {requested_slots[slot_name]} but actual calculated amount is zero. This"
                    " can happen if user requests resource amount smaller than target device's"
                    " quantum size.",
                )
            actual_alloc_map[slot_name] = actual_alloc

        return actual_alloc_map

    def _allocate_by_filling(
        self,
        requested_slots: Mapping[SlotName, Decimal],
        *,
        affinity_hint: Optional[AffinityHint] = None,
        context_tag: Optional[str] = None,
        min_memory: Decimal = Decimal(0.01),
    ) -> Mapping[SlotName, Mapping[DeviceId, Decimal]]:
        allocation: dict[SlotName, dict[DeviceId, Decimal]] = {}
        for slot_name, alloc in requested_slots.items():
            slot_allocation: dict[DeviceId, Decimal] = {}

            # fill up starting from the most free devices
            sorted_dev_allocs = self.get_current_allocations(affinity_hint, slot_name)

            if log_alloc_map:
                log.debug("FractionAllocMap(FILL): allocating {} {}", slot_name, alloc)
                log.debug("FractionAllocMap(FILL): current-alloc: {!r}", sorted_dev_allocs)

            slot_type = self.slot_types.get(slot_name, SlotTypes.COUNT)
            if slot_type in (SlotTypes.COUNT, SlotTypes.BYTES):
                pass
            elif slot_type == SlotTypes.UNIQUE:
                if alloc != Decimal(1):
                    raise InvalidResourceArgument(
                        f"You may allocate only 1 for the unique-type slot {slot_name}",
                    )
            total_allocatable = Decimal(0)
            remaining_alloc = Decimal(alloc).normalize()

            for dev_id, current_alloc in sorted_dev_allocs:
                current_alloc = self.allocations[slot_name][dev_id]
                assert slot_name == self.device_slots[dev_id].slot_name
                total_allocatable += self.device_slots[dev_id].amount - current_alloc
            if total_allocatable < alloc:
                raise InsufficientResource(
                    "FractionAllocMap: insufficient allocatable amount!",
                    context_tag=context_tag,
                    slot_name=slot_name,
                    requested_alloc=alloc,
                    total_allocatable=total_allocatable,
                    allocation=allocation,
                )
            for dev_id, current_alloc in sorted_dev_allocs:
                current_alloc = self.allocations[slot_name][dev_id]
                allocatable = self.device_slots[dev_id].amount - current_alloc
                if allocatable > 0:
                    allocated = min(remaining_alloc, allocatable)
                    slot_allocation[dev_id] = allocated
                    self.allocations[slot_name][dev_id] += allocated
                    remaining_alloc -= allocated
                if remaining_alloc <= 0:
                    break

            allocation[slot_name] = slot_allocation
        return allocation

    def _allocate_evenly(
        self,
        requested_slots: Mapping[SlotName, Decimal],
        *,
        affinity_hint: Optional[AffinityHint] = None,
        context_tag: Optional[str] = None,
        min_memory: Decimal = Decimal(0.01),
    ) -> Mapping[SlotName, Mapping[DeviceId, Decimal]]:
        # higher value means more even with 0 being the highest value
        def measure_evenness(
            alloc_map: Mapping[DeviceId, Decimal],
        ) -> Decimal:
            alloc_arr = sorted([alloc_map[dev_id] for dev_id in alloc_map])
            evenness_score = Decimal(0).quantize(self.digits)
            for idx in range(len(alloc_arr) - 1):
                evenness_score += abs(alloc_arr[idx + 1] - alloc_arr[idx])
            return -evenness_score

        # higher value means more fragmented
        # i.e. the number of unusable resources is higher
        def measure_fragmentation(
            allocation: Mapping[DeviceId, Decimal],
            min_memory: Decimal,
        ) -> int:
            fragmentation_arr = [
                self.device_slots[dev_id].amount - allocation[dev_id] for dev_id in allocation
            ]
            return sum(
                self.digits < v.quantize(self.digits) < min_memory.quantize(self.digits)
                for v in fragmentation_arr
            )

        # evenly distributes remaining_alloc across dev_allocs
        def distribute_evenly(
            dev_allocs: list[tuple[DeviceId, Decimal]],
            remaining_alloc: Decimal,
            allocation: dict[DeviceId, Decimal],
        ) -> None:
            n_devices = len(dev_allocs)
            for dev_id, _ in dev_allocs:
                dev_allocation = remaining_alloc / n_devices
                dev_allocation = dev_allocation.quantize(self.digits, rounding=ROUND_DOWN)
                allocation[dev_id] = dev_allocation

            # need to take care of decimals
            remainder = round(
                remaining_alloc * self.powers - dev_allocation * n_devices * self.powers
            )
            for idx in range(remainder):
                dev_id, _ = dev_allocs[idx]
                allocation[dev_id] += self.digits

        # allocates remaining_alloc across multiple devices i.e. dev_allocs
        # all devices in dev_allocs are being used
        def allocate_across_devices(
            dev_allocs: list[tuple[DeviceId, Decimal]],
            remaining_alloc: Decimal,
            slot_name: str,
        ) -> dict[DeviceId, Decimal]:
            slot_allocation: dict[DeviceId, Decimal] = {}
            n_devices = len(dev_allocs)
            idx = n_devices - 1  # check from the device with smallest allocatable resource
            while n_devices > 0:
                dev_id, current_alloc = dev_allocs[idx]
                allocatable = self.device_slots[dev_id].amount - current_alloc
                # if the remaining_alloc can be allocated to evenly among remaining devices
                if allocatable >= remaining_alloc / n_devices:
                    break
                slot_allocation[dev_id] = allocatable.quantize(self.digits)
                remaining_alloc -= allocatable
                idx -= 1
                n_devices -= 1

            if n_devices > 0:
                distribute_evenly(dev_allocs[:n_devices], remaining_alloc, slot_allocation)

            return slot_allocation

        min_memory = min_memory.quantize(self.digits)
        allocation: dict[SlotName, dict[DeviceId, Decimal]] = {}
        for slot_name, alloc in requested_slots.items():
            slot_allocation: dict[DeviceId, Decimal] = {}
            remaining_alloc = Decimal(alloc).normalize()
            sorted_dev_allocs = self.get_current_allocations(affinity_hint, slot_name)

            # do not consider devices whose remaining resource under min_memory
            sorted_dev_allocs = list(
                filter(
                    lambda pair: self.device_slots[pair[0]].amount - pair[1] >= min_memory,
                    sorted_dev_allocs,
                )
            )

            if log_alloc_map:
                log.debug("FractionAllocMap(EVENLY): allocating {} {}", slot_name, alloc)
                log.debug("FractionAllocMap(EVENLY): current-alloc: {!r}", sorted_dev_allocs)

            # check if there is enough resource for allocation
            total_allocatable = Decimal(0)
            for dev_id, current_alloc in sorted_dev_allocs:
                current_alloc = self.allocations[slot_name][dev_id]
                total_allocatable += self.device_slots[dev_id].amount - current_alloc
            if total_allocatable.quantize(self.digits) < remaining_alloc.quantize(self.digits):
                raise InsufficientResource(
                    "FractionAllocMap: insufficient allocatable amount!",
                    context_tag=context_tag,
                    slot_name=slot_name,
                    requested_alloc=alloc,
                    total_allocatable=total_allocatable,
                    allocation=allocation,
                )

            # allocate resources
            if (
                remaining_alloc
                <= self.device_slots[sorted_dev_allocs[0][0]].amount - sorted_dev_allocs[0][1]
            ):
                # if remaining_alloc fits in one device
                for dev_id, current_alloc in sorted_dev_allocs[::-1]:
                    allocatable = self.device_slots[dev_id].amount - current_alloc
                    if remaining_alloc <= allocatable:
                        slot_allocation[dev_id] = remaining_alloc.quantize(self.digits)
                        break
            else:
                # need to distribute across devices
                # calculate the minimum number of required devices
                n_devices, allocated = 0, Decimal(0)
                for dev_id, current_alloc in sorted_dev_allocs:
                    n_devices += 1
                    allocated += self.device_slots[dev_id].amount - current_alloc
                    if allocated.quantize(self.digits) >= remaining_alloc.quantize(self.digits):
                        break
                # need to check from using minimum number of devices to using all devices
                # evenness must be non-decreasing with the increase of window size
                best_alloc_candidate_arr = []
                for n_dev in range(n_devices, len(sorted_dev_allocs) + 1):
                    allocatable = sum(
                        map(
                            lambda x: self.device_slots[x[0]].amount - x[1],
                            sorted_dev_allocs[:n_dev],
                        ),
                        start=Decimal(0),
                    )
                    # choose the best allocation from all possible allocation candidates
                    alloc_candidate = allocate_across_devices(
                        sorted_dev_allocs[:n_dev],
                        remaining_alloc,
                        slot_name,
                    )
                    max_evenness = measure_evenness(alloc_candidate)
                    # three criteria to decide allocation are
                    # eveness, number of resources used, and amount of fragmentatino
                    alloc_candidate_arr = [
                        (
                            alloc_candidate,
                            max_evenness,
                            -len(alloc_candidate),
                            -measure_fragmentation(alloc_candidate, min_memory),
                        ),
                    ]
                    for idx in range(1, len(sorted_dev_allocs) - n_dev + 1):
                        # update amount of allocatable space
                        allocatable -= (
                            self.device_slots[sorted_dev_allocs[idx - 1][0]].amount
                            - sorted_dev_allocs[idx - 1][1]
                        )
                        allocatable += (
                            self.device_slots[sorted_dev_allocs[idx + n_dev - 1][0]].amount
                            - sorted_dev_allocs[idx + n_dev - 1][1]
                        )
                        # break if not enough resource
                        if allocatable.quantize(self.digits) < remaining_alloc.quantize(
                            self.digits
                        ):
                            break
                        alloc_candidate = allocate_across_devices(
                            sorted_dev_allocs[idx : idx + n_dev],
                            remaining_alloc,
                            slot_name,
                        )
                        # evenness gets worse (or same at best) as the allocatable gets smaller
                        evenness_score = measure_evenness(alloc_candidate)
                        if evenness_score < max_evenness:
                            break
                        alloc_candidate_arr.append(
                            (
                                alloc_candidate,
                                evenness_score,
                                -len(alloc_candidate),
                                -measure_fragmentation(alloc_candidate, min_memory),
                            ),
                        )
                    # since evenness is the same, sort by fragmentation (low is good)
                    best_alloc_candidate_arr.append(
                        sorted(alloc_candidate_arr, key=lambda x: x[2])[-1],
                    )
                    # there is no need to look at more devices if the desired evenness is achieved
                    if max_evenness.quantize(self.digits) == self.digits:
                        best_alloc_candidate_arr = best_alloc_candidate_arr[-1:]
                        break
                # choose the best allocation with the three criteria
                slot_allocation = sorted(
                    best_alloc_candidate_arr,
                    key=operator.itemgetter(1, 2, 3),
                )[-1][0]
            allocation[slot_name] = slot_allocation
            for dev_id, value in slot_allocation.items():
                self.allocations[slot_name][dev_id] += value
        return allocation

    def apply_allocation(
        self,
        existing_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> None:
        for slot_name, per_device_alloc in existing_alloc.items():
            for device_id, alloc in per_device_alloc.items():
                self.allocations[slot_name][device_id] += alloc

    def free(
        self,
        existing_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> None:
        for slot_name, per_device_alloc in existing_alloc.items():
            for device_id, alloc in per_device_alloc.items():
                self.allocations[slot_name][device_id] -= alloc

#!/usr/bin/env python3
"""
Docker shm/memory 테스트용 메모리 할당 스크립트

사용법:
    python allocate_memory.py --shm-alloc-mb 500 --ram-alloc-mb 700
    python allocate_memory.py --shm-alloc-mb 500 --ram-alloc-mb 700 --ram-first
    python allocate_memory.py --shm-alloc-mb 500 --ram-alloc-mb 700 --release-shm-before-ram

출력:
    SUCCESS: 모든 할당 성공
    SHM_ALLOC_FAILED: shared memory 할당 실패
    RAM_ALLOC_FAILED: RAM 할당 실패
"""

import argparse
import sys
from multiprocessing import shared_memory


def allocate_shm(size_mb: int) -> shared_memory.SharedMemory | None:
    """Allocate shared memory using multiprocessing.shared_memory

    Note: POSIX shared memory uses lazy allocation. The actual memory is only
    allocated when pages are touched. We must write to the memory to trigger
    the actual allocation and enforce tmpfs limits.
    """
    if size_mb <= 0:
        return None

    try:
        shm = shared_memory.SharedMemory(create=True, size=size_mb * 1024 * 1024)
        # Touch all pages to trigger actual allocation
        # This is necessary because POSIX shm uses lazy allocation
        buf = shm.buf
        for i in range(0, len(buf), 4096):  # Touch each page (4KB)
            buf[i] = 0xFF
        return shm
    except OSError:
        return None


def allocate_ram(size_mb: int) -> bytearray | None:
    """Allocate specified MB in RAM"""
    if size_mb <= 0:
        return None

    try:
        return bytearray(size_mb * 1024 * 1024)
    except MemoryError:
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Memory allocation test")
    parser.add_argument("--shm-alloc-mb", type=int, default=0, help="MB to allocate as shared memory")
    parser.add_argument("--ram-alloc-mb", type=int, default=0, help="MB to allocate in RAM")
    parser.add_argument("--ram-first", action="store_true", help="Allocate RAM before shm (default: shm first)")
    parser.add_argument("--release-shm-before-ram", action="store_true", help="Allocate shm, release it, then allocate RAM")
    args = parser.parse_args()

    shm = None
    ram = None
    try:
        if args.release_shm_before_ram:
            # shm 할당 → shm 해제 → RAM 할당 (메모리 반환 테스트)
            if args.shm_alloc_mb > 0:
                shm = allocate_shm(args.shm_alloc_mb)
                if shm is None:
                    print("SHM_ALLOC_FAILED")
                    sys.exit(1)
                # 즉시 해제
                shm.close()
                shm.unlink()
                shm = None  # cleanup에서 다시 해제 시도 방지

            if args.ram_alloc_mb > 0:
                ram = allocate_ram(args.ram_alloc_mb)
                if ram is None:
                    print("RAM_ALLOC_FAILED")
                    sys.exit(1)

        elif args.ram_first:
            # RAM first, then shm
            if args.ram_alloc_mb > 0:
                ram = allocate_ram(args.ram_alloc_mb)
                if ram is None:
                    print("RAM_ALLOC_FAILED")
                    sys.exit(1)

            if args.shm_alloc_mb > 0:
                shm = allocate_shm(args.shm_alloc_mb)
                if shm is None:
                    print("SHM_ALLOC_FAILED")
                    sys.exit(1)
        else:
            # shm first, then RAM (default)
            if args.shm_alloc_mb > 0:
                shm = allocate_shm(args.shm_alloc_mb)
                if shm is None:
                    print("SHM_ALLOC_FAILED")
                    sys.exit(1)

            if args.ram_alloc_mb > 0:
                ram = allocate_ram(args.ram_alloc_mb)
                if ram is None:
                    print("RAM_ALLOC_FAILED")
                    sys.exit(1)

        print("SUCCESS")
        sys.exit(0)

    finally:
        # Cleanup shared memory
        if shm is not None:
            shm.close()
            shm.unlink()


if __name__ == "__main__":
    main()

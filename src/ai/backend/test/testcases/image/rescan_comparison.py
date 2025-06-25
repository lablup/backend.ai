import functools
from typing import override

from ai.backend.client.output.fields import image_fields
from ai.backend.common.utils import join_non_empty
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.container_registry import ContainerRegistriesContext
from ai.backend.test.contexts.image import RescannedImagesContext
from ai.backend.test.templates.image.harbor_scanner import (
    HarborRegistryRawScanner,
    HarborRegistryRawScannerArgs,
)
from ai.backend.test.templates.template import TestCode


# TODO: Modify the structure to use an exporter instead of using print statements directly.
class RescanResultComparison(TestCode):
    """
    Compares the rescan results of Backend.AI's image scanner with those of HarborRegistryRawScanner and outputs the differences.
    """

    @override
    async def test(self) -> None:
        client_session = ClientSessionContext.current()
        container_registry_deps = ContainerRegistriesContext.current()
        rescan_results = RescannedImagesContext.current()

        # Get rescanned image canonical names
        rescanned_canonicals = []
        for _key, uuid_list in rescan_results.rescanned_images.items():
            for image_id in uuid_list:
                # TODO: Query all images in a single request.
                result = await client_session.Image.get_by_id(
                    str(image_id),
                    [
                        image_fields["name"],
                        image_fields["registry"],
                        image_fields["tag"],
                    ],
                )
                join = functools.partial(join_non_empty, sep="/")
                canonical = f"{join(result['registry'], result['name'])}:{result['tag']}"
                rescanned_canonicals.append(canonical)

        # Scan Harbor registries directly and compare with rescan results
        harbor_scanner_canonicals = []
        for registry_dep in container_registry_deps:
            try:
                async with HarborRegistryRawScanner(
                    HarborRegistryRawScannerArgs(
                        registry_dep.url, registry_dep.username, registry_dep.password
                    )
                ) as scanner:
                    project_canonicals = await scanner.scan_specific_registry(registry_dep.project)
                    harbor_scanner_canonicals.extend(project_canonicals)
            except Exception as e:
                print(f"Harbor scanner failed for {registry_dep.name}/{registry_dep.project}: {e}")

        # Compare results
        rescanned_set = set(rescanned_canonicals)
        harbor_set = set(harbor_scanner_canonicals)

        print("\n" + "=" * 80)
        print("🔍 RESCAN vs HARBOR SCANNER COMPARISON")
        print("=" * 80)

        print(f"📋 RESCAN RESULTS     : {len(rescanned_set):>4} images")
        print(f"🐳 HARBOR SCANNER     : {len(harbor_set):>4} images")

        only_in_rescan = rescanned_set - harbor_set
        only_in_harbor = harbor_set - rescanned_set
        common_images = rescanned_set & harbor_set

        print(f"🤝 COMMON IMAGES      : {len(common_images):>4} images")
        print(f"🔴 ONLY IN RESCAN     : {len(only_in_rescan):>4} images")
        print(f"🔵 ONLY IN HARBOR     : {len(only_in_harbor):>4} images")

        print("-" * 80)
        if rescanned_set == harbor_set:
            print("✅ PERFECT MATCH!")
            print("   All images are consistent between rescan and Harbor scanner.")
            print("=" * 80)
        else:
            print("⚠️  MISMATCH DETECTED")
            mismatch_count = len(only_in_rescan) + len(only_in_harbor)
            total_unique = len(rescanned_set | harbor_set)
            match_rate = (len(common_images) / total_unique) * 100 if total_unique > 0 else 0
            print(f"   Match rate: {match_rate:.1f}% ({len(common_images)}/{total_unique})")
            print(f"   Differences: {mismatch_count} images")

            if only_in_rescan:
                print(f"\n🔴 MISSING FROM HARBOR SCANNER ({len(only_in_rescan)} images):")
                print("   These images were found in rescan but not in Harbor direct scan:")
                for i, img in enumerate(sorted(only_in_rescan), 1):
                    print(f"   {i:>2}. {img}")

            if only_in_harbor:
                print(f"\n🔵 MISSING FROM RESCAN RESULTS ({len(only_in_harbor)} images):")
                print("   These images were found in Harbor but not in rescan results:")
                for i, img in enumerate(sorted(only_in_harbor), 1):
                    print(f"   {i:>2}. {img}")

            print("=" * 80)
            raise AssertionError(
                "Mismatch detected between image rescan results and Harbor scanner results."
            )

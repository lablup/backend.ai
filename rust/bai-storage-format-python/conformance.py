import importlib.machinery
import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = ROOT / "bai-storage-format" / "corpus" / "corpus.json"


def load():
    for profile in ("release", "debug"):
        for suffix in ("dylib", "so"):
            built = ROOT / "target" / profile / f"libbai_storage_format.{suffix}"
            if built.exists():
                loader = importlib.machinery.ExtensionFileLoader(
                    "bai_storage_format", str(built)
                )
                spec = importlib.util.spec_from_loader("bai_storage_format", loader)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module
    raise SystemExit("build the extension first: cargo build -p bai-storage-format-python")


def mutate(module, base, kind, at, extra):
    out = bytearray(base)
    if kind == "flip":
        out[at] ^= extra
    elif kind == "truncate":
        del out[at:]
    elif kind == "append":
        out.extend(b"\0" * extra)
    elif kind == "swap-chunks":
        stride = module.CHUNK_STORED
        first = module.HEADER_LEN + at * stride
        second = module.HEADER_LEN + extra * stride
        out[first : first + stride], out[second : second + stride] = (
            out[second : second + stride],
            out[first : first + stride],
        )
    return bytes(out)


def rejects(failures, case, call):
    try:
        call()
    except ValueError as error:
        code = str(error).split(":")[0]
        if code != case["error"]:
            failures.append(f"{case['case']}: rejected as {code}, expected {case['error']}")
    else:
        failures.append(f"{case['case']}: accepted a mutated input")


def main():
    module = load()
    corpus = json.loads(CORPUS.read_text())
    failures = []
    total = 0
    for case in corpus["derive"]:
        total += 1
        key = module.FolderKey(bytes.fromhex(case["folder_key"]))
        header = key.file_header(bytes.fromhex(case["file_id"]))
        if header.hex() != case["file_header"]:
            failures.append(f"{case['case']}: file header")
    for case in corpus["content"]:
        total += 1
        key = module.FolderKey(bytes.fromhex(case["folder_key"]))
        plaintext = bytes.fromhex(case["plaintext"])
        ciphertext = bytes.fromhex(case["ciphertext"])
        nonces = [bytes.fromhex(nonce) for nonce in case["nonces"]]
        sealed = key.encrypt_with(bytes.fromhex(case["file_id"]), plaintext, nonces)
        if sealed != ciphertext:
            failures.append(f"{case['case']}: sealed bytes")
        if key.decrypt(ciphertext) != plaintext:
            failures.append(f"{case['case']}: opened bytes")
        if module.stored_len(len(plaintext)) != len(ciphertext):
            failures.append(f"{case['case']}: stored length")
        if module.plaintext_len(len(ciphertext)) != len(plaintext):
            failures.append(f"{case['case']}: plaintext length")
    for case in corpus["names"]:
        total += 1
        key = module.FolderKey(bytes.fromhex(case["folder_key"]))
        dir_iv = bytes.fromhex(case["dir_iv"])
        encrypted = key.encrypt_name(dir_iv, case["name"])
        if encrypted.on_disk != case["on_disk"] or encrypted.encoded != case["encoded"]:
            failures.append(f"{case['case']}: encrypted name")
        if encrypted.sidecar_name != case["sidecar_name"]:
            failures.append(f"{case['case']}: sidecar name")
        if key.decrypt_name(dir_iv, case["encoded"]) != case["name"]:
            failures.append(f"{case['case']}: decrypted name")
    for case in corpus["reject"]:
        total += 1
        base = next(entry for entry in corpus["content"] if entry["case"] == case["from"])
        key = module.FolderKey(bytes.fromhex(base["folder_key"]))
        broken = mutate(
            module,
            bytes.fromhex(base["ciphertext"]),
            case["mutation"]["kind"],
            case["mutation"]["at"],
            case["mutation"]["extra"],
        )
        rejects(failures, case, lambda: key.decrypt(broken))
    for case in corpus["reject_names"]:
        total += 1
        key = module.FolderKey(bytes.fromhex(case["folder_key"]))
        dir_iv = bytes.fromhex(case["dir_iv"])
        rejects(failures, case, lambda: key.decrypt_name(dir_iv, case["encoded"]))
    for failure in failures:
        print(failure, file=sys.stderr)
    print(f"{total} cases, {len(failures)} failures")
    sys.exit(1 if failures else 0)


main()

use std::path::PathBuf;

use bai_storage_format as fmt;
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};

const CONTENT_SIZES: [usize; 6] = [0, 1, 65535, 65536, 65537, 131079];
const NAMES: [&str; 6] = [
    "hello.txt",
    "데이터셋.parquet",
    "checkpoints",
    "a name with spaces and 😀",
    "s175",
    "s176",
];
const MUTATIONS: [(&str, &str, i64, i64); 7] = [
    ("flip-header-version", "flip", 4, 1),
    ("flip-file-id", "flip", 10, 1),
    ("flip-first-chunk", "flip", 40, 1),
    ("flip-last-tag", "flip", -1, 1),
    ("truncate-to-first-chunk", "truncate", 22 + 65576, 0),
    ("truncate-to-header", "truncate", 22, 0),
    ("append-one-byte", "append", 0, 1),
];

fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{b:02x}")).collect()
}

fn unhex(text: &str) -> Vec<u8> {
    (0..text.len() / 2)
        .map(|i| u8::from_str_radix(&text[i * 2..i * 2 + 2], 16).unwrap())
        .collect()
}

fn stream(label: &str, len: usize) -> Vec<u8> {
    let mut out = Vec::with_capacity(len + 32);
    let mut counter = 0u64;
    while out.len() < len {
        let mut hash = Sha256::new();
        hash.update(label.as_bytes());
        hash.update(counter.to_le_bytes());
        out.extend_from_slice(&hash.finalize());
        counter += 1;
    }
    out.truncate(len);
    out
}

fn folder_key(label: &str) -> [u8; 32] {
    stream(label, 32).try_into().unwrap()
}

fn plaintext_name(name: &str) -> String {
    match name {
        "s175" => "n".repeat(175),
        "s176" => "n".repeat(176),
        other => other.to_string(),
    }
}

fn mutate(base: &[u8], kind: &str, at: i64, extra: i64) -> Vec<u8> {
    let mut out = base.to_vec();
    match kind {
        "flip" => {
            let index = if at < 0 {
                (out.len() as i64 + at) as usize
            } else {
                at as usize
            };
            out[index] ^= extra as u8;
        }
        "truncate" => out.truncate(at as usize),
        "append" => out.extend(std::iter::repeat_n(0u8, extra as usize)),
        "swap-chunks" => {
            let first = fmt::HEADER_LEN + at as usize * fmt::CHUNK_STORED;
            let second = fmt::HEADER_LEN + extra as usize * fmt::CHUNK_STORED;
            for offset in 0..fmt::CHUNK_STORED {
                out.swap(first + offset, second + offset);
            }
        }
        _ => unreachable!(),
    }
    out
}

fn content_cases() -> Vec<Value> {
    CONTENT_SIZES
        .iter()
        .map(|size| {
            let label = format!("content-{size}");
            let key = folder_key(&label);
            let folder = fmt::FolderKey::new(&key);
            let file_id: fmt::FileId = stream(&format!("{label}/id"), 16).try_into().unwrap();
            let plaintext = stream(&format!("{label}/data"), *size);
            let count = fmt::chunk_count(*size as u64) as usize;
            let raw = stream(&format!("{label}/nonces"), count * fmt::NONCE_LEN);
            let nonces: Vec<[u8; fmt::NONCE_LEN]> = raw
                .chunks(fmt::NONCE_LEN)
                .map(|n| n.try_into().unwrap())
                .collect();
            let ciphertext =
                fmt::seal_with(&folder.file_key(&file_id).unwrap(), &plaintext, &nonces).unwrap();
            json!({
                "case": label,
                "folder_key": hex(&key),
                "file_id": hex(&file_id),
                "nonces": nonces.iter().map(|n| hex(n)).collect::<Vec<_>>(),
                "plaintext": hex(&plaintext),
                "ciphertext": hex(&ciphertext),
            })
        })
        .collect()
}

fn name_cases() -> Vec<Value> {
    let key = folder_key("names");
    let folder = fmt::FolderKey::new(&key);
    let mut cases = Vec::new();
    for (index, name) in NAMES.iter().enumerate() {
        for dir in 0..2 {
            let dir_iv: [u8; fmt::DIR_IV_LEN] =
                stream(&format!("names/dir-{dir}"), fmt::DIR_IV_LEN)
                    .try_into()
                    .unwrap();
            let plain = plaintext_name(name);
            let encrypted = fmt::encrypt_name(&folder, &dir_iv, &plain).unwrap();
            cases.push(json!({
                "case": format!("name-{index}-dir-{dir}"),
                "folder_key": hex(&key),
                "dir_iv": hex(&dir_iv),
                "name": plain,
                "on_disk": encrypted.on_disk,
                "encoded": encrypted.encoded,
                "sidecar_name": encrypted.sidecar.map(|(file, _)| file),
            }));
        }
    }
    cases
}

fn reject_cases(content: &[Value]) -> Vec<Value> {
    let base = content
        .iter()
        .find(|case| case["case"] == "content-131079")
        .unwrap();
    let folder = fmt::FolderKey::from_slice(&unhex(base["folder_key"].as_str().unwrap())).unwrap();
    let ciphertext = unhex(base["ciphertext"].as_str().unwrap());
    MUTATIONS
        .iter()
        .chain([("swap-first-two-chunks", "swap-chunks", 0i64, 1i64)].iter())
        .map(|(name, kind, at, extra)| {
            let error = fmt::open(&folder, &mutate(&ciphertext, kind, *at, *extra)).unwrap_err();
            json!({
                "case": *name,
                "from": base["case"],
                "mutation": {"kind": *kind, "at": *at, "extra": *extra},
                "error": format!("{error:?}"),
            })
        })
        .collect()
}

fn reject_name_cases(names: &[Value]) -> Vec<Value> {
    let base = &names[0];
    let key = unhex(base["folder_key"].as_str().unwrap());
    let folder = fmt::FolderKey::from_slice(&key).unwrap();
    let dir_iv: [u8; fmt::DIR_IV_LEN] = unhex(base["dir_iv"].as_str().unwrap()).try_into().unwrap();
    let other_iv: [u8; fmt::DIR_IV_LEN] = unhex(names[1]["dir_iv"].as_str().unwrap())
        .try_into()
        .unwrap();
    let encoded = base["encoded"].as_str().unwrap().to_string();
    let mut flipped = encoded.clone().into_bytes();
    flipped[3] = if flipped[3] == b'A' { b'B' } else { b'A' };
    let variants = [
        (
            "name-flipped-character",
            dir_iv,
            String::from_utf8(flipped).unwrap(),
        ),
        ("name-under-other-dir-iv", other_iv, encoded),
        ("name-not-base64", dir_iv, "not base64!!".to_string()),
        ("name-too-short", dir_iv, "AAAA".to_string()),
    ];
    variants
        .into_iter()
        .map(|(case, iv, text)| {
            let error = fmt::decrypt_name(&folder, &iv, &text).unwrap_err();
            json!({
                "case": case,
                "folder_key": hex(&key),
                "dir_iv": hex(&iv),
                "encoded": text,
                "error": format!("{error:?}"),
            })
        })
        .collect()
}

fn derive_cases() -> Vec<Value> {
    ["derive-a", "derive-b"]
        .iter()
        .map(|label| {
            let key = folder_key(label);
            let folder = fmt::FolderKey::new(&key);
            let file_id: fmt::FileId = stream(&format!("{label}/id"), 16).try_into().unwrap();
            json!({
                "case": *label,
                "folder_key": hex(&key),
                "name_cipher_key": hex(folder.name_cipher_key()),
                "name_auth_key": hex(folder.name_auth_key()),
                "file_id": hex(&file_id),
                "file_header": hex(folder.file_key(&file_id).unwrap().header()),
            })
        })
        .collect()
}

fn build() -> Value {
    let content = content_cases();
    let names = name_cases();
    let reject = reject_cases(&content);
    let reject_names = reject_name_cases(&names);
    json!({
        "format": "backend.ai/cc-storage/v1",
        "version": fmt::VERSION,
        "parameters": {
            "salt": String::from_utf8(fmt::SALT.to_vec()).unwrap(),
            "magic": hex(&fmt::MAGIC),
            "suite": fmt::SUITE_XCHACHA20_POLY1305,
            "header_len": fmt::HEADER_LEN,
            "file_id_len": fmt::FILE_ID_LEN,
            "chunk_plaintext": fmt::CHUNK_PLAINTEXT,
            "nonce_len": fmt::NONCE_LEN,
            "tag_len": fmt::TAG_LEN,
            "siv_len": fmt::SIV_LEN,
            "dir_iv_len": fmt::DIR_IV_LEN,
            "dir_iv_file": fmt::DIR_IV_FILE,
            "max_on_disk": fmt::MAX_ON_DISK,
            "long_prefix": fmt::LONG_PREFIX,
            "long_suffix": fmt::LONG_SUFFIX,
        },
        "derive": derive_cases(),
        "content": content,
        "names": names,
        "reject": reject,
        "reject_names": reject_names,
    })
}

fn expect(ok: bool, case: &str, what: &str, failures: &mut Vec<String>) {
    if !ok {
        failures.push(format!("{case}: {what}"));
    }
}

fn folder_of(case: &Value) -> fmt::FolderKey {
    fmt::FolderKey::from_slice(&unhex(case["folder_key"].as_str().unwrap())).unwrap()
}

fn dir_iv_of(case: &Value) -> [u8; fmt::DIR_IV_LEN] {
    unhex(case["dir_iv"].as_str().unwrap()).try_into().unwrap()
}

fn check(corpus: &Map<String, Value>) -> Vec<String> {
    let mut failures = Vec::new();
    for case in corpus["derive"].as_array().unwrap() {
        let name = case["case"].as_str().unwrap();
        let folder = folder_of(case);
        let file_id: fmt::FileId = unhex(case["file_id"].as_str().unwrap()).try_into().unwrap();
        expect(
            hex(folder.name_cipher_key()) == case["name_cipher_key"].as_str().unwrap(),
            name,
            "name cipher key",
            &mut failures,
        );
        expect(
            hex(folder.name_auth_key()) == case["name_auth_key"].as_str().unwrap(),
            name,
            "name authentication key",
            &mut failures,
        );
        expect(
            hex(folder.file_key(&file_id).unwrap().header())
                == case["file_header"].as_str().unwrap(),
            name,
            "file header",
            &mut failures,
        );
    }
    for case in corpus["content"].as_array().unwrap() {
        let name = case["case"].as_str().unwrap();
        let folder = folder_of(case);
        let file_id: fmt::FileId = unhex(case["file_id"].as_str().unwrap()).try_into().unwrap();
        let plaintext = unhex(case["plaintext"].as_str().unwrap());
        let ciphertext = unhex(case["ciphertext"].as_str().unwrap());
        let nonces: Vec<[u8; fmt::NONCE_LEN]> = case["nonces"]
            .as_array()
            .unwrap()
            .iter()
            .map(|n| unhex(n.as_str().unwrap()).try_into().unwrap())
            .collect();
        let sealed =
            fmt::seal_with(&folder.file_key(&file_id).unwrap(), &plaintext, &nonces).unwrap();
        expect(sealed == ciphertext, name, "sealed bytes", &mut failures);
        expect(
            fmt::open(&folder, &ciphertext).unwrap() == plaintext,
            name,
            "opened bytes",
            &mut failures,
        );
        expect(
            fmt::stored_len(plaintext.len() as u64) == ciphertext.len() as u64,
            name,
            "stored length",
            &mut failures,
        );
        expect(
            fmt::plaintext_len(ciphertext.len() as u64).unwrap() == plaintext.len() as u64,
            name,
            "plaintext length",
            &mut failures,
        );
    }
    for case in corpus["names"].as_array().unwrap() {
        let name = case["case"].as_str().unwrap();
        let folder = folder_of(case);
        let dir_iv = dir_iv_of(case);
        let plain = case["name"].as_str().unwrap();
        let encrypted = fmt::encrypt_name(&folder, &dir_iv, plain).unwrap();
        expect(
            encrypted.on_disk == case["on_disk"].as_str().unwrap(),
            name,
            "on-disk name",
            &mut failures,
        );
        expect(
            encrypted.encoded == case["encoded"].as_str().unwrap(),
            name,
            "encoded name",
            &mut failures,
        );
        expect(
            encrypted.sidecar.map(|(file, _)| file).as_deref() == case["sidecar_name"].as_str(),
            name,
            "sidecar name",
            &mut failures,
        );
        expect(
            fmt::decrypt_name(&folder, &dir_iv, case["encoded"].as_str().unwrap()).unwrap()
                == plain,
            name,
            "decrypted name",
            &mut failures,
        );
    }
    for case in corpus["reject"].as_array().unwrap() {
        let name = case["case"].as_str().unwrap();
        let base = corpus["content"]
            .as_array()
            .unwrap()
            .iter()
            .find(|entry| entry["case"] == case["from"])
            .unwrap();
        let broken = mutate(
            &unhex(base["ciphertext"].as_str().unwrap()),
            case["mutation"]["kind"].as_str().unwrap(),
            case["mutation"]["at"].as_i64().unwrap(),
            case["mutation"]["extra"].as_i64().unwrap(),
        );
        match fmt::open(&folder_of(base), &broken) {
            Ok(_) => failures.push(format!("{name}: accepted a mutated ciphertext")),
            Err(error) => expect(
                format!("{error:?}") == case["error"].as_str().unwrap(),
                name,
                "rejection reason",
                &mut failures,
            ),
        }
    }
    for case in corpus["reject_names"].as_array().unwrap() {
        let name = case["case"].as_str().unwrap();
        match fmt::decrypt_name(
            &folder_of(case),
            &dir_iv_of(case),
            case["encoded"].as_str().unwrap(),
        ) {
            Ok(_) => failures.push(format!("{name}: accepted a mutated name")),
            Err(error) => expect(
                format!("{error:?}") == case["error"].as_str().unwrap(),
                name,
                "rejection reason",
                &mut failures,
            ),
        }
    }
    failures
}

fn corpus_path() -> PathBuf {
    std::env::args()
        .nth(2)
        .map(PathBuf::from)
        .unwrap_or_else(|| {
            PathBuf::from(env!("CARGO_MANIFEST_DIR"))
                .join("../bai-storage-format/corpus/corpus.json")
        })
}

fn main() {
    let path = corpus_path();
    match std::env::args().nth(1).as_deref() {
        Some("generate") => {
            std::fs::write(&path, serde_json::to_string_pretty(&build()).unwrap()).unwrap();
            println!("wrote {}", path.display());
        }
        Some("check") => {
            let corpus: Map<String, Value> =
                serde_json::from_str(&std::fs::read_to_string(&path).unwrap()).unwrap();
            let failures = check(&corpus);
            let total: usize = ["derive", "content", "names", "reject", "reject_names"]
                .iter()
                .map(|section| corpus[*section].as_array().unwrap().len())
                .sum();
            for failure in &failures {
                eprintln!("{failure}");
            }
            println!("{total} cases, {} failures", failures.len());
            std::process::exit(i32::from(!failures.is_empty()));
        }
        _ => {
            eprintln!("usage: bai-storage-corpus generate|check [path]");
            std::process::exit(2);
        }
    }
}

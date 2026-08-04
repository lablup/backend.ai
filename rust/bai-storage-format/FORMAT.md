# Backend.AI confidential storage format, version 1

Identifier `backend.ai/cc-storage/v1`. This document is normative for the bytes. Where it and any
implementation disagree, the frozen conformance corpus at `corpus/corpus.json` decides, because the
corpus is the format's definition of record and every surface — the command-line client, the software
development kit, the browser, and the guest's own filesystem layer — is read against it.

All integers are little-endian. All lengths are in bytes.

## 1. Scope

The format protects folder content and folder structure against a party that can read and rewrite the
backing store: the storage operator. It does not carry access control. User-to-user authorisation is
the platform's, unchanged, and a party holding the folder key is authorised by definition.

The format is symmetric. A key that reads a folder also writes it.

## 2. Key derivation

The folder key is 32 uniformly random bytes.

    PRK          = HKDF-Extract(SHA-256, salt = "backend.ai/cc-storage/v1", ikm = folder key)
    name secrets = HKDF-Expand(PRK, info = "name", 64)
    name cipher key = name secrets[0..32]
    name auth key   = name secrets[32..64]
    file key(id) = HKDF-Expand(PRK, info = "file" || id, 32)

`id` is the 16-byte file identifier from the file header.

## 3. Content framing

### 3.1 Header

22 bytes, present exactly once at the start of every encrypted file.

| offset | length | value |
|---|---|---|
| 0 | 4 | `42 41 43 46`, the ASCII `BACF` |
| 4 | 1 | format version, `01` |
| 5 | 1 | cipher suite, `01` for XChaCha20-Poly1305 |
| 6 | 16 | file identifier, uniformly random, chosen when the file is created |

### 3.2 Frames

Plaintext is cut into chunks of exactly 65536 bytes, the last of which may be shorter. A file whose
plaintext is empty has exactly one chunk, of length zero; no encrypted file has zero chunks.

Chunk `i` is stored as

    nonce (24, uniformly random) || XChaCha20-Poly1305(
        key   = file key(id),
        nonce = nonce,
        aad   = header (22) || i as u64 (8) || last (1),
        msg   = chunk plaintext)

where `last` is `01` for the final chunk of the file and `00` otherwise. The ciphertext-and-tag field
is the chunk plaintext length plus 16.

Frames are concatenated after the header in index order, so frame `i` begins at offset
`22 + i * 65576` and every chunk but the last occupies exactly 65576 bytes. A reader may therefore
seek to any chunk without reading the ones before it, and a writer may replace one chunk in place.

**A chunk rewritten in place must draw a fresh nonce.** Reusing a nonce with the same file key and
different plaintext discloses the exclusive-or of the two plaintexts.

### 3.3 Length

    chunk count(n)   = max(1, ceil(n / 65536))
    stored length(n) = 22 + n + 40 * chunk count(n)

The inverse is exact: the stored length determines the plaintext length, so a reader learns the
plaintext length from the file size without decrypting anything.

### 3.4 What the framing detects

Modification of any byte of ciphertext, tag, nonce, file identifier, version or suite. Reordering
frames within a file, because the index is authenticated. Moving a frame between files, because the
file identifier is authenticated and keys the frame. Truncation to a chunk boundary, because the new
final frame does not carry the final-chunk flag. Extension, because the appended bytes make the
previous final frame non-final.

Deletion of a whole file, rollback of a whole file to an earlier version, and the tree shape itself
are **not** detected. That is the recorded property of the default folder tier: encrypted, not
tamper-evident. It is a per-folder disclosure, not a defect to be silently carried.

## 4. Name and directory-structure encryption

### 4.1 Directory initialisation vector

Every ciphertext directory, the folder root included, contains a file named `.bai.diriv` holding 16
uniformly random bytes chosen when that directory is created. It is never encrypted and never renamed.
Because names are keyed by the containing directory's vector, the same plaintext name in two
directories yields two unrelated ciphertext names, and renaming a directory leaves the names inside it
valid.

### 4.2 Name encryption

Name encryption is deterministic, so a lookup can encrypt the wanted name and go straight to it.

    siv       = HMAC-SHA-256(name auth key, dir iv || name)[0..16]
    body      = XChaCha20(name cipher key, nonce = siv || 00 * 8, counter 0) xor name
    sealed    = siv || body
    encoded   = base64url(sealed), no padding

`name` is the UTF-8 encoding of one path component. It must not be empty, `.`, `..`, `.bai.diriv`, or
contain `/` or a zero byte.

Decryption decrypts `body`, recomputes the synthetic value over the recovered name, and compares in
constant time. A mismatch is an authentication failure; so is a recovered name that is not valid UTF-8
or not a usable component.

### 4.3 Long names

If `encoded` is 255 characters or shorter it is the on-disk name. Otherwise the on-disk name is

    "bai.L." || base64url(SHA-256(encoded)), no padding

which is 49 characters, and the full `encoded` string is written as the sole content of a sidecar file
whose name is the on-disk name with `.n` appended.

Short-form names cannot collide with either reserved shape: base64url contains no `.`, so an encrypted
name is never `.bai.diriv` and never begins with `bai.L.`.

### 4.4 Structure

The ciphertext tree mirrors the plaintext tree one directory for one directory and one file for one
file. Visible to the storage operator: the number of entries, the depth and branching of the tree,
each file's length to within 65536 bytes, and every timestamp. Only names and content are hidden.

## 5. The conformance corpus

`corpus/corpus.json` is frozen. Regenerating it is a format change and requires a new version byte.

Sections: `parameters` restates the constants above; `derive` pins the subkeys and file headers for
two folder keys; `content` pins six ciphertexts spanning the empty, single-chunk, boundary and
multi-chunk cases, each with its file identifier and per-chunk nonces so that sealing is byte-checkable
and not merely round-trippable; `names` pins twelve encrypted names including the 255-character
boundary and the long-name split, each under two directory vectors; `reject` and `reject_names` pin
mutations that must be refused, each with the refusal reason.

A `reject` case names a `content` case and a mutation to apply to it — `flip` a byte, `truncate` to a
length, `append` zero bytes, or `swap-chunks` two frames. A negative `at` counts back from the end.

`cargo run -p bai-storage-corpus -- check` reads the corpus against this crate.
`python3 bai-storage-format-python/conformance.py` reads it against the Python extension.
`node bai-storage-format-wasm/conformance.cjs` reads it against the WebAssembly build.
All three must report zero failures before the format is considered implemented anywhere.

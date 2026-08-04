const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const format = require(path.join(__dirname, "pkg", "bai_storage_format_wasm.js"));
const corpus = JSON.parse(
  fs.readFileSync(path.join(root, "bai-storage-format", "corpus", "corpus.json"), "utf8"),
);

const unhex = (text) => Buffer.from(text, "hex");
const hex = (bytes) => Buffer.from(bytes).toString("hex");
const failures = [];
let total = 0;

function mutate(base, kind, at, extra) {
  const out = Buffer.from(base);
  if (kind === "flip") {
    const index = at < 0 ? out.length + at : at;
    out[index] ^= extra;
    return out;
  }
  if (kind === "truncate") return out.subarray(0, at);
  if (kind === "append") return Buffer.concat([out, Buffer.alloc(extra)]);
  const stride = format.chunk_stored();
  const first = format.header_len() + at * stride;
  const second = format.header_len() + extra * stride;
  const held = Buffer.from(out.subarray(first, first + stride));
  out.copy(out, first, second, second + stride);
  held.copy(out, second);
  return out;
}

function rejects(name, expected, call) {
  try {
    call();
  } catch (error) {
    const code = String(error.message ?? error).split(":")[0];
    if (code !== expected) failures.push(`${name}: rejected as ${code}, expected ${expected}`);
    return;
  }
  failures.push(`${name}: accepted a mutated input`);
}

for (const entry of corpus.derive) {
  total += 1;
  const key = new format.FolderKey(unhex(entry.folder_key));
  if (hex(key.file_header(unhex(entry.file_id))) !== entry.file_header) {
    failures.push(`${entry.case}: file header`);
  }
}

for (const entry of corpus.content) {
  total += 1;
  const key = new format.FolderKey(unhex(entry.folder_key));
  const plaintext = unhex(entry.plaintext);
  const ciphertext = unhex(entry.ciphertext);
  const nonces = Buffer.concat(entry.nonces.map(unhex));
  const sealed = key.encrypt_with(unhex(entry.file_id), plaintext, nonces);
  if (hex(sealed) !== entry.ciphertext) failures.push(`${entry.case}: sealed bytes`);
  if (hex(key.decrypt(ciphertext)) !== entry.plaintext) {
    failures.push(`${entry.case}: opened bytes`);
  }
  if (format.stored_len(BigInt(plaintext.length)) !== BigInt(ciphertext.length)) {
    failures.push(`${entry.case}: stored length`);
  }
  if (format.plaintext_len(BigInt(ciphertext.length)) !== BigInt(plaintext.length)) {
    failures.push(`${entry.case}: plaintext length`);
  }
}

for (const entry of corpus.names) {
  total += 1;
  const key = new format.FolderKey(unhex(entry.folder_key));
  const dirIv = unhex(entry.dir_iv);
  const encrypted = key.encrypt_name(dirIv, entry.name);
  if (encrypted.on_disk !== entry.on_disk || encrypted.encoded !== entry.encoded) {
    failures.push(`${entry.case}: encrypted name`);
  }
  if ((encrypted.sidecar_name ?? null) !== entry.sidecar_name) {
    failures.push(`${entry.case}: sidecar name`);
  }
  if (key.decrypt_name(dirIv, entry.encoded) !== entry.name) {
    failures.push(`${entry.case}: decrypted name`);
  }
}

for (const entry of corpus.reject) {
  total += 1;
  const base = corpus.content.find((candidate) => candidate.case === entry.from);
  const key = new format.FolderKey(unhex(base.folder_key));
  const broken = mutate(
    unhex(base.ciphertext),
    entry.mutation.kind,
    entry.mutation.at,
    entry.mutation.extra,
  );
  rejects(entry.case, entry.error, () => key.decrypt(broken));
}

for (const entry of corpus.reject_names) {
  total += 1;
  const key = new format.FolderKey(unhex(entry.folder_key));
  rejects(entry.case, entry.error, () => key.decrypt_name(unhex(entry.dir_iv), entry.encoded));
}

for (const failure of failures) console.error(failure);
console.log(`${total} cases, ${failures.length} failures`);
process.exit(failures.length === 0 ? 0 : 1);

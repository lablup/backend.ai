export const FORMAT_ID = "backend.ai/cc-storage/v1";
export const CAPABILITY_HEADER = "X-BackendAI-Storage-Format";

export class FolderCipher {
  constructor(fmt, material) {
    this.fmt = fmt;
    this.material = material;
    this.key = new fmt.FolderKey(material.key);
  }
}

export function materialFromRelease(released) {
  const unhex = (text) => Uint8Array.from(text.match(/../g).map((b) => parseInt(b, 16)));
  return {
    key: unhex(released.key),
    tier: released.tier,
  };
}

export async function* seal(cipher, blob) {
  const fmt = cipher.fmt;
  const fileId = fmt.new_file_id();
  yield cipher.key.file_header(fileId);
  const span = fmt.chunk_plaintext();
  const count = Math.max(1, Math.ceil(blob.size / span));
  for (let index = 0; index < count; index += 1) {
    const slice = blob.slice(index * span, Math.min(blob.size, (index + 1) * span));
    const nonce = crypto.getRandomValues(new Uint8Array(fmt.nonce_len()));
    yield cipher.key.seal_chunk(
      fileId,
      BigInt(index),
      index + 1 === count,
      nonce,
      new Uint8Array(await slice.arrayBuffer()),
    );
  }
}

export async function* open(cipher, blob) {
  const fmt = cipher.fmt;
  const head = await blob.slice(0, fmt.header_len() + fmt.chunk_stored()).arrayBuffer();
  const fileId = fmt.parse_header(new Uint8Array(head));
  const count = Number(fmt.chunk_count(fmt.plaintext_len(BigInt(blob.size))));
  for (let index = 0; index < count; index += 1) {
    const start = Number(fmt.chunk_offset(BigInt(index)));
    const frame = await blob
      .slice(start, Math.min(blob.size, start + fmt.chunk_stored()))
      .arrayBuffer();
    yield cipher.key.open_chunk(
      fileId,
      BigInt(index),
      index + 1 === count,
      new Uint8Array(frame),
    );
  }
}

const join = (parent, child) => (parent ? `${parent}/${child}` : child);
const components = (relpath) =>
  String(relpath)
    .split("/")
    .filter((part) => part !== "" && part !== "." && part !== "/");

export class CipherPaths {
  constructor(cipher, store) {
    this.cipher = cipher;
    this.store = store;
    this.ivs = new Map();
  }

  async sealed(cipherDir) {
    const fmt = this.cipher.fmt;
    return (await this.store.listdir(cipherDir)).filter((entry) => !fmt.is_reserved(entry.name));
  }

  async dirIv(cipherDir, create) {
    if (this.ivs.has(cipherDir)) return this.ivs.get(cipherDir);
    const fmt = this.cipher.fmt;
    const marker = join(cipherDir, fmt.dir_iv_file());
    let iv = await this.store.read(marker);
    if (iv === null) {
      if (cipherDir === "" && (await this.sealed(cipherDir)).length > 0) {
        throw new Error(
          `the ciphertext root holds sealed entries but no ${fmt.dir_iv_file()}; this folder was` +
            " written before the vector of its root directory was carried on the export, and no" +
            " key releasable today decrypts the names in it",
        );
      }
      if (!create) throw new Error(`no directory vector at ${marker}`);
      await this.store.mkdir(cipherDir);
      await this.store.write(marker, fmt.new_dir_iv());
      iv = await this.store.read(marker);
    }
    this.ivs.set(cipherDir, iv);
    return iv;
  }

  async resolve(relpath, create = false) {
    let current = "";
    for (const part of components(relpath)) {
      const iv = await this.dirIv(current, create);
      const encrypted = this.cipher.key.encrypt_name(iv, part);
      if (create && encrypted.sidecar_name !== undefined) {
        await this.store.write(
          join(current, encrypted.sidecar_name),
          new TextEncoder().encode(encrypted.sidecar_content),
        );
      }
      current = join(current, encrypted.on_disk);
    }
    return current;
  }

  async listing(relpath) {
    const fmt = this.cipher.fmt;
    const cipherDir = await this.resolve(relpath);
    const sealed = await this.sealed(cipherDir);
    if (sealed.length === 0) return [];
    const iv = await this.dirIv(cipherDir, false);
    const out = [];
    for (const entry of sealed) {
      const sidecar = fmt.sidecar_of(entry.name);
      const encoded =
        sidecar === undefined
          ? entry.name
          : new TextDecoder().decode(await this.store.read(join(cipherDir, sidecar)));
      out.push({
        name: this.cipher.key.decrypt_name(iv, encoded),
        onDisk: entry.name,
        size: entry.isDir ? entry.size : Number(fmt.plaintext_len(BigInt(entry.size))),
        isDir: entry.isDir,
      });
    }
    return out;
  }
}

mod content;
mod error;
mod key;
mod name;

pub use content::{
    chunk_count, chunk_offset, open, parse_header, plaintext_len, seal, seal_with, stored_len,
    FileKey, CHUNK_OVERHEAD, CHUNK_PLAINTEXT, CHUNK_STORED, FILE_ID_LEN, HEADER_LEN, MAGIC,
    NONCE_LEN, SUITE_XCHACHA20_POLY1305, TAG_LEN, VERSION,
};
pub use error::{Error, Result};
pub use key::{new_file_id, FileId, FolderKey, FOLDER_KEY_LEN, SALT};
pub use name::{
    decrypt as decrypt_name, encrypt as encrypt_name, is_reserved, new_dir_iv, sidecar_of,
    EncryptedName, DIR_IV_FILE, DIR_IV_LEN, LONG_PREFIX, LONG_SUFFIX, MAX_ON_DISK, SIV_LEN,
};

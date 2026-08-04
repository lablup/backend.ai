use bai_storage_format as fmt;
use wasm_bindgen::prelude::*;

fn raise(error: fmt::Error) -> JsError {
    JsError::new(&format!("{error:?}: {error}"))
}

fn wrap<T>(result: fmt::Result<T>) -> Result<T, JsError> {
    result.map_err(raise)
}

fn sized<const N: usize>(bytes: &[u8]) -> Result<[u8; N], JsError> {
    bytes.try_into().map_err(|_| raise(fmt::Error::KeyLength))
}

#[wasm_bindgen(getter_with_clone)]
pub struct EncryptedName {
    pub on_disk: String,
    pub encoded: String,
    pub sidecar_name: Option<String>,
    pub sidecar_content: Option<String>,
}

#[wasm_bindgen]
pub struct FolderKey(fmt::FolderKey);

#[wasm_bindgen]
impl FolderKey {
    #[wasm_bindgen(constructor)]
    pub fn new(folder_key: &[u8]) -> Result<FolderKey, JsError> {
        Ok(Self(wrap(fmt::FolderKey::from_slice(folder_key))?))
    }

    pub fn file_header(&self, file_id: &[u8]) -> Result<Vec<u8>, JsError> {
        Ok(wrap(self.0.file_key(&sized(file_id)?))?.header().to_vec())
    }

    pub fn encrypt(&self, plaintext: &[u8]) -> Result<Vec<u8>, JsError> {
        wrap(fmt::seal(&self.0, plaintext))
    }

    pub fn encrypt_with(
        &self,
        file_id: &[u8],
        plaintext: &[u8],
        nonces: &[u8],
    ) -> Result<Vec<u8>, JsError> {
        let key = wrap(self.0.file_key(&sized(file_id)?))?;
        let nonces = nonces
            .chunks(fmt::NONCE_LEN)
            .map(sized)
            .collect::<Result<Vec<_>, _>>()?;
        wrap(fmt::seal_with(&key, plaintext, &nonces))
    }

    pub fn decrypt(&self, ciphertext: &[u8]) -> Result<Vec<u8>, JsError> {
        wrap(fmt::open(&self.0, ciphertext))
    }

    pub fn seal_chunk(
        &self,
        file_id: &[u8],
        index: u64,
        last: bool,
        nonce: &[u8],
        plaintext: &[u8],
    ) -> Result<Vec<u8>, JsError> {
        let key = wrap(self.0.file_key(&sized(file_id)?))?;
        wrap(key.seal_chunk(index, last, &sized(nonce)?, plaintext))
    }

    pub fn open_chunk(
        &self,
        file_id: &[u8],
        index: u64,
        last: bool,
        stored: &[u8],
    ) -> Result<Vec<u8>, JsError> {
        let key = wrap(self.0.file_key(&sized(file_id)?))?;
        wrap(key.open_chunk(index, last, stored))
    }

    pub fn encrypt_name(&self, dir_iv: &[u8], name: &str) -> Result<EncryptedName, JsError> {
        let encrypted = wrap(fmt::encrypt_name(&self.0, &sized(dir_iv)?, name))?;
        let (sidecar_name, sidecar_content) = match encrypted.sidecar {
            Some((file, content)) => (Some(file), Some(content)),
            None => (None, None),
        };
        Ok(EncryptedName {
            on_disk: encrypted.on_disk,
            encoded: encrypted.encoded,
            sidecar_name,
            sidecar_content,
        })
    }

    pub fn decrypt_name(&self, dir_iv: &[u8], encoded: &str) -> Result<String, JsError> {
        wrap(fmt::decrypt_name(&self.0, &sized(dir_iv)?, encoded))
    }
}

#[wasm_bindgen]
pub fn generate_folder_key() -> Result<Vec<u8>, JsError> {
    Ok(wrap(fmt::FolderKey::generate())?.to_vec())
}

#[wasm_bindgen]
pub fn new_file_id() -> Result<Vec<u8>, JsError> {
    Ok(wrap(fmt::new_file_id())?.to_vec())
}

#[wasm_bindgen]
pub fn new_dir_iv() -> Result<Vec<u8>, JsError> {
    Ok(wrap(fmt::new_dir_iv())?.to_vec())
}

#[wasm_bindgen]
pub fn parse_header(stored: &[u8]) -> Result<Vec<u8>, JsError> {
    Ok(wrap(fmt::parse_header(stored))?.to_vec())
}

#[wasm_bindgen]
pub fn chunk_count(plaintext_len: u64) -> u64 {
    fmt::chunk_count(plaintext_len)
}

#[wasm_bindgen]
pub fn chunk_offset(index: u64) -> u64 {
    fmt::chunk_offset(index)
}

#[wasm_bindgen]
pub fn stored_len(plaintext_len: u64) -> u64 {
    fmt::stored_len(plaintext_len)
}

#[wasm_bindgen]
pub fn plaintext_len(stored_len: u64) -> Result<u64, JsError> {
    wrap(fmt::plaintext_len(stored_len))
}

#[wasm_bindgen]
pub fn sidecar_of(on_disk: &str) -> Option<String> {
    fmt::sidecar_of(on_disk)
}

#[wasm_bindgen]
pub fn is_reserved(on_disk: &str) -> bool {
    fmt::is_reserved(on_disk)
}

#[wasm_bindgen]
pub fn version() -> u8 {
    fmt::VERSION
}

#[wasm_bindgen]
pub fn chunk_plaintext() -> usize {
    fmt::CHUNK_PLAINTEXT
}

#[wasm_bindgen]
pub fn chunk_stored() -> usize {
    fmt::CHUNK_STORED
}

#[wasm_bindgen]
pub fn header_len() -> usize {
    fmt::HEADER_LEN
}

#[wasm_bindgen]
pub fn nonce_len() -> usize {
    fmt::NONCE_LEN
}

#[wasm_bindgen]
pub fn dir_iv_len() -> usize {
    fmt::DIR_IV_LEN
}

#[wasm_bindgen]
pub fn dir_iv_file() -> String {
    fmt::DIR_IV_FILE.to_string()
}

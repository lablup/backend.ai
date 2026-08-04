use std::borrow::Cow;

use ::bai_storage_format as fmt;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

fn raise(error: fmt::Error) -> PyErr {
    PyValueError::new_err(format!("{error:?}: {error}"))
}

fn wrap<T>(result: fmt::Result<T>) -> PyResult<T> {
    result.map_err(raise)
}

fn sized<const N: usize>(bytes: &[u8]) -> PyResult<[u8; N]> {
    bytes.try_into().map_err(|_| raise(fmt::Error::KeyLength))
}

#[pyclass(frozen, get_all)]
struct EncryptedName {
    on_disk: String,
    encoded: String,
    sidecar_name: Option<String>,
    sidecar_content: Option<String>,
}

#[pyclass(frozen)]
struct FolderKey(fmt::FolderKey);

#[pymethods]
impl FolderKey {
    #[new]
    fn new(folder_key: &[u8]) -> PyResult<Self> {
        Ok(Self(wrap(fmt::FolderKey::from_slice(folder_key))?))
    }

    fn file_header<'a>(&self, file_id: &[u8]) -> PyResult<Cow<'a, [u8]>> {
        let key = wrap(self.0.file_key(&sized(file_id)?))?;
        Ok(Cow::Owned(key.header().to_vec()))
    }

    fn encrypt<'a>(&self, plaintext: &[u8]) -> PyResult<Cow<'a, [u8]>> {
        Ok(Cow::Owned(wrap(fmt::seal(&self.0, plaintext))?))
    }

    fn encrypt_with<'a>(
        &self,
        file_id: &[u8],
        plaintext: &[u8],
        nonces: Vec<Vec<u8>>,
    ) -> PyResult<Cow<'a, [u8]>> {
        let key = wrap(self.0.file_key(&sized(file_id)?))?;
        let nonces = nonces
            .iter()
            .map(|nonce| sized(nonce))
            .collect::<PyResult<Vec<_>>>()?;
        Ok(Cow::Owned(wrap(fmt::seal_with(&key, plaintext, &nonces))?))
    }

    fn decrypt<'a>(&self, ciphertext: &[u8]) -> PyResult<Cow<'a, [u8]>> {
        Ok(Cow::Owned(wrap(fmt::open(&self.0, ciphertext))?))
    }

    fn seal_chunk<'a>(
        &self,
        file_id: &[u8],
        index: u64,
        last: bool,
        nonce: &[u8],
        plaintext: &[u8],
    ) -> PyResult<Cow<'a, [u8]>> {
        let key = wrap(self.0.file_key(&sized(file_id)?))?;
        Ok(Cow::Owned(wrap(key.seal_chunk(
            index,
            last,
            &sized(nonce)?,
            plaintext,
        ))?))
    }

    fn open_chunk<'a>(
        &self,
        file_id: &[u8],
        index: u64,
        last: bool,
        stored: &[u8],
    ) -> PyResult<Cow<'a, [u8]>> {
        let key = wrap(self.0.file_key(&sized(file_id)?))?;
        Ok(Cow::Owned(wrap(key.open_chunk(index, last, stored))?))
    }

    fn encrypt_name(&self, dir_iv: &[u8], name: &str) -> PyResult<EncryptedName> {
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

    fn decrypt_name(&self, dir_iv: &[u8], encoded: &str) -> PyResult<String> {
        wrap(fmt::decrypt_name(&self.0, &sized(dir_iv)?, encoded))
    }
}

#[pyfunction]
fn generate_folder_key<'a>() -> PyResult<Cow<'a, [u8]>> {
    Ok(Cow::Owned(wrap(fmt::FolderKey::generate())?.to_vec()))
}

#[pyfunction]
fn new_file_id<'a>() -> PyResult<Cow<'a, [u8]>> {
    Ok(Cow::Owned(wrap(fmt::new_file_id())?.to_vec()))
}

#[pyfunction]
fn new_dir_iv<'a>() -> PyResult<Cow<'a, [u8]>> {
    Ok(Cow::Owned(wrap(fmt::new_dir_iv())?.to_vec()))
}

#[pyfunction]
fn parse_header<'a>(stored: &[u8]) -> PyResult<Cow<'a, [u8]>> {
    Ok(Cow::Owned(wrap(fmt::parse_header(stored))?.to_vec()))
}

#[pyfunction]
fn chunk_count(plaintext_len: u64) -> u64 {
    fmt::chunk_count(plaintext_len)
}

#[pyfunction]
fn chunk_offset(index: u64) -> u64 {
    fmt::chunk_offset(index)
}

#[pyfunction]
fn stored_len(plaintext_len: u64) -> u64 {
    fmt::stored_len(plaintext_len)
}

#[pyfunction]
fn plaintext_len(stored_len: u64) -> PyResult<u64> {
    wrap(fmt::plaintext_len(stored_len))
}

#[pyfunction]
fn sidecar_of(on_disk: &str) -> Option<String> {
    fmt::sidecar_of(on_disk)
}

#[pyfunction]
fn is_reserved(on_disk: &str) -> bool {
    fmt::is_reserved(on_disk)
}

#[pymodule]
fn bai_storage_format(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_class::<FolderKey>()?;
    module.add_class::<EncryptedName>()?;
    module.add_function(wrap_pyfunction!(generate_folder_key, module)?)?;
    module.add_function(wrap_pyfunction!(new_file_id, module)?)?;
    module.add_function(wrap_pyfunction!(new_dir_iv, module)?)?;
    module.add_function(wrap_pyfunction!(parse_header, module)?)?;
    module.add_function(wrap_pyfunction!(chunk_count, module)?)?;
    module.add_function(wrap_pyfunction!(chunk_offset, module)?)?;
    module.add_function(wrap_pyfunction!(stored_len, module)?)?;
    module.add_function(wrap_pyfunction!(plaintext_len, module)?)?;
    module.add_function(wrap_pyfunction!(sidecar_of, module)?)?;
    module.add_function(wrap_pyfunction!(is_reserved, module)?)?;
    module.add("VERSION", fmt::VERSION)?;
    module.add("CHUNK_PLAINTEXT", fmt::CHUNK_PLAINTEXT)?;
    module.add("CHUNK_STORED", fmt::CHUNK_STORED)?;
    module.add("HEADER_LEN", fmt::HEADER_LEN)?;
    module.add("NONCE_LEN", fmt::NONCE_LEN)?;
    module.add("TAG_LEN", fmt::TAG_LEN)?;
    module.add("FILE_ID_LEN", fmt::FILE_ID_LEN)?;
    module.add("DIR_IV_LEN", fmt::DIR_IV_LEN)?;
    module.add("DIR_IV_FILE", fmt::DIR_IV_FILE)?;
    module.add("MAX_ON_DISK", fmt::MAX_ON_DISK)?;
    Ok(())
}

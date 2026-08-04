use hkdf::Hkdf;
use sha2::Sha256;

use crate::content::{FileKey, FILE_ID_LEN};
use crate::error::{Error, Result};

pub const FOLDER_KEY_LEN: usize = 32;
pub const SALT: &[u8] = b"backend.ai/cc-storage/v1";

pub type FileId = [u8; FILE_ID_LEN];

pub struct FolderKey {
    hk: Hkdf<Sha256>,
    name_secrets: [u8; 64],
}

impl FolderKey {
    pub fn new(folder_key: &[u8; FOLDER_KEY_LEN]) -> Self {
        let hk = Hkdf::<Sha256>::new(Some(SALT), folder_key);
        let mut name_secrets = [0u8; 64];
        hk.expand(b"name", &mut name_secrets).unwrap();
        Self { hk, name_secrets }
    }

    pub fn from_slice(folder_key: &[u8]) -> Result<Self> {
        let bytes: [u8; FOLDER_KEY_LEN] = folder_key.try_into().map_err(|_| Error::KeyLength)?;
        Ok(Self::new(&bytes))
    }

    pub fn generate() -> Result<[u8; FOLDER_KEY_LEN]> {
        let mut bytes = [0u8; FOLDER_KEY_LEN];
        getrandom::getrandom(&mut bytes).map_err(|_| Error::Random)?;
        Ok(bytes)
    }

    pub fn name_cipher_key(&self) -> &[u8; 32] {
        self.name_secrets[..32].try_into().unwrap()
    }

    pub fn name_auth_key(&self) -> &[u8] {
        &self.name_secrets[32..]
    }

    pub fn file_key(&self, file_id: &FileId) -> Result<FileKey> {
        let mut info = [0u8; 4 + FILE_ID_LEN];
        info[..4].copy_from_slice(b"file");
        info[4..].copy_from_slice(file_id);
        let mut derived = [0u8; 32];
        self.hk.expand(&info, &mut derived).unwrap();
        FileKey::new(*file_id, &derived)
    }
}

pub fn new_file_id() -> Result<FileId> {
    let mut id = [0u8; FILE_ID_LEN];
    getrandom::getrandom(&mut id).map_err(|_| Error::Random)?;
    Ok(id)
}

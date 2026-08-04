use chacha20poly1305::aead::{Aead, KeyInit, Payload};
use chacha20poly1305::{XChaCha20Poly1305, XNonce};

use crate::error::{Error, Result};
use crate::key::{new_file_id, FileId, FolderKey};

pub const MAGIC: [u8; 4] = *b"BACF";
pub const VERSION: u8 = 1;
pub const SUITE_XCHACHA20_POLY1305: u8 = 1;
pub const FILE_ID_LEN: usize = 16;
pub const HEADER_LEN: usize = 4 + 1 + 1 + FILE_ID_LEN;
pub const NONCE_LEN: usize = 24;
pub const TAG_LEN: usize = 16;
pub const CHUNK_PLAINTEXT: usize = 65536;
pub const CHUNK_OVERHEAD: usize = NONCE_LEN + TAG_LEN;
pub const CHUNK_STORED: usize = CHUNK_PLAINTEXT + CHUNK_OVERHEAD;

pub struct FileKey {
    header: [u8; HEADER_LEN],
    cipher: XChaCha20Poly1305,
}

impl FileKey {
    pub fn new(file_id: FileId, derived: &[u8; 32]) -> Result<Self> {
        let mut header = [0u8; HEADER_LEN];
        header[..4].copy_from_slice(&MAGIC);
        header[4] = VERSION;
        header[5] = SUITE_XCHACHA20_POLY1305;
        header[6..].copy_from_slice(&file_id);
        let cipher = XChaCha20Poly1305::new_from_slice(derived).map_err(|_| Error::KeyLength)?;
        Ok(Self { header, cipher })
    }

    pub fn header(&self) -> &[u8; HEADER_LEN] {
        &self.header
    }

    pub fn file_id(&self) -> FileId {
        self.header[6..].try_into().unwrap()
    }

    fn aad(&self, index: u64, last: bool) -> [u8; HEADER_LEN + 9] {
        let mut aad = [0u8; HEADER_LEN + 9];
        aad[..HEADER_LEN].copy_from_slice(&self.header);
        aad[HEADER_LEN..HEADER_LEN + 8].copy_from_slice(&index.to_le_bytes());
        aad[HEADER_LEN + 8] = u8::from(last);
        aad
    }

    pub fn seal_chunk(
        &self,
        index: u64,
        last: bool,
        nonce: &[u8; NONCE_LEN],
        plaintext: &[u8],
    ) -> Result<Vec<u8>> {
        if plaintext.len() > CHUNK_PLAINTEXT || (!last && plaintext.len() != CHUNK_PLAINTEXT) {
            return Err(Error::ChunkSize);
        }
        let aad = self.aad(index, last);
        let sealed = self
            .cipher
            .encrypt(
                &XNonce::from(*nonce),
                Payload {
                    msg: plaintext,
                    aad: &aad,
                },
            )
            .map_err(|_| Error::Authentication)?;
        let mut out = Vec::with_capacity(NONCE_LEN + sealed.len());
        out.extend_from_slice(nonce);
        out.extend_from_slice(&sealed);
        Ok(out)
    }

    pub fn seal_chunk_random(&self, index: u64, last: bool, plaintext: &[u8]) -> Result<Vec<u8>> {
        let mut nonce = [0u8; NONCE_LEN];
        getrandom::getrandom(&mut nonce).map_err(|_| Error::Random)?;
        self.seal_chunk(index, last, &nonce, plaintext)
    }

    pub fn open_chunk(&self, index: u64, last: bool, stored: &[u8]) -> Result<Vec<u8>> {
        if stored.len() < CHUNK_OVERHEAD || stored.len() > CHUNK_STORED {
            return Err(Error::Truncated);
        }
        let aad = self.aad(index, last);
        let nonce: [u8; NONCE_LEN] = stored[..NONCE_LEN].try_into().unwrap();
        self.cipher
            .decrypt(
                &XNonce::from(nonce),
                Payload {
                    msg: &stored[NONCE_LEN..],
                    aad: &aad,
                },
            )
            .map_err(|_| Error::Authentication)
    }
}

pub fn chunk_count(plaintext_len: u64) -> u64 {
    if plaintext_len == 0 {
        1
    } else {
        plaintext_len.div_ceil(CHUNK_PLAINTEXT as u64)
    }
}

pub fn stored_len(plaintext_len: u64) -> u64 {
    HEADER_LEN as u64 + plaintext_len + chunk_count(plaintext_len) * CHUNK_OVERHEAD as u64
}

pub fn plaintext_len(stored_len: u64) -> Result<u64> {
    let body = stored_len
        .checked_sub(HEADER_LEN as u64)
        .ok_or(Error::Truncated)?;
    let full = body / CHUNK_STORED as u64;
    let rest = body % CHUNK_STORED as u64;
    let (chunks, tail) = if rest == 0 {
        (full, CHUNK_PLAINTEXT as u64)
    } else {
        (
            full + 1,
            rest.checked_sub(CHUNK_OVERHEAD as u64)
                .ok_or(Error::Truncated)?,
        )
    };
    if chunks == 0 {
        return Err(Error::Truncated);
    }
    Ok((chunks - 1) * CHUNK_PLAINTEXT as u64 + tail)
}

pub fn chunk_offset(index: u64) -> u64 {
    HEADER_LEN as u64 + index * CHUNK_STORED as u64
}

pub fn parse_header(stored: &[u8]) -> Result<FileId> {
    if stored.len() < HEADER_LEN + CHUNK_OVERHEAD {
        return Err(Error::Truncated);
    }
    if stored[..4] != MAGIC || stored[4] != VERSION || stored[5] != SUITE_XCHACHA20_POLY1305 {
        return Err(Error::Header);
    }
    Ok(stored[6..HEADER_LEN].try_into().unwrap())
}

pub fn seal(folder: &FolderKey, plaintext: &[u8]) -> Result<Vec<u8>> {
    let key = folder.file_key(&new_file_id()?)?;
    let mut nonces = vec![[0u8; NONCE_LEN]; chunk_count(plaintext.len() as u64) as usize];
    for nonce in nonces.iter_mut() {
        getrandom::getrandom(nonce).map_err(|_| Error::Random)?;
    }
    seal_with(&key, plaintext, &nonces)
}

pub fn seal_with(key: &FileKey, plaintext: &[u8], nonces: &[[u8; NONCE_LEN]]) -> Result<Vec<u8>> {
    let count = chunk_count(plaintext.len() as u64) as usize;
    if nonces.len() != count {
        return Err(Error::KeyLength);
    }
    let mut out = Vec::with_capacity(stored_len(plaintext.len() as u64) as usize);
    out.extend_from_slice(key.header());
    for (index, nonce) in nonces.iter().enumerate() {
        let start = index * CHUNK_PLAINTEXT;
        let end = plaintext.len().min(start + CHUNK_PLAINTEXT);
        let last = index + 1 == count;
        out.extend_from_slice(&key.seal_chunk(
            index as u64,
            last,
            nonce,
            &plaintext[start..end],
        )?);
    }
    Ok(out)
}

pub fn open(folder: &FolderKey, stored: &[u8]) -> Result<Vec<u8>> {
    let key = folder.file_key(&parse_header(stored)?)?;
    let length = plaintext_len(stored.len() as u64)?;
    let count = chunk_count(length) as usize;
    let mut out = Vec::with_capacity(length as usize);
    for index in 0..count {
        let start = chunk_offset(index as u64) as usize;
        let end = stored.len().min(start + CHUNK_STORED);
        out.extend_from_slice(&key.open_chunk(
            index as u64,
            index + 1 == count,
            &stored[start..end],
        )?);
    }
    Ok(out)
}

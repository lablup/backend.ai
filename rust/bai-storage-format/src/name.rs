use base64::engine::general_purpose::URL_SAFE_NO_PAD;
use base64::Engine;
use chacha20::cipher::{KeyIvInit, StreamCipher};
use chacha20::XChaCha20;
use hmac::digest::KeyInit;
use hmac::{Hmac, Mac};
use sha2::{Digest, Sha256};
use subtle::ConstantTimeEq;

use crate::error::{Error, Result};
use crate::key::FolderKey;

pub const DIR_IV_LEN: usize = 16;
pub const DIR_IV_FILE: &str = ".bai.diriv";
pub const SIV_LEN: usize = 16;
pub const MAX_ON_DISK: usize = 255;
pub const LONG_PREFIX: &str = "bai.L.";
pub const LONG_SUFFIX: &str = ".n";

pub struct EncryptedName {
    pub on_disk: String,
    pub encoded: String,
    pub sidecar: Option<(String, String)>,
}

pub fn new_dir_iv() -> Result<[u8; DIR_IV_LEN]> {
    let mut iv = [0u8; DIR_IV_LEN];
    getrandom::getrandom(&mut iv).map_err(|_| Error::Random)?;
    Ok(iv)
}

fn usable(name: &str) -> bool {
    !name.is_empty()
        && name != "."
        && name != ".."
        && !name.contains('/')
        && !name.contains('\0')
        && name != DIR_IV_FILE
}

fn siv(folder: &FolderKey, dir_iv: &[u8; DIR_IV_LEN], name: &[u8]) -> [u8; SIV_LEN] {
    let mut mac = <Hmac<Sha256> as KeyInit>::new_from_slice(folder.name_auth_key()).unwrap();
    mac.update(dir_iv);
    mac.update(name);
    mac.finalize().into_bytes()[..SIV_LEN].try_into().unwrap()
}

fn keystream(folder: &FolderKey, siv: &[u8; SIV_LEN], buffer: &mut [u8]) {
    let mut nonce = [0u8; 24];
    nonce[..SIV_LEN].copy_from_slice(siv);
    let mut cipher = XChaCha20::new_from_slices(folder.name_cipher_key(), &nonce).unwrap();
    cipher.apply_keystream(buffer);
}

fn long_stub(encoded: &str) -> String {
    let digest = Sha256::digest(encoded.as_bytes());
    format!("{}{}", LONG_PREFIX, URL_SAFE_NO_PAD.encode(digest))
}

pub fn encrypt(folder: &FolderKey, dir_iv: &[u8; DIR_IV_LEN], name: &str) -> Result<EncryptedName> {
    if !usable(name) {
        return Err(Error::NameSyntax);
    }
    let siv = siv(folder, dir_iv, name.as_bytes());
    let mut body = name.as_bytes().to_vec();
    keystream(folder, &siv, &mut body);
    let mut sealed = siv.to_vec();
    sealed.extend_from_slice(&body);
    let encoded = URL_SAFE_NO_PAD.encode(&sealed);
    if encoded.len() <= MAX_ON_DISK {
        return Ok(EncryptedName {
            on_disk: encoded.clone(),
            encoded,
            sidecar: None,
        });
    }
    let on_disk = long_stub(&encoded);
    let sidecar = Some((format!("{on_disk}{LONG_SUFFIX}"), encoded.clone()));
    Ok(EncryptedName {
        on_disk,
        encoded,
        sidecar,
    })
}

pub fn decrypt(folder: &FolderKey, dir_iv: &[u8; DIR_IV_LEN], encoded: &str) -> Result<String> {
    let sealed = URL_SAFE_NO_PAD
        .decode(encoded)
        .map_err(|_| Error::NameEncoding)?;
    if sealed.len() < SIV_LEN {
        return Err(Error::NameEncoding);
    }
    let claimed: [u8; SIV_LEN] = sealed[..SIV_LEN].try_into().unwrap();
    let mut body = sealed[SIV_LEN..].to_vec();
    keystream(folder, &claimed, &mut body);
    if !bool::from(siv(folder, dir_iv, &body).ct_eq(&claimed)) {
        return Err(Error::Authentication);
    }
    let name = String::from_utf8(body).map_err(|_| Error::NameEncoding)?;
    if !usable(&name) {
        return Err(Error::NameSyntax);
    }
    Ok(name)
}

pub fn sidecar_of(on_disk: &str) -> Option<String> {
    on_disk
        .starts_with(LONG_PREFIX)
        .then(|| format!("{on_disk}{LONG_SUFFIX}"))
}

pub fn is_reserved(on_disk: &str) -> bool {
    on_disk == DIR_IV_FILE || (on_disk.starts_with(LONG_PREFIX) && on_disk.ends_with(LONG_SUFFIX))
}

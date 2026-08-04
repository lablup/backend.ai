use core::fmt;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Error {
    KeyLength,
    Header,
    Truncated,
    ChunkSize,
    Authentication,
    NameSyntax,
    NameEncoding,
    Random,
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let text = match self {
            Error::KeyLength => "key or nonce has the wrong length",
            Error::Header => "not a backend.ai confidential storage file",
            Error::Truncated => "ciphertext length is not a whole number of frames",
            Error::ChunkSize => "chunk plaintext length is not permitted at this index",
            Error::Authentication => "authentication failed",
            Error::NameSyntax => "name is not a usable path component",
            Error::NameEncoding => "encoded name is malformed",
            Error::Random => "the platform random source failed",
        };
        f.write_str(text)
    }
}

impl std::error::Error for Error {}

pub type Result<T> = core::result::Result<T, Error>;

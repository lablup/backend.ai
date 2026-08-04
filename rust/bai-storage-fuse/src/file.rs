use std::fs::{File, OpenOptions};
use std::io;
use std::os::unix::fs::FileExt;
use std::path::Path;

use bai_storage_format::{
    chunk_count, chunk_offset, new_file_id, parse_header, plaintext_len, stored_len, FileKey,
    FolderKey, CHUNK_OVERHEAD, CHUNK_PLAINTEXT, CHUNK_STORED, HEADER_LEN,
};

pub const CHUNK: u64 = CHUNK_PLAINTEXT as u64;

pub fn err(code: i32) -> io::Error {
    io::Error::from_raw_os_error(code)
}

pub struct CryptFile {
    file: File,
    key: FileKey,
}

impl CryptFile {
    pub fn open(path: &Path, folder: &FolderKey, write: bool) -> io::Result<Self> {
        let file = OpenOptions::new().read(true).write(write).open(path)?;
        let mut head = [0u8; HEADER_LEN + CHUNK_OVERHEAD];
        file.read_exact_at(&mut head, 0)?;
        let id = parse_header(&head).map_err(|_| err(libc::EIO))?;
        let key = folder.file_key(&id).map_err(|_| err(libc::EIO))?;
        Ok(Self { file, key })
    }

    pub fn create(path: &Path, folder: &FolderKey) -> io::Result<Self> {
        let file = OpenOptions::new()
            .read(true)
            .write(true)
            .create_new(true)
            .open(path)?;
        let id = new_file_id().map_err(|_| err(libc::EIO))?;
        let key = folder.file_key(&id).map_err(|_| err(libc::EIO))?;
        file.write_all_at(key.header(), 0)?;
        let made = Self { file, key };
        made.put(0, true, &[])?;
        Ok(made)
    }

    fn stored(&self) -> io::Result<u64> {
        Ok(self.file.metadata()?.len())
    }

    fn plain(&self) -> io::Result<(u64, u64)> {
        let stored = self.stored()?;
        Ok((stored, plaintext_len(stored).map_err(|_| err(libc::EIO))?))
    }

    fn get(&self, index: u64, last: bool, stored: u64) -> io::Result<Vec<u8>> {
        let start = chunk_offset(index);
        let mut frame = vec![0u8; stored.saturating_sub(start).min(CHUNK_STORED as u64) as usize];
        self.file.read_exact_at(&mut frame, start)?;
        self.key
            .open_chunk(index, last, &frame)
            .map_err(|_| err(libc::EIO))
    }

    fn put(&self, index: u64, last: bool, chunk: &[u8]) -> io::Result<()> {
        let frame = self
            .key
            .seal_chunk_random(index, last, chunk)
            .map_err(|_| err(libc::EIO))?;
        self.file.write_all_at(&frame, chunk_offset(index))
    }

    pub fn read(&self, offset: u64, size: usize) -> io::Result<Vec<u8>> {
        let (stored, len) = self.plain()?;
        if offset >= len || size == 0 {
            return Ok(Vec::new());
        }
        let end = (offset + size as u64).min(len);
        let count = chunk_count(len);
        let mut out = Vec::with_capacity((end - offset) as usize);
        for index in offset / CHUNK..=(end - 1) / CHUNK {
            let chunk = self.get(index, index + 1 == count, stored)?;
            let base = index * CHUNK;
            let from = offset.saturating_sub(base) as usize;
            let to = ((end - base).min(CHUNK) as usize).min(chunk.len());
            out.extend_from_slice(&chunk[from.min(to)..to]);
        }
        Ok(out)
    }

    pub fn write(&self, offset: u64, data: &[u8]) -> io::Result<()> {
        if data.is_empty() {
            return Ok(());
        }
        let (stored, len) = self.plain()?;
        self.rewrite(
            stored,
            len,
            len.max(offset + data.len() as u64),
            offset,
            data,
        )
    }

    pub fn truncate(&self, wanted: u64) -> io::Result<()> {
        let (stored, len) = self.plain()?;
        if wanted == len {
            return Ok(());
        }
        if wanted > len {
            return self.rewrite(stored, len, wanted, len, &[]);
        }
        let count = chunk_count(len);
        let index = chunk_count(wanted) - 1;
        let kept = (wanted - index * CHUNK) as usize;
        let chunk = self.get(index, index + 1 == count, stored)?;
        self.put(index, true, &chunk[..kept])?;
        self.file.set_len(stored_len(wanted))
    }

    fn rewrite(
        &self,
        stored: u64,
        len: u64,
        wanted: u64,
        offset: u64,
        data: &[u8],
    ) -> io::Result<()> {
        let held = chunk_count(len);
        let count = chunk_count(wanted);
        let first = (offset / CHUNK).min(held - 1);
        let last = if wanted > len {
            count - 1
        } else {
            (offset + data.len() as u64 - 1) / CHUNK
        };
        for index in first..=last {
            let base = index * CHUNK;
            let width = (wanted - base).min(CHUNK) as usize;
            let mut chunk = vec![0u8; width];
            if index < held {
                let previous = self.get(index, index + 1 == held, stored)?;
                let carried = previous.len().min(width);
                chunk[..carried].copy_from_slice(&previous[..carried]);
            }
            let touched = base + width as u64;
            if offset < touched && base < offset + data.len() as u64 {
                let from = offset.max(base);
                let to = (offset + data.len() as u64).min(touched);
                chunk[(from - base) as usize..(to - base) as usize]
                    .copy_from_slice(&data[(from - offset) as usize..(to - offset) as usize]);
            }
            self.put(index, index + 1 == count, &chunk)?;
        }
        Ok(())
    }
}

use std::collections::HashMap;
use std::ffi::{CString, OsStr};
use std::fs::{self, Metadata, Permissions};
use std::io;
use std::os::unix::ffi::OsStrExt;
use std::os::unix::fs::{chown, MetadataExt, PermissionsExt};
use std::path::{Path, PathBuf};
use std::sync::Mutex;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use bai_storage_format::{
    decrypt_name, encrypt_name, is_reserved, new_dir_iv, plaintext_len, sidecar_of, EncryptedName,
    FolderKey, DIR_IV_FILE, DIR_IV_LEN,
};
use fuser::{
    BsdFileFlags, FileAttr, FileHandle, FileType, Filesystem, FopenFlags, Generation, INodeNo,
    InitFlags, KernelConfig, OpenFlags, RenameFlags, ReplyAttr, ReplyCreate, ReplyData,
    ReplyDirectory, ReplyEmpty, ReplyEntry, ReplyOpen, ReplyStatfs, ReplyWrite, Request, TimeOrNow,
    WriteFlags,
};

use crate::file::{err, CryptFile, CHUNK};

const TTL: Duration = Duration::from_secs(1);
const ROOT: u64 = 1;

#[derive(Default)]
struct State {
    paths: HashMap<u64, PathBuf>,
    inodes: HashMap<PathBuf, u64>,
    ivs: HashMap<PathBuf, [u8; DIR_IV_LEN]>,
    open: HashMap<u64, CryptFile>,
    next_ino: u64,
    next_fh: u64,
}

pub struct Fs {
    root: PathBuf,
    folder: FolderKey,
    read_only: bool,
    state: Mutex<State>,
}

fn stamp(seconds: i64) -> SystemTime {
    UNIX_EPOCH + Duration::from_secs(seconds.max(0) as u64)
}

impl Fs {
    pub fn new(cipher: &Path, key: &[u8], read_only: bool) -> io::Result<Self> {
        let mut state = State {
            next_ino: ROOT + 1,
            next_fh: 1,
            ..State::default()
        };
        state.paths.insert(ROOT, PathBuf::new());
        state.inodes.insert(PathBuf::new(), ROOT);
        let mounted = Self {
            root: cipher.canonicalize()?,
            folder: FolderKey::from_slice(key).map_err(|_| err(libc::EINVAL))?,
            read_only,
            state: Mutex::new(state),
        };
        {
            let mut state = mounted.state.lock().unwrap();
            mounted.dir_iv(&mut state, Path::new(""))?;
        }
        Ok(mounted)
    }

    fn writable(&self) -> io::Result<()> {
        if self.read_only {
            return Err(err(libc::EROFS));
        }
        Ok(())
    }

    fn at(&self, rel: &Path) -> PathBuf {
        self.root.join(rel)
    }

    fn rel(&self, state: &State, ino: INodeNo) -> io::Result<PathBuf> {
        state
            .paths
            .get(&ino.0)
            .cloned()
            .ok_or_else(|| err(libc::ENOENT))
    }

    fn intern(&self, state: &mut State, rel: PathBuf) -> u64 {
        if let Some(known) = state.inodes.get(&rel) {
            return *known;
        }
        let ino = state.next_ino;
        state.next_ino += 1;
        state.inodes.insert(rel.clone(), ino);
        state.paths.insert(ino, rel);
        ino
    }

    fn dir_iv(&self, state: &mut State, dir: &Path) -> io::Result<[u8; DIR_IV_LEN]> {
        if let Some(known) = state.ivs.get(dir) {
            return Ok(*known);
        }
        let marker = self.at(dir).join(DIR_IV_FILE);
        let iv = match fs::read(&marker) {
            Ok(bytes) => {
                <[u8; DIR_IV_LEN]>::try_from(bytes.as_slice()).map_err(|_| err(libc::EIO))?
            }
            Err(missing) if missing.kind() == io::ErrorKind::NotFound && !self.read_only => {
                let fresh = new_dir_iv().map_err(|_| err(libc::EIO))?;
                fs::write(&marker, fresh)?;
                fresh
            }
            Err(other) => return Err(other),
        };
        state.ivs.insert(dir.to_path_buf(), iv);
        Ok(iv)
    }

    fn seal(&self, state: &mut State, dir: &Path, name: &OsStr) -> io::Result<EncryptedName> {
        let iv = self.dir_iv(state, dir)?;
        let plain = name.to_str().ok_or_else(|| err(libc::EINVAL))?;
        encrypt_name(&self.folder, &iv, plain).map_err(|_| err(libc::EINVAL))
    }

    fn sidecar(&self, dir: &Path, sealed: &EncryptedName) -> io::Result<()> {
        if let Some((name, encoded)) = &sealed.sidecar {
            fs::write(self.at(dir).join(name), encoded)?;
        }
        Ok(())
    }

    fn drop_sidecar(&self, dir: &Path, sealed: &EncryptedName) {
        if let Some((name, _)) = &sealed.sidecar {
            let _ = fs::remove_file(self.at(dir).join(name));
        }
    }

    fn attr(&self, ino: u64, meta: &Metadata) -> io::Result<FileAttr> {
        let kind = FileType::from_std(meta.file_type()).ok_or_else(|| err(libc::EIO))?;
        let size = if kind == FileType::RegularFile {
            plaintext_len(meta.len()).map_err(|_| err(libc::EIO))?
        } else {
            meta.len()
        };
        Ok(FileAttr {
            ino: INodeNo(ino),
            size,
            blocks: size.div_ceil(512),
            atime: stamp(meta.atime()),
            mtime: stamp(meta.mtime()),
            ctime: stamp(meta.ctime()),
            crtime: UNIX_EPOCH,
            kind,
            perm: (meta.mode() & 0o7777) as u16,
            nlink: meta.nlink() as u32,
            uid: meta.uid(),
            gid: meta.gid(),
            rdev: meta.rdev() as u32,
            blksize: CHUNK as u32,
            flags: 0,
        })
    }

    fn forget_tree(&self, state: &mut State, rel: &Path) {
        let gone: Vec<PathBuf> = state
            .inodes
            .keys()
            .filter(|held| held.starts_with(rel))
            .cloned()
            .collect();
        for path in gone {
            if let Some(ino) = state.inodes.remove(&path) {
                state.paths.remove(&ino);
            }
            state.ivs.remove(&path);
        }
    }

    fn repath(&self, state: &mut State, old: &Path, new: &Path) {
        let moved: Vec<PathBuf> = state
            .inodes
            .keys()
            .filter(|held| held.starts_with(old))
            .cloned()
            .collect();
        for path in moved {
            let rest = path.strip_prefix(old).unwrap();
            let fresh = if rest.as_os_str().is_empty() {
                new.to_path_buf()
            } else {
                new.join(rest)
            };
            if let Some(ino) = state.inodes.remove(&path) {
                state.inodes.insert(fresh.clone(), ino);
                state.paths.insert(ino, fresh.clone());
            }
            if let Some(iv) = state.ivs.remove(&path) {
                state.ivs.insert(fresh, iv);
            }
        }
    }

    fn do_lookup(&self, parent: INodeNo, name: &OsStr) -> io::Result<FileAttr> {
        let mut state = self.state.lock().unwrap();
        let dir = self.rel(&state, parent)?;
        let sealed = self.seal(&mut state, &dir, name)?;
        let rel = dir.join(&sealed.on_disk);
        let meta = fs::symlink_metadata(self.at(&rel))?;
        let ino = self.intern(&mut state, rel);
        self.attr(ino, &meta)
    }

    fn do_getattr(&self, ino: INodeNo) -> io::Result<FileAttr> {
        let state = self.state.lock().unwrap();
        let rel = self.rel(&state, ino)?;
        self.attr(ino.0, &fs::symlink_metadata(self.at(&rel))?)
    }

    fn do_setattr(
        &self,
        ino: INodeNo,
        mode: Option<u32>,
        owner: (Option<u32>, Option<u32>),
        size: Option<u64>,
    ) -> io::Result<FileAttr> {
        let rel = {
            let state = self.state.lock().unwrap();
            self.rel(&state, ino)?
        };
        let path = self.at(&rel);
        if mode.is_some() || size.is_some() || owner.0.is_some() || owner.1.is_some() {
            self.writable()?;
        }
        if let Some(bits) = mode {
            fs::set_permissions(&path, Permissions::from_mode(bits & 0o7777))?;
        }
        if owner.0.is_some() || owner.1.is_some() {
            chown(&path, owner.0, owner.1)?;
        }
        if let Some(wanted) = size {
            CryptFile::open(&path, &self.folder, true)?.truncate(wanted)?;
        }
        self.attr(ino.0, &fs::symlink_metadata(&path)?)
    }

    fn listing(&self, ino: INodeNo) -> io::Result<Vec<(u64, FileType, String)>> {
        let mut state = self.state.lock().unwrap();
        let dir = self.rel(&state, ino)?;
        let iv = self.dir_iv(&mut state, &dir)?;
        let parent = match dir.parent() {
            Some(above) => self.intern(&mut state, above.to_path_buf()),
            None => ino.0,
        };
        let mut listing = vec![
            (ino.0, FileType::Directory, ".".to_owned()),
            (parent, FileType::Directory, "..".to_owned()),
        ];
        for entry in fs::read_dir(self.at(&dir))? {
            let entry = entry?;
            let Ok(on_disk) = entry.file_name().into_string() else {
                continue;
            };
            if is_reserved(&on_disk) {
                continue;
            }
            let encoded = match sidecar_of(&on_disk) {
                Some(name) => fs::read_to_string(self.at(&dir).join(name))?,
                None => on_disk.clone(),
            };
            let Ok(plain) = decrypt_name(&self.folder, &iv, encoded.trim()) else {
                continue;
            };
            let Some(kind) = FileType::from_std(entry.file_type()?) else {
                continue;
            };
            let child = self.intern(&mut state, dir.join(&on_disk));
            listing.push((child, kind, plain));
        }
        Ok(listing)
    }

    fn hold(&self, state: &mut State, handle: CryptFile) -> u64 {
        let fh = state.next_fh;
        state.next_fh += 1;
        state.open.insert(fh, handle);
        fh
    }

    fn do_open(&self, ino: INodeNo) -> io::Result<u64> {
        let mut state = self.state.lock().unwrap();
        let rel = self.rel(&state, ino)?;
        let handle = CryptFile::open(&self.at(&rel), &self.folder, !self.read_only)?;
        Ok(self.hold(&mut state, handle))
    }

    fn do_read(&self, fh: FileHandle, offset: u64, size: u32) -> io::Result<Vec<u8>> {
        let state = self.state.lock().unwrap();
        let handle = state.open.get(&fh.0).ok_or_else(|| err(libc::EBADF))?;
        handle.read(offset, size as usize)
    }

    fn do_write(&self, fh: FileHandle, offset: u64, data: &[u8]) -> io::Result<u32> {
        self.writable()?;
        let state = self.state.lock().unwrap();
        let handle = state.open.get(&fh.0).ok_or_else(|| err(libc::EBADF))?;
        handle.write(offset, data)?;
        Ok(data.len() as u32)
    }

    fn do_create(
        &self,
        parent: INodeNo,
        name: &OsStr,
        mode: u32,
        owner: (u32, u32),
    ) -> io::Result<(FileAttr, u64)> {
        self.writable()?;
        let mut state = self.state.lock().unwrap();
        let dir = self.rel(&state, parent)?;
        let sealed = self.seal(&mut state, &dir, name)?;
        let rel = dir.join(&sealed.on_disk);
        let handle = CryptFile::create(&self.at(&rel), &self.folder)?;
        self.sidecar(&dir, &sealed)?;
        fs::set_permissions(self.at(&rel), Permissions::from_mode(mode & 0o7777))?;
        chown(self.at(&rel), Some(owner.0), Some(owner.1))?;
        let meta = fs::symlink_metadata(self.at(&rel))?;
        let ino = self.intern(&mut state, rel);
        Ok((self.attr(ino, &meta)?, self.hold(&mut state, handle)))
    }

    fn do_mkdir(
        &self,
        parent: INodeNo,
        name: &OsStr,
        mode: u32,
        owner: (u32, u32),
    ) -> io::Result<FileAttr> {
        self.writable()?;
        let mut state = self.state.lock().unwrap();
        let dir = self.rel(&state, parent)?;
        let sealed = self.seal(&mut state, &dir, name)?;
        let rel = dir.join(&sealed.on_disk);
        fs::create_dir(self.at(&rel))?;
        self.sidecar(&dir, &sealed)?;
        self.dir_iv(&mut state, &rel)?;
        fs::set_permissions(self.at(&rel), Permissions::from_mode(mode & 0o7777))?;
        chown(self.at(&rel), Some(owner.0), Some(owner.1))?;
        let meta = fs::symlink_metadata(self.at(&rel))?;
        let ino = self.intern(&mut state, rel);
        self.attr(ino, &meta)
    }

    fn do_unlink(&self, parent: INodeNo, name: &OsStr) -> io::Result<()> {
        self.writable()?;
        let mut state = self.state.lock().unwrap();
        let dir = self.rel(&state, parent)?;
        let sealed = self.seal(&mut state, &dir, name)?;
        let rel = dir.join(&sealed.on_disk);
        fs::remove_file(self.at(&rel))?;
        self.drop_sidecar(&dir, &sealed);
        self.forget_tree(&mut state, &rel);
        Ok(())
    }

    fn do_rmdir(&self, parent: INodeNo, name: &OsStr) -> io::Result<()> {
        self.writable()?;
        let mut state = self.state.lock().unwrap();
        let dir = self.rel(&state, parent)?;
        let sealed = self.seal(&mut state, &dir, name)?;
        let rel = dir.join(&sealed.on_disk);
        for entry in fs::read_dir(self.at(&rel))? {
            if entry?.file_name() != OsStr::new(DIR_IV_FILE) {
                return Err(err(libc::ENOTEMPTY));
            }
        }
        let _ = fs::remove_file(self.at(&rel).join(DIR_IV_FILE));
        fs::remove_dir(self.at(&rel))?;
        self.drop_sidecar(&dir, &sealed);
        self.forget_tree(&mut state, &rel);
        Ok(())
    }

    fn do_rename(
        &self,
        parent: INodeNo,
        name: &OsStr,
        newparent: INodeNo,
        newname: &OsStr,
    ) -> io::Result<()> {
        self.writable()?;
        let mut state = self.state.lock().unwrap();
        let from_dir = self.rel(&state, parent)?;
        let into_dir = self.rel(&state, newparent)?;
        let from = self.seal(&mut state, &from_dir, name)?;
        let into = self.seal(&mut state, &into_dir, newname)?;
        let old = from_dir.join(&from.on_disk);
        let new = into_dir.join(&into.on_disk);
        self.sidecar(&into_dir, &into)?;
        fs::rename(self.at(&old), self.at(&new))?;
        self.drop_sidecar(&from_dir, &from);
        self.forget_tree(&mut state, &new);
        self.repath(&mut state, &old, &new);
        Ok(())
    }

    fn do_statfs(&self) -> io::Result<libc::statvfs> {
        let path = CString::new(self.root.as_os_str().as_bytes()).map_err(|_| err(libc::EINVAL))?;
        let mut found: libc::statvfs = unsafe { std::mem::zeroed() };
        if unsafe { libc::statvfs(path.as_ptr(), &mut found) } != 0 {
            return Err(io::Error::last_os_error());
        }
        Ok(found)
    }
}

impl Filesystem for Fs {
    fn init(&mut self, _req: &Request, config: &mut KernelConfig) -> io::Result<()> {
        let _ = config.add_capabilities(InitFlags::FUSE_WRITEBACK_CACHE);
        let _ = config.set_max_write(CHUNK as u32);
        let _ = config.set_max_readahead(CHUNK as u32);
        Ok(())
    }

    fn lookup(&self, _req: &Request, parent: INodeNo, name: &OsStr, reply: ReplyEntry) {
        match self.do_lookup(parent, name) {
            Ok(attr) => reply.entry(&TTL, &attr, Generation(0)),
            Err(failure) => reply.error(failure.into()),
        }
    }

    fn getattr(&self, _req: &Request, ino: INodeNo, _fh: Option<FileHandle>, reply: ReplyAttr) {
        match self.do_getattr(ino) {
            Ok(attr) => reply.attr(&TTL, &attr),
            Err(failure) => reply.error(failure.into()),
        }
    }

    fn setattr(
        &self,
        _req: &Request,
        ino: INodeNo,
        mode: Option<u32>,
        uid: Option<u32>,
        gid: Option<u32>,
        size: Option<u64>,
        _atime: Option<TimeOrNow>,
        _mtime: Option<TimeOrNow>,
        _ctime: Option<SystemTime>,
        _fh: Option<FileHandle>,
        _crtime: Option<SystemTime>,
        _chgtime: Option<SystemTime>,
        _bkuptime: Option<SystemTime>,
        _flags: Option<BsdFileFlags>,
        reply: ReplyAttr,
    ) {
        match self.do_setattr(ino, mode, (uid, gid), size) {
            Ok(attr) => reply.attr(&TTL, &attr),
            Err(failure) => reply.error(failure.into()),
        }
    }

    fn mkdir(
        &self,
        req: &Request,
        parent: INodeNo,
        name: &OsStr,
        mode: u32,
        umask: u32,
        reply: ReplyEntry,
    ) {
        match self.do_mkdir(parent, name, mode & !umask, (req.uid(), req.gid())) {
            Ok(attr) => reply.entry(&TTL, &attr, Generation(0)),
            Err(failure) => reply.error(failure.into()),
        }
    }

    fn unlink(&self, _req: &Request, parent: INodeNo, name: &OsStr, reply: ReplyEmpty) {
        match self.do_unlink(parent, name) {
            Ok(()) => reply.ok(),
            Err(failure) => reply.error(failure.into()),
        }
    }

    fn rmdir(&self, _req: &Request, parent: INodeNo, name: &OsStr, reply: ReplyEmpty) {
        match self.do_rmdir(parent, name) {
            Ok(()) => reply.ok(),
            Err(failure) => reply.error(failure.into()),
        }
    }

    fn rename(
        &self,
        _req: &Request,
        parent: INodeNo,
        name: &OsStr,
        newparent: INodeNo,
        newname: &OsStr,
        _flags: RenameFlags,
        reply: ReplyEmpty,
    ) {
        match self.do_rename(parent, name, newparent, newname) {
            Ok(()) => reply.ok(),
            Err(failure) => reply.error(failure.into()),
        }
    }

    fn open(&self, _req: &Request, ino: INodeNo, _flags: OpenFlags, reply: ReplyOpen) {
        match self.do_open(ino) {
            Ok(fh) => reply.opened(FileHandle(fh), FopenFlags::empty()),
            Err(failure) => reply.error(failure.into()),
        }
    }

    fn read(
        &self,
        _req: &Request,
        _ino: INodeNo,
        fh: FileHandle,
        offset: u64,
        size: u32,
        _flags: OpenFlags,
        _lock_owner: Option<fuser::LockOwner>,
        reply: ReplyData,
    ) {
        match self.do_read(fh, offset, size) {
            Ok(data) => reply.data(&data),
            Err(failure) => reply.error(failure.into()),
        }
    }

    fn write(
        &self,
        _req: &Request,
        _ino: INodeNo,
        fh: FileHandle,
        offset: u64,
        data: &[u8],
        _write_flags: WriteFlags,
        _flags: OpenFlags,
        _lock_owner: Option<fuser::LockOwner>,
        reply: ReplyWrite,
    ) {
        match self.do_write(fh, offset, data) {
            Ok(written) => reply.written(written),
            Err(failure) => reply.error(failure.into()),
        }
    }

    fn flush(
        &self,
        _req: &Request,
        _ino: INodeNo,
        _fh: FileHandle,
        _lock_owner: fuser::LockOwner,
        reply: ReplyEmpty,
    ) {
        reply.ok();
    }

    fn fsync(
        &self,
        _req: &Request,
        _ino: INodeNo,
        _fh: FileHandle,
        _datasync: bool,
        reply: ReplyEmpty,
    ) {
        reply.ok();
    }

    fn release(
        &self,
        _req: &Request,
        _ino: INodeNo,
        fh: FileHandle,
        _flags: OpenFlags,
        _lock_owner: Option<fuser::LockOwner>,
        _flush: bool,
        reply: ReplyEmpty,
    ) {
        self.state.lock().unwrap().open.remove(&fh.0);
        reply.ok();
    }

    fn readdir(
        &self,
        _req: &Request,
        ino: INodeNo,
        _fh: FileHandle,
        offset: u64,
        mut reply: ReplyDirectory,
    ) {
        match self.listing(ino) {
            Err(failure) => reply.error(failure.into()),
            Ok(listing) => {
                for (index, (child, kind, name)) in
                    listing.into_iter().enumerate().skip(offset as usize)
                {
                    if reply.add(INodeNo(child), index as u64 + 1, kind, name) {
                        break;
                    }
                }
                reply.ok();
            }
        }
    }

    fn statfs(&self, _req: &Request, _ino: INodeNo, reply: ReplyStatfs) {
        match self.do_statfs() {
            Ok(found) => reply.statfs(
                found.f_blocks,
                found.f_bfree,
                found.f_bavail,
                found.f_files,
                found.f_ffree,
                found.f_bsize as u32,
                255,
                found.f_frsize as u32,
            ),
            Err(failure) => reply.error(failure.into()),
        }
    }

    fn create(
        &self,
        req: &Request,
        parent: INodeNo,
        name: &OsStr,
        mode: u32,
        umask: u32,
        _flags: i32,
        reply: ReplyCreate,
    ) {
        match self.do_create(parent, name, mode & !umask, (req.uid(), req.gid())) {
            Ok((attr, fh)) => reply.created(
                &TTL,
                &attr,
                Generation(0),
                FileHandle(fh),
                FopenFlags::empty(),
            ),
            Err(failure) => reply.error(failure.into()),
        }
    }

    fn access(&self, _req: &Request, _ino: INodeNo, _mask: fuser::AccessFlags, reply: ReplyEmpty) {
        reply.ok();
    }
}

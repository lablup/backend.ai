mod file;
mod fs;

use std::fs::File;
use std::io::Read;
use std::mem::ManuallyDrop;
use std::os::fd::FromRawFd;
use std::path::PathBuf;
use std::process::exit;

use fuser::{Config, MountOption, Session, SessionACL};

fn quit(reason: &str) -> ! {
    eprintln!("bai-storage-fuse: {reason}");
    exit(2)
}

fn read_key(fd: i32) -> [u8; 32] {
    let mut raw = Vec::new();
    let mut source = ManuallyDrop::new(unsafe { File::from_raw_fd(fd) });
    if let Err(failure) = source.read_to_end(&mut raw) {
        quit(&format!("the folder key could not be read: {failure}"));
    }
    let body = raw.strip_suffix(b"\n").unwrap_or(&raw);
    if body.len() == 64 && body.iter().all(u8::is_ascii_hexdigit) {
        let mut key = [0u8; 32];
        for (index, pair) in body.chunks(2).enumerate() {
            key[index] = u8::from_str_radix(std::str::from_utf8(pair).unwrap(), 16).unwrap();
        }
        raw.fill(0);
        return key;
    }
    let key = <[u8; 32]>::try_from(body).unwrap_or_else(|_| {
        quit("the folder key is neither 32 raw bytes nor 64 hexadecimal digits")
    });
    raw.fill(0);
    key
}

fn daemonise() {
    unsafe {
        match libc::fork() {
            -1 => quit("the driver could not detach from its caller"),
            0 => {}
            _ => libc::_exit(0),
        }
        libc::setsid();
        let null = libc::open(c"/dev/null".as_ptr(), libc::O_RDWR);
        if null >= 0 {
            for fd in 0..3 {
                libc::dup2(null, fd);
            }
            if null > 2 {
                libc::close(null);
            }
        }
    }
}

fn main() {
    let mut arguments = std::env::args_os().skip(1);
    let (mut read_only, mut foreground, mut shared, mut key_fd) = (false, false, false, 0);
    let mut given: Vec<PathBuf> = Vec::new();
    while let Some(argument) = arguments.next() {
        match argument.to_str() {
            Some("-ro") => read_only = true,
            Some("-fg") => foreground = true,
            Some("-allow-other") => shared = true,
            Some("-key-fd") => {
                key_fd = arguments
                    .next()
                    .and_then(|value| value.to_str().and_then(|text| text.parse().ok()))
                    .unwrap_or_else(|| quit("-key-fd wants a file descriptor number"));
            }
            _ => given.push(PathBuf::from(argument)),
        }
    }
    if given.len() != 2 {
        quit("usage: bai-storage-fuse [-ro] [-fg] [-allow-other] [-key-fd N] <cipherdir> <mountpoint>");
    }
    let mut key = read_key(key_fd);
    let mounted = fs::Fs::new(&given[0], &key, read_only).unwrap_or_else(|failure| {
        quit(&format!(
            "{} is not a usable folder: {failure}",
            given[0].display()
        ))
    });
    key.fill(0);
    let mut options = vec![
        MountOption::FSName("bai-cc-storage".to_owned()),
        MountOption::Subtype("backend.ai/cc-storage/v1".to_owned()),
        MountOption::NoSuid,
        MountOption::NoDev,
    ];
    if read_only {
        options.push(MountOption::RO);
    }
    let mut config = Config::default();
    config.mount_options = options;
    config.acl = if shared {
        SessionACL::All
    } else {
        SessionACL::Owner
    };
    let session = Session::new(mounted, &given[1], &config).unwrap_or_else(|failure| {
        quit(&format!(
            "{} could not be mounted: {failure}",
            given[1].display()
        ))
    });
    if !foreground {
        daemonise();
    }
    if let Err(failure) = session.run() {
        quit(&format!("the driver stopped: {failure}"));
    }
}

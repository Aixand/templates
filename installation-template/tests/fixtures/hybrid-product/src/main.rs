// Exercise a real embedded interpreter without a fixture-specific Cargo dependency.
use std::{
    env,
    ffi::{c_char, c_void, CString},
    process::exit,
};

#[cfg(unix)]
unsafe fn library(path: &str) -> *mut c_void {
    #[cfg_attr(target_os = "linux", link(name = "dl"))]
    extern "C" {
        fn dlopen(path: *const c_char, flags: i32) -> *mut c_void;
    }
    let global = if cfg!(target_os = "macos") {
        0x8
    } else {
        0x100
    };
    dlopen(CString::new(path).unwrap().as_ptr(), 2 | global)
}

#[cfg(windows)]
unsafe fn library(path: &str) -> *mut c_void {
    #[link(name = "kernel32")]
    extern "system" {
        fn LoadLibraryW(path: *const u16) -> *mut c_void;
    }
    let path: Vec<u16> = path.encode_utf16().chain(Some(0)).collect();
    LoadLibraryW(path.as_ptr())
}

unsafe fn symbol(handle: *mut c_void, name: &str) -> *mut c_void {
    let name = CString::new(name).unwrap();
    #[cfg(unix)]
    {
        extern "C" {
            fn dlsym(handle: *mut c_void, name: *const c_char) -> *mut c_void;
        }
        dlsym(handle, name.as_ptr())
    }
    #[cfg(windows)]
    {
        #[link(name = "kernel32")]
        extern "system" {
            fn GetProcAddress(handle: *mut c_void, name: *const c_char) -> *mut c_void;
        }
        GetProcAddress(handle, name.as_ptr())
    }
}

fn main() {
    unsafe {
        let handle = library(&env::args().nth(1).expect("Python library argument"));
        assert!(!handle.is_null(), "Python shared library could not load");
        let init = symbol(handle, "Py_Initialize");
        let run = symbol(handle, "PyRun_SimpleString");
        let finalize = symbol(handle, "Py_FinalizeEx");
        assert!(!init.is_null() && !run.is_null() && !finalize.is_null());
        let init: unsafe extern "C" fn() = std::mem::transmute(init);
        let run: unsafe extern "C" fn(*const c_char) -> i32 = std::mem::transmute(run);
        let finalize: unsafe extern "C" fn() -> i32 = std::mem::transmute(finalize);
        init();
        let source = CString::new("from fixture_product_library import message\nassert message() == 'independent Python resource'\nprint('embedded Python verified')").unwrap();
        let result = run(source.as_ptr());
        let finished = finalize();
        exit(if result == 0 && finished == 0 { 0 } else { 1 });
    }
}

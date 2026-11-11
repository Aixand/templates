use std::{
    env, fs,
    process::{exit, Command},
};

fn main() {
    let binary = env::current_exe().unwrap();
    let worker = binary.with_file_name(if cfg!(windows) {
        "fixture-worker.exe"
    } else {
        "fixture-worker"
    });
    let result = Command::new(worker).output().unwrap();
    if !result.status.success() || result.stdout != b"worker 1.0.0\n" {
        exit(17);
    }
    let message = binary
        .parent()
        .unwrap()
        .parent()
        .unwrap()
        .join("share/message.txt");
    assert_eq!(
        fs::read_to_string(message).unwrap().trim(),
        "native resources"
    );
    println!("complete native bundle 1.0.0");
}

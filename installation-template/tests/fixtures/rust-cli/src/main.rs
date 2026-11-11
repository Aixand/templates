fn main() {
    match std::env::args().nth(1).as_deref() {
        Some("--version") => println!("fixture-rust-cli {}", env!("CARGO_PKG_VERSION")),
        Some("--self-test") => {
            let executable = std::env::current_exe().unwrap();
            let resource = executable
                .parent()
                .unwrap()
                .parent()
                .unwrap()
                .join("share/assets/greeting.txt");
            assert_eq!(
                std::fs::read_to_string(resource).unwrap(),
                "Installed resource\n"
            );
            println!("Native payload resource verified");
        }
        _ => println!("Usage: fixture-rust-cli --version | --self-test"),
    }
}

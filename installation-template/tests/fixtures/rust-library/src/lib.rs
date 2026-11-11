pub fn greet(name: &str) -> String {
    include_str!("greeting.txt").trim().replace("{name}", name)
}

#[cfg(test)]
mod tests {
    #[test]
    fn api_reads_packaged_resource() {
        assert_eq!(super::greet("世界"), "Hello, 世界!");
    }
}

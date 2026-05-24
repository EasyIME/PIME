use std::io::{self, BufRead, Write};
use std::thread;
use std::time::Duration;

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let scenario = args.get(2).map(|s| s.as_str()).unwrap_or("echo");

    if scenario == "fail-start" {
        std::process::exit(1);
    }

    let stdin = io::stdin();
    let mut stdout = io::stdout();

    for line in stdin.lock().lines() {
        let line = line.expect("Failed to read from stdin");
        
        match scenario {
            "echo" => {
                // Input format: client_id|message
                if let Some(pos) = line.find('|') {
                    let client_id = &line[..pos];
                    let message = &line[pos + 1..];
                    
                    if message.contains(r#""method":"close""#) {
                        eprintln!("Mock backend received CLOSE for client {}", client_id);
                    }

                    println!("PIME_MSG|{}|REPLY: {}", client_id, message);
                    stdout.flush().unwrap();
                }
            }
            "crash" => {
                if line.contains("CRASH_NOW") {
                    std::process::exit(1);
                }
                if let Some(pos) = line.find('|') {
                    let client_id = &line[..pos];
                    let message = &line[pos + 1..];
                    println!("PIME_MSG|{}|REPLY: {}", client_id, message);
                    stdout.flush().unwrap();
                }
            }
            "hang" => {
                if line.contains("HANG_NOW") {
                    thread::sleep(Duration::from_secs(3600));
                }
                if let Some(pos) = line.find('|') {
                    let client_id = &line[..pos];
                    let message = &line[pos + 1..];
                    println!("PIME_MSG|{}|REPLY: {}", client_id, message);
                    stdout.flush().unwrap();
                }
            }
            _ => {}
        }
    }
}

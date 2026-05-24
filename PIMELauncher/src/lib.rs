//! PIMELauncher2 Background Service
//!
//! This crate provides the core logic for the PIME background service, which acts as a
//! proxy between local clients (IME DLLs) and various language backend processes.
//! It handles named pipe communication, backend lifecycle management, and security ACLs.

pub mod acl;
pub mod backend_manager;
pub mod backend_registry;
pub mod client_session;
pub mod pipe_server;
pub mod protocol;
pub mod testing;

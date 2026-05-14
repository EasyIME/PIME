Build a rust-based, constantly running background service.
- run as current user, ensure single instance.
- restart on crash, if possible.
- work as a proxy to forward incomining connections to backend processes.
  - each connected client is assigned a unique ID (uuid), and its initial message contains information about the backend it needs.
  - upon connection, the service makes sure the required backend program is spawned and running.
  - then, it forwards all subsequent messages to the backend process via its stdin.
  - and forwards back any message from the backend process's stdout to the client via its pipe.
  - The incoming messages from the clients and the resonse from the backends may contain extra info, which needs to be stripped before forwarding.
  - Multiple clients can connect to the same backend process asynchronously, so the message needs to contain their client ID for the backend to distinguish   between them.
  - The response from the backend stdout may contain extra debug outputs, which needs to be filtered out. If a line from stdout doesn't has PIME_MSG| prefix, it's not a message from the backend and should be ignored.
  - Also monitor the backend processes.
    - If a backend crashes or is killed, restart it.
    - If a backend service hangs for more than N seconds, restart it. Can be checked by the time it received client input and the time it respond.
    - Default N is 30 seconds, configurable.
  - keep track of connected clients and their states. If the backend dies, do not disconnect client. Just silently restart backend seamlessly.

- setup a windows named pipe for other programs to communicate with this service.
  - name: \\.\pipe\<current-user>\PIME\Launcher
  - ACL:
    - allows processes run by current user to connect.
    - allow windows 8+ app containers to connect (metro apps)
    - disallow other users to connect.

- Protocol:
  - UTF-8 Plain text, line-based, terminated by \n.
  - Client request: one-line json string.
    - Prefix with "<client_id>|" and forward to backend.
  - Server response:
    - Decode raw response from backend: "PIMG_MSG|<client_id>|<reply JSON string>\n"
    - Remove the "<client_id>|" prefix and send the rest to corresponding client.

- Available backends:
  - Hard code in the code temporarily. We will implement discovery mechanism later.
  - Each backend has:
    - A name
    - A full command line with args to run
    - The main program may be python.exe or node.js so make sure you know how to spawn them properly with UTF-8 encoding for stdio redirect.

Implementation details:
- Use tokio for async i/o and pipes.
- Add comments to the security ACL setup code since it's complex and error prone.
- Make sure everything is non-blocking and async, and resources are never leaked.
- Add error logging.

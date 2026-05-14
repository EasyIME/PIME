import os
import json
import time

def main():
    username = os.environ.get("USERNAME", "pcman")
    pipe_name = fr"\\.\pipe\{username}\PIME\Launcher"
    
    print(f"Connecting to {pipe_name}...")
    try:
        # Open the named pipe for reading and writing
        f = open(pipe_name, "r+b")
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    # 1. Send the initial JSON string
    init_msg = json.dumps({"backend": "test_backend"}) + "\n"
    f.write(init_msg.encode("utf-8"))
    f.flush()
    print(f"Sent initialization: {init_msg.strip()}")
    
    # 2. Wait a moment and send a test message
    time.sleep(0.5)
    test_msg = "Hello from Python Client!\n"
    f.write(test_msg.encode("utf-8"))
    f.flush()
    print(f"Sent message: {test_msg.strip()}")
    
    # 3. Read the response
    print("Waiting for response...")
    # Read one line
    reply = f.readline()
    if reply:
        print(f"Received response: {reply.decode('utf-8').strip()}")
    else:
        print("No response received.")
        
    f.close()

if __name__ == "__main__":
    main()

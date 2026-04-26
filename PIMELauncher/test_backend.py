import sys
import json

def main():
    for line in sys.stdin:
        # Expected input format: "<client_id>|<message>"
        parts = line.strip().split('|', 1)
        if len(parts) == 2:
            client_id = parts[0]
            msg = parts[1]
            
            # Simple echo reply
            reply = {"status": "ok", "echo": msg}
            
            # Output format: "PIME_MSG|<client_id>|<reply JSON string>"
            print(f"PIME_MSG|{client_id}|{json.dumps(reply)}", flush=True)

if __name__ == "__main__":
    main()

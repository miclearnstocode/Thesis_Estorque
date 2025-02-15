import threading
import socket
import json
from database import DatabaseHandler

class Peer:
    def __init__(self, host='0.0.0.0', port=65433, max_connections=100): #maximum number of clients
        self.host = host
        self.port = port
        self.db_handler = DatabaseHandler()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)  # Increase buffer size
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)  # Increase buffer size
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(max_connections)
        self.active_connections = set()
        self.lock = threading.Lock()
    
    def start_server(self):
        """Start the server in a separate thread."""
        server_thread = threading.Thread(target=self.run_server, daemon=True)
        server_thread.start()
        print(f"🔥 High-performance server started on {self.host}:{self.port}")
    
    def run_server(self):
        try:
            print(f"✅ Server listening on {self.host}:{self.port}")
            while True:
                conn, addr = self.server_socket.accept()
                with self.lock:
                    self.active_connections.add(conn)
                print(f"Connected by {addr}")
                threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
        except Exception as e:
            print(f"Server error: {e}")
    
    def handle_client(self, conn, addr):
        """Handle incoming client requests efficiently."""
        with conn:
            try:
                while True:
                    data = conn.recv(4096).decode()  # Increase recv buffer size
                    if not data:
                        print(f"Client {addr} disconnected")
                        break
                    request = json.loads(data)
                    action = request.get("action")
                    request_data = request.get("data", {})
                    print(f"📩 Received {action} from {addr}")
                    response = self.db_handler.execute_action(action, request_data)
                    conn.sendall(json.dumps(response).encode())
            except json.JSONDecodeError:
                conn.sendall(json.dumps({"status": "error", "message": "Invalid JSON format"}).encode())
            except Exception as e:
                conn.sendall(json.dumps({"status": "error", "message": str(e)}).encode())
            finally:
                with self.lock:
                    self.active_connections.discard(conn)
                print(f"Connection with {addr} closed")
                conn.close()
    
    def send_request(self, target_host, target_port, action, data={}):
        """Send a request to another peer (acting as a client)."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)  # Increase buffer size
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)  # Increase buffer size
            try:
                client_socket.connect((target_host, target_port))
                request = json.dumps({"action": action, "data": data})
                client_socket.sendall(request.encode())
                response = client_socket.recv(4096).decode()
                print(f"🔄 Response: {response}")
                return json.loads(response)
            except Exception as e:
                print(f"❌ Client error: {e}")
                return {"status": "error", "message": str(e)}
    
    def shutdown_server(self):
        """Gracefully shutdown the server."""
        print("🔌 Shutting down server...")
        with self.lock:
            for conn in list(self.active_connections):
                conn.close()
            self.active_connections.clear()
        self.server_socket.close()

if __name__ == "__main__":
    peer = Peer()
    peer.start_server()  # Start the high-performance server
    
    # Example: Sending a request to another peer
    target_host = "127.0.0.1"
    target_port = 65433
    peer.send_request(target_host, target_port, "test_action", {"info": "Hello from peer!"})
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        with open('data.json', 'r', encoding='utf-8') as file:
                dict_data = json.load(file)
        
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        # Convert dictionary to JSON string
        json_data = json.dumps(dict_data)

        # Encode JSON string to bytes
        byte_data = json_data.encode()
        
        self.wfile.write(byte_data)

# Set the port (e.g., 8000) and create an HTTP server
port = 8001
httpd = HTTPServer(('localhost', port), SimpleHTTPRequestHandler)

print(f"Serving HTTP on port {port}...")
httpd.serve_forever()

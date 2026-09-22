#!/usr/bin/env python3
"""Servidor local para revisar el sitio antes de publicarlo en GitHub Pages.

    python3 servir.py            -> http://localhost:8000
    python3 servir.py 8080       -> http://localhost:8080

Necesario solo para la revisión local: en GitHub Pages el sitio funciona
directamente, sin este script.
"""
import http.server, socketserver, sys, os

PUERTO = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
os.chdir(os.path.dirname(os.path.abspath(__file__)))

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

with socketserver.TCPServer(('', PUERTO), Handler) as httpd:
    print(f'Sirviendo en http://localhost:{PUERTO}  (Ctrl+C para detener)')
    httpd.serve_forever()

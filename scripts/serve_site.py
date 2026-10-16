"""Preview only the exact built release on loopback, including Pages subpaths."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import mimetypes
import os
from pathlib import Path
import re
import stat
import sys
from urllib.parse import unquote, urlsplit

from build_site import ROOT, verify_release

PROJECT_PREFIX = '/Agent-bench-website'


def request_file(raw_path):
    try:
        raw = urlsplit(raw_path).path
        path = unquote(raw, errors='strict')
    except (ValueError, UnicodeError):
        return None
    if '%' in path or '\\' in path or any(ord(c) < 32 or ord(c) == 127 for c in path):
        return None
    # Encoded separators create ambiguous routing at proxies and are never needed.
    if re.search(r'%2f|%5c', raw, re.IGNORECASE):
        return None
    if path.startswith(PROJECT_PREFIX + '/'):
        path = path[len(PROJECT_PREFIX):]
    if path == '/':
        return 'index.html'
    if not path.startswith('/') or any(not part or part.startswith('.') for part in path[1:].split('/')):
        return None
    return path[1:]


def open_release_file(root, relative):
    """Open every component without following links, including during replacements."""
    directory_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        parts = relative.split('/')
        for part in parts[:-1]:
            child_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = child_fd
        file_fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd)
        handle = os.fdopen(file_fd, 'rb')
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            handle.close()
            raise OSError('Not a regular release file')
        return handle
    finally:
        os.close(directory_fd)


class PreviewHandler(BaseHTTPRequestHandler):
    server_version = 'ReleasePreview'

    def do_GET(self):
        self.serve_file(send_body=True)

    def do_HEAD(self):
        self.serve_file(send_body=False)

    def log_message(self, format, *args):
        # No request-path log: malformed requests must not echo local path probes.
        pass

    def serve_file(self, *, send_body):
        relative = request_file(self.path)
        if relative not in self.server.allowed_files:
            self.send_error(404, 'Not found')
            return
        try:
            handle = open_release_file(self.server.release_root, relative)
        except OSError:
            self.send_error(404, 'Not found')
            return
        with handle:
            size = os.fstat(handle.fileno()).st_size
            start, end, status = 0, size - 1, 200
            requested = self.headers.get('Range')
            if requested:
                match = re.fullmatch(r'bytes=(\d*)-(\d*)', requested.strip())
                try:
                    if not match or not size:
                        raise ValueError
                    first, last = match.groups()
                    if first:
                        start = int(first)
                        end = min(int(last), size - 1) if last else size - 1
                    elif last and int(last) > 0:
                        start, end = max(0, size - int(last)), size - 1
                    else:
                        raise ValueError
                    if start >= size or start > end:
                        raise ValueError
                except ValueError:
                    self.send_response(416)
                    self.send_header('Content-Range', f'bytes */{size}')
                    self.send_header('Content-Length', '0')
                    self.end_headers()
                    return
                status = 206
            length = end - start + 1
            self.send_response(status)
            self.send_header('Content-Type', mimetypes.guess_type(relative)[0] or 'application/octet-stream')
            self.send_header('Content-Length', str(length))
            self.send_header('Accept-Ranges', 'bytes')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            if status == 206:
                self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
            self.end_headers()
            if send_body:
                handle.seek(start)
                remaining = length
                try:
                    while remaining:
                        chunk = handle.read(min(64 * 1024, remaining))
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        remaining -= len(chunk)
                except (BrokenPipeError, ConnectionResetError):
                    pass


def create_server(release_root, *, port=4174):
    release_root = Path(release_root).absolute()
    if release_root.name != 'dist' or release_root.is_symlink():
        raise ValueError('Preview root must be the real dist release directory')
    allowed_files = verify_release(release_root) - {'.nojekyll'}
    server = ThreadingHTTPServer(('127.0.0.1', port), PreviewHandler)
    server.release_root = release_root
    server.allowed_files = allowed_files
    return server


def main():
    try:
        server = create_server(ROOT / 'dist')
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f'Preview failed: {error}. Run npm run build first.', file=sys.stderr)
        return 1
    print('Release preview: http://127.0.0.1:4174/ (also /Agent-bench-website/)', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

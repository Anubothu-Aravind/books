"""
api_server.py

Zero-dependency local Python HTTP server serving JSON REST API endpoints
for the Bible corpus, geography points, and cross-references.
Connects dynamically to the exported SQLite database (bible_database.db).

Usage:
    python scripts/python/api_server.py
"""

import http.server
import socketserver
import urllib.parse
import json
import sqlite3
import os
import sys

PORT = 8090

script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(os.path.dirname(script_dir))
db_path = os.path.join(base_dir, "scriptural_tradition.db")


def resolve_version_code(cursor, input_code):
    input_code = input_code.upper()
    # Try exact match on code
    cursor.execute("SELECT code FROM versions WHERE code=?", (input_code,))
    row = cursor.fetchone()
    if row:
        return row[0]
    # Try exact match on abbreviation
    cursor.execute("SELECT code FROM versions WHERE abbreviation=?", (input_code,))
    row = cursor.fetchone()
    if row:
        return row[0]
    # Try match ending with _input_code (e.g. BENGALI_IRV or GREEK_TR_EBIBLE)
    cursor.execute("SELECT code FROM versions WHERE code LIKE ?", (f"%_{input_code}",))
    rows = cursor.fetchall()
    if len(rows) == 1:
        return rows[0][0]
    elif len(rows) > 1:
        # Ambiguous match (e.g. IRV maps to BENGALI_IRV, TELUGU_IRV, etc.)
        # Default to first one or exact preference
        return rows[0][0]
    return input_code



class ApiHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # Override to suppress default logging output to stderr
        sys.stdout.write("%s - - [%s] %s\n" % (
            self.client_address[0],
            self.log_date_time_string(),
            format % args
        ))

    def send_json(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*") # Enable CORS for explorer UI
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"))

    def send_error_json(self, status, message):
        self.send_json(status, {"error": message})

    def do_OPTIONS(self):
        # Handle CORS preflight requests
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_GET(self):
        # Parse query parameters
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query_params = urllib.parse.parse_qs(parsed_url.query)

        # Serve API Explorer files if requested
        if path.startswith("/web/"):
            # Set target directory relative to base_dir
            # Example: http://localhost:8080/web/api_explorer/index.html
            super().do_GET()
            return

        # Ensure database exists
        if not os.path.exists(db_path):
            self.send_error_json(500, "Database file bible_database.db not found. Please run export_sqlite.py first.")
            return

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # --- API Endpoints ---
            
            # 1. GET /api/versions
            if path == "/api/versions":
                cursor.execute("SELECT code, name, language, year, license, checksum_hash FROM versions ORDER BY language, code")
                rows = cursor.fetchall()
                data = [
                    {
                        "code": r[0],
                        "name": r[1],
                        "language": r[2],
                        "year": r[3],
                        "license": r[4],
                        "checksum_hash": r[5]
                    } for r in rows
                ]
                self.send_json(200, data)
                
            # 2. GET /api/books
            elif path == "/api/books":
                # Get unique book names
                cursor.execute("SELECT DISTINCT book_name, testament FROM verses ORDER BY testament DESC, id ASC")
                rows = cursor.fetchall()
                data = [{"name": r[0], "testament": r[1]} for r in rows]
                self.send_json(200, data)

            # 3. GET /api/verse
            elif path == "/api/verse":
                raw_version = query_params.get("version", ["KJV"])[0].upper()
                version = resolve_version_code(cursor, raw_version)
                book = query_params.get("book", [""])[0]
                chapter_str = query_params.get("chapter", [""])[0]
                verse_str = query_params.get("verse", [""])[0]

                if not book or not chapter_str or not verse_str:
                    self.send_error_json(400, "Missing required parameters: book, chapter, and verse are required.")
                    return

                try:
                    chapter = int(chapter_str)
                    verse = int(verse_str)
                except ValueError:
                    self.send_error_json(400, "Parameters chapter and verse must be integers.")
                    return

                cursor.execute(
                    "SELECT text, label, testament FROM verses WHERE version=? AND book_name=? AND chapter=? AND verse=?",
                    (version, book, chapter, verse)
                )
                row = cursor.fetchone()
                if row:
                    self.send_json(200, {
                        "version": version,
                        "book": book,
                        "chapter": chapter,
                        "verse": verse,
                        "testament": row[2],
                        "text": row[0],
                        "label": row[1]
                    })
                else:
                    self.send_error_json(404, "Verse not found in database.")

            # 4. GET /api/chapter
            elif path == "/api/chapter":
                raw_version = query_params.get("version", ["KJV"])[0].upper()
                version = resolve_version_code(cursor, raw_version)
                book = query_params.get("book", [""])[0]
                chapter_str = query_params.get("chapter", [""])[0]

                if not book or not chapter_str:
                    self.send_error_json(400, "Missing required parameters: book and chapter are required.")
                    return

                try:
                    chapter = int(chapter_str)
                except ValueError:
                    self.send_error_json(400, "Parameter chapter must be an integer.")
                    return

                cursor.execute(
                    "SELECT verse, text, label FROM verses WHERE version=? AND book_name=? AND chapter=? ORDER BY verse ASC",
                    (version, book, chapter)
                )
                rows = cursor.fetchall()
                if rows:
                    data = {
                        "version": version,
                        "book": book,
                        "chapter": chapter,
                        "verses": [
                            {
                                "verse": r[0],
                                "text": r[1],
                                "label": r[2]
                            } for r in rows
                        ]
                    }
                    self.send_json(200, data)
                else:
                    self.send_error_json(404, "Chapter not found in database.")

            # 5. GET /api/geography/places
            elif path == "/api/geography/places":
                place_type = query_params.get("type", [""])[0]
                if place_type:
                    cursor.execute(
                        "SELECT place_id, name, type, lat, lon, wikidata_id, confidence FROM geography WHERE type=? ORDER BY name",
                        (place_type,)
                    )
                else:
                    cursor.execute(
                        "SELECT place_id, name, type, lat, lon, wikidata_id, confidence FROM geography ORDER BY name"
                    )
                rows = cursor.fetchall()
                data = [
                    {
                        "id": r[0],
                        "name": r[1],
                        "type": r[2],
                        "lat": r[3],
                        "lon": r[4],
                        "wikidata_id": r[5],
                        "confidence": r[6]
                    } for r in rows
                ]
                self.send_json(200, data)

            # 6. GET /api/geography/places/detail
            elif path == "/api/geography/place":
                place_id = query_params.get("id", [""])[0]
                if not place_id:
                    self.send_error_json(400, "Missing required parameter: id is required.")
                    return

                cursor.execute(
                    "SELECT place_id, name, type, lat, lon, wikidata_id, confidence, verses_list FROM geography WHERE place_id=?",
                    (place_id,)
                )
                row = cursor.fetchone()
                if row:
                    self.send_json(200, {
                        "id": row[0],
                        "name": row[1],
                        "type": row[2],
                        "lat": row[3],
                        "lon": row[4],
                        "wikidata_id": row[5],
                        "confidence": row[6],
                        "verses": json.loads(row[7])
                    })
                else:
                    self.send_error_json(404, "Geography place not found.")

            # 7. GET /api/cross_references
            elif path == "/api/cross_references":
                verse = query_params.get("verse", [""])[0]
                if not verse:
                    self.send_error_json(400, "Missing required parameter: verse is required (e.g. 'Genesis 1:1').")
                    return

                cursor.execute(
                    "SELECT target_verse, votes FROM cross_references WHERE source_verse=? ORDER BY votes DESC",
                    (verse,)
                )
                rows = cursor.fetchall()
                data = {
                    "source_verse": verse,
                    "cross_references": [
                        {
                            "target_verse": r[0],
                            "votes": r[1]
                        } for r in rows
                    ]
                }
                self.send_json(200, data)

            # 8. GET /api/tradition/works
            elif path == "/api/tradition/works":
                cursor.execute("""
                    SELECT id, category, title, author, date, date_confidence, language, translator, license, source, source_url, source_id 
                    FROM tradition_works ORDER BY category, title
                """)
                rows = cursor.fetchall()
                data = [
                    {
                        "id": r[0],
                        "category": r[1],
                        "title": r[2],
                        "author": r[3],
                        "date": r[4],
                        "date_confidence": r[5],
                        "language": r[6],
                        "translator": r[7],
                        "license": r[8],
                        "source": r[9],
                        "source_url": r[10],
                        "source_id": r[11]
                    } for r in rows
                ]
                self.send_json(200, data)

            # 9. GET /api/tradition/passages
            elif path == "/api/tradition/passages":
                work_id_str = query_params.get("work_id", [""])[0]
                if not work_id_str:
                    self.send_error_json(400, "Missing required parameter: work_id is required.")
                    return

                try:
                    work_id = int(work_id_str)
                except ValueError:
                    self.send_error_json(400, "Parameter work_id must be an integer.")
                    return

                cursor.execute("""
                    SELECT section_label, section_number, text 
                    FROM tradition_passages WHERE work_id=? ORDER BY section_number, id
                """, (work_id,))
                rows = cursor.fetchall()
                
                # Fetch work details for context
                cursor.execute("SELECT title, author, category FROM tradition_works WHERE id=?", (work_id,))
                work_row = cursor.fetchone()
                work_title = work_row[0] if work_row else "Unknown"
                work_author = work_row[1] if work_row else "Unknown"
                work_category = work_row[2] if work_row else "Unknown"

                data = {
                    "work_id": work_id,
                    "title": work_title,
                    "author": work_author,
                    "category": work_category,
                    "passages": [
                        {
                            "section_label": r[0],
                            "section_number": r[1],
                            "text": r[2]
                        } for r in rows
                    ]
                }
                self.send_json(200, data)

            # 10. Not Found
            else:
                self.send_error_json(404, f"API Endpoint {path} not found.")

            conn.close()
        except Exception as e:
            self.send_error_json(500, f"Internal Server Error: {e}")


class MyTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def main():
    # Change directory to base_dir to allow serving explorer front-end relative paths
    os.chdir(base_dir)

    print("Starting local REST API server...")
    print(f"Serving endpoints from base: {base_dir}")
    try:
        with MyTCPServer(("", PORT), ApiHandler) as httpd:
            print(f"\n==================================================")
            print(f"   REST API Server is running successfully!")
            print(f"   Open in your browser: http://localhost:{PORT}/web/api_explorer/")
            print(f"==================================================")
            print("Press Ctrl+C to stop the server.")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping API server.")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting API server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

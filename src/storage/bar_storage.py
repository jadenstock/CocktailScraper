# src/storage/bar_storage.py

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


class BarStorage:
    def __init__(self, db_path: str = "data/bars.db"):
        """Initialize bar storage with path to SQLite database"""
        self.db_path = db_path
        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def init_db(self):
        """Initialize the database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bars (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    city TEXT NOT NULL,
                    description TEXT,
                    website TEXT,
                    menu_url TEXT,
                    raw_data TEXT,  -- Stores the full JSON from search
                    discovered_at TIMESTAMP NOT NULL,
                    last_updated TIMESTAMP NOT NULL,
                    search_query TEXT NOT NULL
                )
            """)

            # Add indices for common queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_bars_city ON bars(city)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_bars_name ON bars(name)")

    def add_bar(self, city: str, bar_data: Dict, search_query: str) -> bool:
        """
        Add a bar to storage. Returns True if new bar was added,
        False if bar already existed.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Create a unique ID from name and city
                bar_id = f"{bar_data['name']}_{city}".lower().replace(' ', '_')

                # Check if bar exists
                existing = conn.execute(
                    "SELECT id FROM bars WHERE id = ?",
                    (bar_id,)
                ).fetchone()

                if existing:
                    # Update last_updated timestamp
                    conn.execute("""
                        UPDATE bars 
                        SET last_updated = ?
                        WHERE id = ?
                    """, (datetime.now().isoformat(), bar_id))
                    return False

                # Insert new bar
                conn.execute("""
                    INSERT INTO bars (
                        id, name, city, description, website, 
                        menu_url, raw_data, discovered_at, 
                        last_updated, search_query
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    bar_id,
                    bar_data['name'],
                    city,
                    bar_data.get('description'),
                    bar_data.get('website'),
                    bar_data.get('cocktail_menu_url'),
                    json.dumps(bar_data),
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    search_query
                ))
                return True

        except sqlite3.Error as e:
            print(f"Error adding bar to storage: {e}")
            return False

    def get_bars(
            self,
            city: Optional[str] = None,
            limit: Optional[int] = None,
            include_raw: bool = False
    ) -> List[Dict]:
        """Get bars, optionally filtered by city"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                if city:
                    query = "SELECT * FROM bars WHERE city = ? ORDER BY discovered_at DESC"
                    params = (city,)
                else:
                    query = "SELECT * FROM bars ORDER BY discovered_at DESC"
                    params = ()

                if limit:
                    query += f" LIMIT {limit}"

                cursor = conn.execute(query, params)

                bars = []
                for row in cursor:
                    bar_dict = dict(row)
                    if not include_raw:
                        bar_dict.pop('raw_data', None)
                    bars.append(bar_dict)

                return bars

        except sqlite3.Error as e:
            print(f"Error retrieving bars: {e}")
            return []

    def get_bar_names(self, city: str) -> List[str]:
        """Get just the names of bars in a city"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT name FROM bars WHERE city = ?",
                    (city,)
                )
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error retrieving bar names: {e}")
            return []

    def get_stats(self) -> Dict:
        """Get statistics about the stored data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                stats = {}

                # Total bars
                stats['total_bars'] = conn.execute(
                    "SELECT COUNT(*) FROM bars"
                ).fetchone()[0]

                # Bars per city
                cursor = conn.execute("""
                    SELECT city, COUNT(*) as count 
                    FROM bars 
                    GROUP BY city
                    ORDER BY count DESC
                """)
                stats['bars_by_city'] = dict(cursor.fetchall())

                # Recent discoveries
                cursor = conn.execute("""
                    SELECT city, name, discovered_at
                    FROM bars
                    ORDER BY discovered_at DESC
                    LIMIT 5
                """)
                stats['recent_discoveries'] = [
                    {
                        'city': row[0],
                        'name': row[1],
                        'discovered_at': row[2]
                    }
                    for row in cursor.fetchall()
                ]

                return stats

        except sqlite3.Error as e:
            print(f"Error getting stats: {e}")
            return {}

    def update_menu_info(self, bar_id: str, menu_urls: List[str], menu_data: Dict) -> bool:
        """
        Update a bar's menu information

        Args:
            bar_id: Unique identifier for the bar
            menu_urls: List of discovered menu URLs
            menu_data: Full menu data including cocktails, PDFs, etc.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Store primary menu URL in menu_url column
                primary_url = menu_urls[0] if menu_urls else None

                # Update the bar record
                conn.execute("""
                    UPDATE bars 
                    SET menu_url = ?,
                        last_updated = ?,
                        raw_data = json_set(
                            COALESCE(raw_data, '{}'),
                            '$.menu_data', ?
                        )
                    WHERE id = ?
                """, (
                    primary_url,
                    datetime.now().isoformat(),
                    json.dumps(menu_data),
                    bar_id
                ))
                return True
        except sqlite3.Error as e:
            print(f"Error updating menu info: {e}")
            return False
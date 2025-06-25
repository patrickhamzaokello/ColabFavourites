import mysql.connector
import pandas as pd
from typing import Optional, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and queries for the recommendation system"""
    
    def __init__(self, settings):
        self.settings = settings
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    def get_db_connection(self):
        """Create a new database connection"""
        try:
            db = mysql.connector.connect(
                host=self.settings.db_host,
                user=self.settings.db_user,
                password=self.settings.db_password,
                database=self.settings.db_name,
                autocommit=True
            )
            return db
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def _execute_query_sync(self, query: str) -> pd.DataFrame:
        """Execute query synchronously and return DataFrame"""
        db = None
        cursor = None
        try:
            db = self.get_db_connection()
            cursor = db.cursor()
            cursor.execute(query)
            
            # Fetch column names
            columns = [col[0] for col in cursor.description]
            # Fetch all rows
            rows = cursor.fetchall()
            # Convert to DataFrame
            df = pd.DataFrame(rows, columns=columns)
            return df
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if db:
                db.close()
    
    async def execute_query(self, query: str) -> pd.DataFrame:
        """Execute query asynchronously and return DataFrame"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self._execute_query_sync, 
            query
        )
    
    async def get_song_frequency_data(self) -> pd.DataFrame:
        """Get song frequency data from database"""
        query = """
        SELECT f.userid, f.songid, f.plays 
        FROM frequency f 
        JOIN songs s ON s.id = f.songid  
        WHERE s.path <> '' AND s.available = 1
        """
        return await self.execute_query(query)
    
    async def get_song_details_data(self) -> pd.DataFrame:
        """Get song details with genre information"""
        query = """
        SELECT s.id as songid, s.title, g.name as genre 
        FROM songs s 
        JOIN genres g ON g.id = s.genre 
        WHERE s.path <> '' AND s.available = 1
        """
        return await self.execute_query(query)
    
    async def get_song_by_id(self, song_id: int) -> Optional[Dict[str, Any]]:
        """Get song details by ID"""
        query = f"""
        SELECT s.id as songid, s.title, g.name as genre, 
               s.artist, s.duration, s.path, s.created_at
        FROM songs s 
        JOIN genres g ON g.id = s.genre 
        WHERE s.id = {song_id} AND s.path <> '' AND s.available = 1
        """
        df = await self.execute_query(query)
        if df.empty:
            return None
        return df.iloc[0].to_dict()
    
    async def search_songs_by_title(self, query: str, limit: int = 10) -> pd.DataFrame:
        """Search songs by title"""
        search_query = f"""
        SELECT s.id as songid, s.title, g.name as genre, s.artist
        FROM songs s 
        JOIN genres g ON g.id = s.genre 
        WHERE s.title LIKE '%{query}%' 
        AND s.path <> '' AND s.available = 1
        LIMIT {limit}
        """
        return await self.execute_query(search_query)
    
    async def get_user_play_history(self, user_id: str) -> pd.DataFrame:
        """Get user's play history"""
        query = f"""
        SELECT f.userid, f.songid, f.plays, s.title, g.name as genre
        FROM frequency f 
        JOIN songs s ON s.id = f.songid
        JOIN genres g ON g.id = s.genre
        WHERE f.userid = '{user_id}' 
        AND s.path <> '' AND s.available = 1
        ORDER BY f.plays DESC
        """
        return await self.execute_query(query)
    
    async def health_check(self) -> str:
        """Check database connection health"""
        try:
            query = "SELECT 1 as health_check"
            df = await self.execute_query(query)
            return "healthy" if not df.empty else "unhealthy"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return f"unhealthy: {str(e)}"
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        stats = {}
        
        # Total songs
        query = "SELECT COUNT(*) as count FROM songs WHERE path <> '' AND available = 1"
        df = await self.execute_query(query)
        stats['total_songs'] = int(df.iloc[0]['count'])
        
        # Total users
        query = "SELECT COUNT(DISTINCT userid) as count FROM frequency"
        df = await self.execute_query(query)
        stats['total_users'] = int(df.iloc[0]['count'])
        
        # Total plays
        query = "SELECT SUM(plays) as total_plays FROM frequency"
        df = await self.execute_query(query)
        stats['total_plays'] = int(df.iloc[0]['total_plays'])
        
        # Total genres
        query = "SELECT COUNT(*) as count FROM genres"
        df = await self.execute_query(query)
        stats['total_genres'] = int(df.iloc[0]['count'])
        
        return stats
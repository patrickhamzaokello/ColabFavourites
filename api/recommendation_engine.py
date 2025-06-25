import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
from scipy.sparse import csr_matrix
from fuzzywuzzy import process
from typing import List, Dict, Any, Optional, Tuple
import logging
from collections import Counter

from .database import DatabaseManager
from .models import SongInfo

logger = logging.getLogger(__name__)

class RecommendationEngine:
    """Main recommendation engine class"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.is_initialized = False
        
        # Data structures
        self.song_frequency_df = None
        self.song_details_df = None
        self.user_item_matrix = None
        self.song_genres_matrix = None
        self.cosine_sim_matrix = None
        self.svd_model = None
        self.reduced_matrix = None
        
        # Mappings
        self.user_mapper = {}
        self.song_mapper = {}
        self.user_inv_mapper = {}
        self.song_inv_mapper = {}
        self.song_titles = {}
        self.song_idx = {}
        
        # Statistics
        self.system_stats = {}
        
    async def initialize(self):
        """Initialize the recommendation engine with data from database"""
        try:
            logger.info("Initializing recommendation engine...")
            
            # Load data from database
            await self._load_data()
            
            # Create user-item matrix
            self._create_user_item_matrix()
            
            # Prepare content-based filtering
            self._prepare_content_based_filtering()
            
            # Initialize matrix factorization
            self._initialize_matrix_factorization()
            
            # Calculate system statistics
            self._calculate_system_stats()
            
            self.is_initialized = True
            logger.info("Recommendation engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize recommendation engine: {e}")
            raise
    
    async def _load_data(self):
        """Load data from database"""
        self.song_frequency_df = await self.db_manager.get_song_frequency_data()
        self.song_details_df = await self.db_manager.get_song_details_data()
        
        logger.info(f"Loaded {len(self.song_frequency_df)} frequency records")
        logger.info(f"Loaded {len(self.song_details_df)} song details")
    
    def _create_user_item_matrix(self):
        """Create sparse user-item matrix"""
        M = self.song_frequency_df['userid'].nunique()
        N = self.song_frequency_df['songid'].nunique()

        self.user_mapper = dict(zip(np.unique(self.song_frequency_df["userid"]), list(range(M))))
        self.song_mapper = dict(zip(np.unique(self.song_frequency_df["songid"]), list(range(N))))
        self.user_inv_mapper = dict(zip(list(range(M)), np.unique(self.song_frequency_df["userid"])))
        self.song_inv_mapper = dict(zip(list(range(N)), np.unique(self.song_frequency_df["songid"])))

        user_index = [self.user_mapper[i] for i in self.song_frequency_df['userid']]
        item_index = [self.song_mapper[i] for i in self.song_frequency_df['songid']]

        self.user_item_matrix = csr_matrix(
            (self.song_frequency_df["plays"], (user_index, item_index)), 
            shape=(M, N)
        )
        
        logger.info(f"Created user-item matrix: {self.user_item_matrix.shape}")
    
    def _prepare_content_based_filtering(self):
        """Prepare content-based filtering components"""
        # Create song titles mapping
        self.song_titles = dict(zip(self.song_details_df['songid'], self.song_details_df['title']))
        self.song_idx = dict(zip(self.song_details_df['title'], list(self.song_details_df.index)))
        
        # Create genre matrix
        song_details_copy = self.song_details_df.copy()
        song_details_copy['genre'] = song_details_copy['genre'].apply(lambda x: [x])
        
        genres = set(g for G in song_details_copy['genre'] for g in G)
        for g in genres:
            song_details_copy[g] = song_details_copy.genre.transform(lambda x: int(g in x))
        
        self.song_genres_matrix = song_details_copy.drop(columns=['songid', 'title', 'genre'])
        self.cosine_sim_matrix = cosine_similarity(self.song_genres_matrix, self.song_genres_matrix)
        
        logger.info(f"Created genre similarity matrix: {self.cosine_sim_matrix.shape}")
    
    def _initialize_matrix_factorization(self):
        """Initialize matrix factorization model"""
        try:
            self.svd_model = TruncatedSVD(n_components=20, n_iter=10, random_state=42)
            self.reduced_matrix = self.svd_model.fit_transform(self.user_item_matrix.T)
            logger.info(f"Matrix factorization initialized: {self.reduced_matrix.shape}")
        except Exception as e:
            logger.warning(f"Matrix factorization initialization failed: {e}")
            self.svd_model = None
            self.reduced_matrix = None
    
    def _calculate_system_stats(self):
        """Calculate system statistics"""
        n_total = self.user_item_matrix.shape[0] * self.user_item_matrix.shape[1]
        n_ratings = self.user_item_matrix.nnz
        sparsity = (n_ratings / n_total) * 100
        
        self.system_stats = {
            'total_songs': len(self.song_details_df),
            'total_users': self.song_frequency_df['userid'].nunique(),
            'total_plays': int(self.song_frequency_df['plays'].sum()),
            'total_genres': self.song_details_df['genre'].nunique(),
            'sparsity': round(sparsity, 4),
            'avg_plays_per_user': round(self.song_frequency_df.groupby('userid')['plays'].sum().mean(), 2),
            'avg_plays_per_song': round(self.song_frequency_df.groupby('songid')['plays'].sum().mean(), 2),
            'matrix_shape': self.user_item_matrix.shape
        }
    
    async def find_similar_songs(self, song_id: int, k: int = 10, metric: str = 'cosine') -> List[SongInfo]:
        """Find similar songs using collaborative filtering"""
        if not self.is_initialized:
            raise ValueError("Recommendation engine not initialized")
        
        if song_id not in self.song_mapper:
            raise ValueError(f"Song ID {song_id} not found")
        
        try:
            # Use matrix factorization if available, otherwise use original matrix
            if self.reduced_matrix is not None:
                X = self.reduced_matrix.T
            else:
                X = self.user_item_matrix.T.toarray()
            
            song_ind = self.song_mapper[song_id]
            song_vec = X[song_ind].reshape(1, -1)
            
            kNN = NearestNeighbors(n_neighbors=k+1, algorithm="brute", metric=metric)
            kNN.fit(X)
            distances, indices = kNN.kneighbors(song_vec, return_distance=True)
            
            similar_songs = []
            for i in range(1, k+1):  # Skip first result (itself)
                if i < len(indices[0]):
                    neighbor_idx = indices[0][i]
                    neighbor_song_id = self.song_inv_mapper[neighbor_idx]
                    distance = distances[0][i]
                    
                    # Convert distance to similarity score
                    if metric == 'cosine':
                        similarity = 1 - distance
                    else:
                        similarity = 1 / (1 + distance)
                    
                    song_info = await self._get_song_info(neighbor_song_id, similarity)
                    if song_info:
                        similar_songs.append(song_info)
            
            return similar_songs
            
        except Exception as e:
            logger.error(f"Error finding similar songs: {e}")
            raise
    
    async def get_content_based_recommendations(self, title_string: str, n_recommendations: int = 10) -> Dict[str, Any]:
        """Get content-based recommendations"""
        if not self.is_initialized:
            raise ValueError("Recommendation engine not initialized")
        
        try:
            # Find closest matching title
            all_titles = self.song_details_df['title'].tolist()
            closest_match = process.extractOne(title_string, all_titles)
            matched_title = closest_match[0]
            
            if matched_title not in self.song_idx:
                raise ValueError(f"Song '{matched_title}' not found in index")
            
            idx = self.song_idx[matched_title]
            sim_scores = list(enumerate(self.cosine_sim_matrix[idx]))
            sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
            sim_scores = sim_scores[1:(n_recommendations+1)]
            
            recommendations = []
            for song_idx, similarity in sim_scores:
                song_row = self.song_details_df.iloc[song_idx]
                song_info = SongInfo(
                    song_id=int(song_row['songid']),
                    title=song_row['title'],
                    genre=song_row['genre'],
                    similarity_score=float(similarity)
                )
                recommendations.append(song_info)
            
            return {
                'matched_title': matched_title,
                'songs': recommendations
            }
            
        except Exception as e:
            logger.error(f"Error getting content-based recommendations: {e}")
            raise
    
    async def get_popular_songs(self, limit: int = 10, algorithm: str = "bayesian") -> List[SongInfo]:
        """Get popular songs"""
        if not self.is_initialized:
            raise ValueError("Recommendation engine not initialized")
        
        try:
            if algorithm == "bayesian":
                return await self._get_bayesian_popular_songs(limit)
            else:
                return await self._get_frequency_popular_songs(limit)
        except Exception as e:
            logger.error(f"Error getting popular songs: {e}")
            raise
    
    async def _get_bayesian_popular_songs(self, limit: int) -> List[SongInfo]:
        """Get popular songs using Bayesian average"""
        song_stats = self.song_frequency_df.groupby('songid')['plays'].agg(['count', 'mean'])
        
        C = song_stats['count'].mean()  # Average number of plays
        m = song_stats['mean'].mean()   # Average rating
        
        def bayesian_avg(row):
            return (C * m + row['count'] * row['mean']) / (C + row['count'])
        
        song_stats['bayesian_avg'] = song_stats.apply(bayesian_avg, axis=1)
        top_songs = song_stats.sort_values('bayesian_avg', ascending=False).head(limit)
        
        popular_songs = []
        for song_id, stats in top_songs.iterrows():
            song_info = await self._get_song_info(song_id, stats['bayesian_avg'])
            if song_info:
                popular_songs.append(song_info)
        
        return popular_songs
    
    async def _get_frequency_popular_songs(self, limit: int) -> List[SongInfo]:
        """Get popular songs by frequency"""
        song_totals = self.song_frequency_df.groupby('songid')['plays'].sum().sort_values(ascending=False)
        top_songs = song_totals.head(limit)
        
        popular_songs = []
        for song_id, total_plays in top_songs.items():
            song_info = await self._get_song_info(song_id, float(total_plays))
            if song_info:
                popular_songs.append(song_info)
        
        return popular_songs
    
    async def _get_song_info(self, song_id: int, similarity_score: float = None) -> Optional[SongInfo]:
        """Get song information"""
        try:
            song_details = await self.db_manager.get_song_by_id(song_id)
            if not song_details:
                return None
            
            return SongInfo(
                song_id=song_id,
                title=song_details['title'],
                genre=song_details.get('genre'),
                artist=song_details.get('artist'),
                similarity_score=similarity_score
            )
        except Exception as e:
            logger.error(f"Error getting song info for {song_id}: {e}")
            return None
    
    async def get_song_details(self, song_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed song information"""
        return await self.db_manager.get_song_by_id(song_id)
    
    async def search_songs(self, query: str, limit: int = 10) -> List[SongInfo]:
        """Search songs by title"""
        try:
            df = await self.db_manager.search_songs_by_title(query, limit)
            results = []
            
            for _, row in df.iterrows():
                song_info = SongInfo(
                    song_id=int(row['songid']),
                    title=row['title'],
                    genre=row['genre'],
                    artist=row.get('artist')
                )
                results.append(song_info)
            
            return results
        except Exception as e:
            logger.error(f"Error searching songs: {e}")
            raise
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        if not self.is_initialized:
            # Get basic stats from database
            return await self.db_manager.get_system_stats()
        
        return self.system_stats
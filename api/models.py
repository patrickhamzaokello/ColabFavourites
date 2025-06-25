from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class MetricType(str, Enum):
    """Supported distance metrics for similarity calculations"""
    cosine = "cosine"
    euclidean = "euclidean"

class PopularityAlgorithm(str, Enum):
    """Supported popularity algorithms"""
    bayesian = "bayesian"
    frequency = "frequency"

class SongInfo(BaseModel):
    """Song information model"""
    song_id: int = Field(..., description="Unique song identifier")
    title: str = Field(..., description="Song title")
    genre: Optional[str] = Field(None, description="Song genre")
    artist: Optional[str] = Field(None, description="Song artist")
    similarity_score: Optional[float] = Field(None, description="Similarity score (0-1)")

class SimilarSongsRequest(BaseModel):
    """Request model for similar songs recommendation"""
    song_id: int = Field(..., description="Song ID to find similar songs for", gt=0)
    k: int = Field(10, description="Number of similar songs to return", ge=1, le=50)
    metric: MetricType = Field(MetricType.cosine, description="Distance metric to use")

class SimilarSongsResponse(BaseModel):
    """Response model for similar songs recommendation"""
    song_id: int = Field(..., description="Original song ID")
    similar_songs: List[SongInfo] = Field(..., description="List of similar songs")
    algorithm: str = Field(..., description="Algorithm used")
    metric: str = Field(..., description="Distance metric used")

class ContentBasedRequest(BaseModel):
    """Request model for content-based recommendations"""
    song_title: str = Field(..., description="Song title to find recommendations for", min_length=1)
    n_recommendations: int = Field(10, description="Number of recommendations to return", ge=1, le=50)

class ContentBasedResponse(BaseModel):
    """Response model for content-based recommendations"""
    query_title: str = Field(..., description="Original query title")
    matched_title: str = Field(..., description="Best matching song title found")
    recommendations: List[SongInfo] = Field(..., description="List of recommended songs")
    algorithm: str = Field(..., description="Algorithm used")

class PopularSongsResponse(BaseModel):
    """Response model for popular songs"""
    popular_songs: List[SongInfo] = Field(..., description="List of popular songs")
    algorithm: str = Field(..., description="Algorithm used")
    limit: int = Field(..., description="Number of songs returned")

class UserPlayHistory(BaseModel):
    """User play history model"""
    user_id: str = Field(..., description="User identifier")
    song_id: int = Field(..., description="Song identifier")
    plays: int = Field(..., description="Number of plays")
    title: str = Field(..., description="Song title")
    genre: str = Field(..., description="Song genre")

class SystemStats(BaseModel):
    """System statistics model"""
    total_songs: int = Field(..., description="Total number of songs")
    total_users: int = Field(..., description="Total number of users")
    total_plays: int = Field(..., description="Total number of plays")
    total_genres: int = Field(..., description="Total number of genres")
    sparsity: Optional[float] = Field(None, description="Data sparsity percentage")
    avg_plays_per_user: Optional[float] = Field(None, description="Average plays per user")
    avg_plays_per_song: Optional[float] = Field(None, description="Average plays per song")

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    code: Optional[int] = Field(None, description="Error code")

class RecommendationEngineStatus(BaseModel):
    """Recommendation engine status"""
    is_initialized: bool = Field(..., description="Whether the engine is initialized")
    algorithms_available: List[str] = Field(..., description="Available recommendation algorithms")
    data_last_updated: Optional[str] = Field(None, description="When data was last updated")
    
class SearchRequest(BaseModel):
    """Search request model"""
    query: str = Field(..., description="Search query", min_length=1)
    limit: int = Field(10, description="Maximum number of results", ge=1, le=100)

class SearchResponse(BaseModel):
    """Search response model"""
    query: str = Field(..., description="Original search query")
    results: List[SongInfo] = Field(..., description="Search results")
    total_found: int = Field(..., description="Total number of results found")

class UserRecommendationRequest(BaseModel):
    """Request model for user-based recommendations"""
    user_id: str = Field(..., description="User ID to generate recommendations for")
    n_recommendations: int = Field(10, description="Number of recommendations", ge=1, le=50)
    algorithm: str = Field("collaborative", description="Algorithm to use")

class UserRecommendationResponse(BaseModel):
    """Response model for user-based recommendations"""
    user_id: str = Field(..., description="User ID")
    recommendations: List[SongInfo] = Field(..., description="Recommended songs")
    algorithm: str = Field(..., description="Algorithm used")
    user_profile: Optional[Dict[str, Any]] = Field(None, description="User profile information")
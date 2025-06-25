from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uvicorn
import logging

from .models import (
    SimilarSongsRequest, 
    SimilarSongsResponse, 
    ContentBasedRequest,
    ContentBasedResponse,
    PopularSongsResponse,
    SearchResponse,
    SystemStats
)
from .database import DatabaseManager
from .recommendation_engine import RecommendationEngine
from .config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MW Music Recommender API",
    description="Music recommendation system API with collaborative and content-based filtering",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings = get_settings()
db_manager = DatabaseManager(settings)
recommendation_engine = RecommendationEngine(db_manager)

@app.on_event("startup")
async def startup_event():
    """Initialize the recommendation engine on startup"""
    try:
        await recommendation_engine.initialize()
        logger.info("Recommendation engine initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize recommendation engine: {e}")

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {"message": "MW Music Recommender API is running", "version": "1.0.0"}

@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check"""
    try:
        # Test database connection
        db_status = await db_manager.health_check()
        return {
            "status": "healthy",
            "database": db_status,
            "recommendation_engine": "initialized" if recommendation_engine.is_initialized else "not_initialized"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.post("/recommendations/similar-songs", response_model=SimilarSongsResponse, tags=["Recommendations"])
async def get_similar_songs(request: SimilarSongsRequest):
    """Get similar songs using collaborative filtering (k-NN)"""
    try:
        similar_songs = await recommendation_engine.find_similar_songs(
            song_id=request.song_id,
            k=request.k,
            metric=request.metric.value
        )
        return SimilarSongsResponse(
            song_id=request.song_id,
            similar_songs=similar_songs,
            algorithm="collaborative_filtering_knn",
            metric=request.metric.value
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/recommendations/content-based", response_model=ContentBasedResponse, tags=["Recommendations"])
async def get_content_based_recommendations(request: ContentBasedRequest):
    """Get content-based recommendations using song genres"""
    try:
        recommendations = await recommendation_engine.get_content_based_recommendations(
            title_string=request.song_title,
            n_recommendations=request.n_recommendations
        )
        return ContentBasedResponse(
            query_title=request.song_title,
            matched_title=recommendations['matched_title'],
            recommendations=recommendations['songs'],
            algorithm="content_based_filtering"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/recommendations/popular", response_model=PopularSongsResponse, tags=["Recommendations"])
async def get_popular_songs(limit: int = 10, algorithm: str = "bayesian"):
    """Get popular songs using bayesian average or simple frequency"""
    try:
        popular_songs = await recommendation_engine.get_popular_songs(
            limit=limit,
            algorithm=algorithm
        )
        return PopularSongsResponse(
            popular_songs=popular_songs,
            algorithm=algorithm,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/songs/{song_id}", tags=["Songs"])
async def get_song_details(song_id: int):
    """Get details for a specific song"""
    try:
        song_details = await recommendation_engine.get_song_details(song_id)
        if not song_details:
            raise HTTPException(status_code=404, detail="Song not found")
        return song_details
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/songs/search/{query}", response_model=SearchResponse, tags=["Songs"])
async def search_songs(query: str, limit: int = 10):
    """Search songs by title"""
    try:
        results = await recommendation_engine.search_songs(query, limit)
        return SearchResponse(
            query=query,
            results=results,
            total_found=len(results)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/stats", response_model=SystemStats, tags=["Statistics"])
async def get_system_stats():
    """Get system statistics"""
    try:
        stats = await recommendation_engine.get_system_stats()
        return SystemStats(**stats)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
# MW Music Recommender API

A FastAPI-based REST API for music recommendations using collaborative filtering and content-based filtering algorithms.

## Features

- **Collaborative Filtering**: Find similar songs using k-nearest neighbors
- **Content-Based Filtering**: Recommend songs based on genre similarity
- **Popular Songs**: Get trending songs using Bayesian average or frequency
- **Search**: Find songs by title with fuzzy matching
- **Statistics**: System metrics and insights

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Database

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your database credentials:
```
DB_HOST=your_db_host
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=mwonya
```

### 3. Run the API

```bash
python run_api.py
```

The API will be available at `http://localhost:8000`

### 4. View API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Health Check
- `GET /` - Basic health check
- `GET /health` - Detailed health status

### Recommendations
- `POST /recommendations/similar-songs` - Get similar songs (collaborative filtering)
- `POST /recommendations/content-based` - Get content-based recommendations
- `GET /recommendations/popular` - Get popular songs

### Songs
- `GET /songs/{song_id}` - Get song details
- `GET /songs/search/{query}` - Search songs by title

### Statistics
- `GET /stats` - Get system statistics

## Example Usage

### Get Similar Songs
```bash
curl -X POST "http://localhost:8000/recommendations/similar-songs" \
  -H "Content-Type: application/json" \
  -d '{
    "song_id": 1787,
    "k": 5,
    "metric": "cosine"
  }'
```

### Content-Based Recommendations
```bash
curl -X POST "http://localhost:8000/recommendations/content-based" \
  -H "Content-Type: application/json" \
  -d '{
    "song_title": "Interest",
    "n_recommendations": 10
  }'
```

### Get Popular Songs
```bash
curl "http://localhost:8000/recommendations/popular?limit=10&algorithm=bayesian"
```

### Search Songs
```bash
curl "http://localhost:8000/songs/search/karamoja?limit=5"
```

## Response Format

All endpoints return JSON with song IDs and metadata:

```json
{
  "song_id": 1787,
  "similar_songs": [
    {
      "song_id": 973,
      "title": "Sacrifice",
      "genre": "Afro pop",
      "artist": "Artist Name",
      "similarity_score": 0.85
    }
  ],
  "algorithm": "collaborative_filtering_knn",
  "metric": "cosine"
}
```

## Architecture

The API is built with:
- **FastAPI**: Modern, fast web framework
- **Pydantic**: Data validation and serialization
- **scikit-learn**: Machine learning algorithms
- **pandas/numpy**: Data processing
- **MySQL**: Database backend

### Key Components

1. **RecommendationEngine**: Core ML algorithms
2. **DatabaseManager**: Async database operations
3. **Models**: Pydantic request/response models
4. **Config**: Environment-based configuration

## Extensibility

The system is designed for easy extension:

- **New Algorithms**: Add methods to `RecommendationEngine`
- **Additional Features**: Create new endpoints in `main.py`
- **Data Sources**: Extend `DatabaseManager` for new data
- **Metrics**: Add evaluation endpoints

## Performance Considerations

- **Async Operations**: All database calls are async
- **Sparse Matrices**: Efficient memory usage for large datasets
- **Caching**: Built-in caching support (configurable)
- **Connection Pooling**: Database connection optimization

## Error Handling

The API includes comprehensive error handling:
- Database connection failures
- Missing songs/users
- Invalid parameters
- Algorithm failures

## Development

### Adding New Recommendation Algorithms

1. Add method to `RecommendationEngine` class
2. Create request/response models in `models.py`
3. Add endpoint in `main.py`
4. Update documentation

### Testing

```bash
# Run tests (when implemented)
pytest tests/

# Test individual endpoints
curl http://localhost:8000/health
```

## Production Deployment

For production:
1. Set `ENVIRONMENT=production`
2. Use proper database credentials
3. Configure logging level
4. Use reverse proxy (nginx)
5. Enable authentication if needed

## License

MIT License - see LICENSE file for details
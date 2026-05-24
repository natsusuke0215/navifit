from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from schemas.place import PlaceNearbyResponse, PlaceDetailResponse
from services import places_service

router = APIRouter(tags=["places"])

@router.get("/nearby")
async def get_nearby_places(
    lat: float = Query(..., description="Vĩ độ"),
    lng: float = Query(..., description="Kinh độ"),
    radius: float = Query(20000.0, description="Bán kính tìm kiếm (mét)"),
    japanese_only: bool = Query(False, description="Ưu tiên các địa điểm có hỗ trợ tiếng Nhật"),
    db: AsyncSession = Depends(get_db)
):
    places = await places_service.get_nearby_places(db, lat, lng, radius, japanese_only)
    result = []
    for p in places:
        # Separator object (dict thuần)
        if isinstance(p, dict):
            result.append(p)
            continue
        result.append({
            "id": p.id, "name": p.name, "name_ja": p.name_ja,
            "address": p.address, "lat": p.lat, "lng": p.lng,
            "rating": p.rating, "category": p.category.value,
            "is_indoor": p.is_indoor, "has_japanese_support": p.has_japanese_support,
            "distance": p.distance, "is_priority": getattr(p, "is_priority", False),
            "safety_level": p.safety_level if hasattr(p, "safety_level") else 2,
            "is_separator": False,
        })
    return result


@router.get("/search", response_model=List[PlaceNearbyResponse])
async def search_places(
    q: str = Query(..., description="Từ khóa tìm kiếm"),
    lat: float = Query(..., description="Vĩ độ"),
    lng: float = Query(..., description="Kinh độ"),
    db: AsyncSession = Depends(get_db)
):
    places = await places_service.search_places(db, q, lat, lng)
    return places

from pydantic import BaseModel, Field
import math
from models.review import Review
from models.best_time import BestTime
from models.place import Place
from sqlalchemy import select, func

class ReviewCreate(BaseModel):
    user_name: str = Field(..., max_length=100)
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field(None, max_length=500)

@router.get("/{place_id}/reviews")
async def get_reviews(place_id: int, page: int = 1, limit: int = 10, db: AsyncSession = Depends(get_db)):
    # count total
    total_stmt = select(func.count(Review.id)).where(Review.place_id == place_id)
    total_res = await db.execute(total_stmt)
    total = total_res.scalar()
    
    # query
    stmt = select(Review).where(Review.place_id == place_id).order_by(Review.created_at.desc()).offset((page-1)*limit).limit(limit)
    res = await db.execute(stmt)
    reviews = res.scalars().all()
    
    return {
        "reviews": [{"id": r.id, "user_name": r.user_name, "rating": r.rating, "comment": r.comment, "created_at": r.created_at} for r in reviews],
        "total": total,
        "page": page,
        "total_pages": math.ceil(total / limit) if total > 0 else 1
    }

@router.get("/{place_id}/best-times")
async def get_best_times(place_id: int, type: str = Query("week"), day_of_week: int = Query(0), db: AsyncSession = Depends(get_db)):
    def get_color(score):
        if score >= 70: return "#4CAF50"
        if score >= 40: return "#FFC107"
        return "#F44336"

    if type == "week":
        stmt = select(BestTime.day_of_week, func.avg(BestTime.score).label("avg_score")).where(BestTime.place_id == place_id).group_by(BestTime.day_of_week)
        res = await db.execute(stmt)
        data = res.all()
        
        days = {0: "T2", 1: "T3", 2: "T4", 3: "T5", 4: "T6", 5: "T7", 6: "CN"}
        result_map = {i: 0 for i in range(7)}
        for row in data:
            result_map[row.day_of_week] = int(row.avg_score)
            
        return [{"day": i, "label": days[i], "avg_score": result_map[i], "color": get_color(result_map[i])} for i in range(7)]
        
    elif type == "day":
        stmt = select(BestTime).where(BestTime.place_id == place_id, BestTime.day_of_week == day_of_week).order_by(BestTime.hour)
        res = await db.execute(stmt)
        data = res.scalars().all()
        
        result_map = {i: 0 for i in range(24)}
        for row in data:
            result_map[row.hour] = row.score
            
        return [{"hour": i, "label": f"{i:02d}:00", "score": result_map[i], "color": get_color(result_map[i])} for i in range(24)]

@router.get("/{place_id}/detail")
async def get_place_detail_full(place_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Place).where(Place.id == place_id))
    place = res.scalar_one_or_none()
    if not place: raise HTTPException(status_code=404, detail="Không tìm thấy địa điểm")
    
    place_dict = {
        "id": place.id, "name": place.name, "name_ja": place.name_ja, "address": place.address,
        "lat": place.lat, "lng": place.lng, "rating": place.rating, "category": place.category.value,
        "is_indoor": place.is_indoor, "has_japanese_support": place.has_japanese_support
    }
    
    place_dict["reviews_data"] = await get_reviews(place_id, 1, 10, db)
    place_dict["best_times_data"] = await get_best_times(place_id, "week", 0, db)
    
    return place_dict

@router.post("/{place_id}/reviews")
async def create_review(place_id: int, review: ReviewCreate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Place).where(Place.id == place_id))
    place = res.scalar_one_or_none()
    if not place: raise HTTPException(404, detail="Không tìm thấy địa điểm")
    
    new_rev = Review(place_id=place_id, user_name=review.user_name, rating=review.rating, comment=review.comment)
    db.add(new_rev)
    await db.commit()
    await db.refresh(new_rev)
    
    avg_stmt = select(func.avg(Review.rating)).where(Review.place_id == place_id)
    avg_res = await db.execute(avg_stmt)
    new_avg = avg_res.scalar()
    
    if new_avg is not None:
        place.rating = round(new_avg, 1)
        await db.commit()
    
    return {
        "review": {"id": new_rev.id, "user_name": new_rev.user_name, "rating": new_rev.rating, "comment": new_rev.comment, "created_at": new_rev.created_at},
        "new_avg_rating": place.rating
    }

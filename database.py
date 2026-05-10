import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/navifit")

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()

async def get_db():
    async with async_session() as session:
        yield session

async def init_db():
    from models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def seed_data():
    import random
    from models import Place, SOSChannel, PlaceCategory, SOSType
    from models.best_time import BestTime
    from sqlalchemy import delete

    async with async_session() as session:
        # Xóa data cũ trước khi seed mới
        await session.execute(delete(BestTime))
        await session.execute(delete(Place))
        await session.execute(delete(SOSChannel))
        await session.commit()

        # ── 20 địa điểm tập luyện tại Hà Nội ───────────────────────────────
        places = [
            # PARK
            Place(name="Công viên Thống Nhất", name_ja="統一公園",
                  address="Trần Nhân Tông, Hai Bà Trưng, Hà Nội",
                  lat=21.0245, lng=105.8412, category=PlaceCategory.park,
                  is_indoor=False, has_japanese_support=True, rating=4.5, safety_level=1,
                  opening_hours={"T2-CN": "05:00-22:00"}, phone="024-3822-1234"),
            Place(name="Công viên Hồ Tây", name_ja="西湖公園",
                  address="Thanh Niên, Tây Hồ, Hà Nội",
                  lat=21.0476, lng=105.8358, category=PlaceCategory.park,
                  is_indoor=False, has_japanese_support=False, rating=4.7, safety_level=1,
                  opening_hours={"T2-CN": "05:00-22:00"}, phone="024-3823-5678"),
            Place(name="Công viên Nghĩa Đô", name_ja="ギアド公園",
                  address="Hoàng Quốc Việt, Cầu Giấy, Hà Nội",
                  lat=21.0432, lng=105.8098, category=PlaceCategory.park,
                  is_indoor=False, has_japanese_support=True, rating=4.2, safety_level=2,
                  opening_hours={"T2-CN": "05:30-21:30"}, phone="024-3756-1234"),
            Place(name="Vườn hoa Lý Thái Tổ", name_ja="リータイトー広場",
                  address="Đinh Tiên Hoàng, Hoàn Kiếm, Hà Nội",
                  lat=21.0285, lng=105.8542, category=PlaceCategory.park,
                  is_indoor=False, has_japanese_support=False, rating=4.0, safety_level=1,
                  opening_hours={"T2-CN": "06:00-22:00"}, phone=""),
            Place(name="Công viên Thủ Lệ", name_ja="トゥーレー動物園公園",
                  address="Cầu Giấy, Hà Nội",
                  lat=21.0298, lng=105.8056, category=PlaceCategory.park,
                  is_indoor=False, has_japanese_support=False, rating=4.3, safety_level=2,
                  opening_hours={"T2-CN": "06:00-21:00"}, phone="024-3834-2345"),
            # GYM
            Place(name="California Fitness Hà Nội", name_ja="カリフォルニアフィットネス",
                  address="72 Trần Hưng Đạo, Hoàn Kiếm, Hà Nội",
                  lat=21.0278, lng=105.8515, category=PlaceCategory.gym,
                  is_indoor=True, has_japanese_support=True, rating=4.6, safety_level=1,
                  opening_hours={"T2-T6": "05:30-23:00", "T7-CN": "07:00-22:00"},
                  phone="024-3936-5678"),
            Place(name="Gym 24h Đống Đa", name_ja="24時間ジム ドンダー",
                  address="Đống Đa, Hà Nội",
                  lat=21.0213, lng=105.8456, category=PlaceCategory.gym,
                  is_indoor=True, has_japanese_support=False, rating=4.1, safety_level=2,
                  opening_hours={"T2-CN": "00:00-23:59"}, phone="024-3512-7890"),
            Place(name="Elite Fitness Ba Đình", name_ja="エリートフィットネス バーディン",
                  address="Ba Đình, Hà Nội",
                  lat=21.0362, lng=105.8374, category=PlaceCategory.gym,
                  is_indoor=True, has_japanese_support=True, rating=4.8, safety_level=1,
                  opening_hours={"T2-T6": "06:00-22:00", "T7-CN": "07:00-21:00"},
                  phone="024-3736-4567"),
            Place(name="Fit24 Cầu Giấy", name_ja="フィット24 カウザイ",
                  address="Cầu Giấy, Hà Nội",
                  lat=21.0354, lng=105.7987, category=PlaceCategory.gym,
                  is_indoor=True, has_japanese_support=False, rating=4.3, safety_level=2,
                  opening_hours={"T2-CN": "05:00-23:00"}, phone="024-3756-8901"),
            Place(name="Zen Yoga & Gym Tây Hồ", name_ja="ゼンヨガ＆ジム タイホー",
                  address="Tây Hồ, Hà Nội",
                  lat=21.0553, lng=105.8329, category=PlaceCategory.gym,
                  is_indoor=True, has_japanese_support=True, rating=4.5, safety_level=1,
                  opening_hours={"T2-T6": "06:00-21:00", "T7-CN": "08:00-20:00"},
                  phone="024-3718-2345"),
            Place(name="IronWolf Gym Hai Bà Trưng", name_ja="アイアンウルフ ジム",
                  address="Hai Bà Trưng, Hà Nội",
                  lat=21.0156, lng=105.8523, category=PlaceCategory.gym,
                  is_indoor=True, has_japanese_support=True, rating=4.0, safety_level=2,
                  opening_hours={"T2-T6": "05:00-23:00", "T7-CN": "07:00-22:00"},
                  phone="024-3976-3456"),
            Place(name="Lotte Fitness Center", name_ja="ロッテフィットネスセンター",
                  address="Liễu Giai, Ba Đình, Hà Nội",
                  lat=21.0143, lng=105.8178, category=PlaceCategory.gym,
                  is_indoor=True, has_japanese_support=True, rating=4.9, safety_level=1,
                  opening_hours={"T2-T6": "06:00-22:00", "T7-CN": "07:00-21:00"},
                  phone="024-3333-6789"),
            # POOL
            Place(name="Bể bơi Mỹ Đình", name_ja="ミーディン水泳プール",
                  address="Mỹ Đình, Nam Từ Liêm, Hà Nội",
                  lat=21.0215, lng=105.7645, category=PlaceCategory.pool,
                  is_indoor=True, has_japanese_support=True, rating=4.4, safety_level=2,
                  opening_hours={"T2-T6": "06:00-21:00", "T7-CN": "06:00-22:00"},
                  phone="024-3768-9012"),
            Place(name="Hồ bơi Hoàng Mai", name_ja="ホアンマイ室内プール",
                  address="Hoàng Mai, Hà Nội",
                  lat=20.9876, lng=105.8612, category=PlaceCategory.pool,
                  is_indoor=True, has_japanese_support=False, rating=3.9, safety_level=3,
                  opening_hours={"T2-CN": "06:00-20:00"}, phone="024-3641-3456"),
            Place(name="Bể bơi Trung Tự", name_ja="チュントゥプール",
                  address="Đống Đa, Hà Nội",
                  lat=21.0134, lng=105.8378, category=PlaceCategory.pool,
                  is_indoor=False, has_japanese_support=False, rating=4.0, safety_level=2,
                  opening_hours={"T2-CN": "06:00-20:00"}, phone="024-3852-5678"),
            Place(name="Hapulico Gym & Pool", name_ja="ハプリコ ジム＆プール",
                  address="Vũ Trọng Phụng, Thanh Xuân, Hà Nội",
                  lat=20.9998, lng=105.8167, category=PlaceCategory.pool,
                  is_indoor=True, has_japanese_support=True, rating=4.6, safety_level=2,
                  opening_hours={"T2-CN": "06:00-22:00"}, phone="024-6251-4567"),
            # BADMINTON
            Place(name="Sân cầu lông Nguyễn Tri Phương", name_ja="グエントリフオン バドミントン",
                  address="Nguyễn Tri Phương, Ba Đình, Hà Nội",
                  lat=21.0198, lng=105.8489, category=PlaceCategory.badminton,
                  is_indoor=True, has_japanese_support=True, rating=4.2, safety_level=2,
                  opening_hours={"T2-CN": "06:00-22:00"}, phone="024-3733-6789"),
            Place(name="Trung tâm cầu lông Gia Lâm", name_ja="ザーラム バドミントンセンター",
                  address="Gia Lâm, Hà Nội",
                  lat=21.0289, lng=105.9012, category=PlaceCategory.badminton,
                  is_indoor=True, has_japanese_support=True, rating=4.5, safety_level=3,
                  opening_hours={"T2-T6": "06:00-22:00", "T7-CN": "07:00-22:00"},
                  phone="024-3827-0123"),
            Place(name="CLB Cầu lông Đống Đa", name_ja="ドンダー バドミントンクラブ",
                  address="Đống Đa, Hà Nội",
                  lat=21.0234, lng=105.8401, category=PlaceCategory.badminton,
                  is_indoor=True, has_japanese_support=False, rating=4.1, safety_level=2,
                  opening_hours={"T2-CN": "05:30-22:30"}, phone="024-3514-1234"),
            Place(name="Sân cầu lông Bạch Mai", name_ja="バクマイ バドミントン",
                  address="Bạch Mai, Hai Bà Trưng, Hà Nội",
                  lat=21.0023, lng=105.8489, category=PlaceCategory.badminton,
                  is_indoor=True, has_japanese_support=False, rating=3.8, safety_level=3,
                  opening_hours={"T2-CN": "06:00-22:00"}, phone="024-3623-5678"),
        ]
        session.add_all(places)
        await session.flush()  # lấy ID trước khi commit

        # Thêm các kênh SOS
        sos_channels = [
            SOSChannel(name="Cảnh sát", name_ja="警察", phone="113", type=SOSType.police),
            SOSChannel(name="Cứu thương", name_ja="救急車", phone="115", type=SOSType.hospital),
            SOSChannel(name="Cứu hỏa", name_ja="消防車", phone="114", type=SOSType.other),
            SOSChannel(name="ĐSQ Nhật Bản tại HN", name_ja="在ハノイ日本大使館", phone="+84-24-3846-3000", type=SOSType.embassy),
            SOSChannel(name="Tổng đài du lịch", name_ja="観光ホットライン", phone="1800-599-902", type=SOSType.other),
            SOSChannel(name="Bệnh viện Việt Đức", name_ja="ビェットドゥック病院", phone="024-3825-3531", type=SOSType.hospital),
        ]
        session.add_all(sos_channels)

        # Seed BestTime: 7 ngày × 24 giờ cho mỗi place
        def base_score(day: int, hour: int) -> int:
            is_weekend = day >= 5
            if is_weekend:
                if 0 <= hour < 5:   return random.randint(15, 30)
                if 5 <= hour < 20:  return random.randint(60, 92)
                return random.randint(30, 55)
            else:
                if 0 <= hour < 5:   return random.randint(10, 25)
                if 5 <= hour < 9:   return random.randint(70, 90)
                if 9 <= hour < 11:  return random.randint(40, 65)
                if 11 <= hour < 14: return random.randint(15, 38)
                if 14 <= hour < 17: return random.randint(40, 65)
                if 17 <= hour < 21: return random.randint(72, 95)
                return random.randint(25, 45)

        best_time_records = []
        for place in places:
            for day in range(7):
                for hour in range(24):
                    best_time_records.append(BestTime(
                        place_id=place.id,
                        day_of_week=day,
                        hour=hour,
                        score=base_score(day, hour)
                    ))
        session.add_all(best_time_records)

        await session.commit()

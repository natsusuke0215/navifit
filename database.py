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
    from sqlalchemy import delete, select, func

    seed_enabled = os.getenv("SEED_ON_STARTUP", "true").lower() == "true"

    async with async_session() as session:
        if not seed_enabled:
            existing = await session.execute(select(func.count(Place.id)))
            if existing.scalar() > 0:
                print("Seed skipped: SEED_ON_STARTUP=false and places already exist.")
                return

        # Xóa data cũ trước khi seed mới
        await session.execute(delete(BestTime))
        await session.execute(delete(Place))
        await session.execute(delete(SOSChannel))
        
        # ── Địa điểm tập luyện và dịch vụ tại Hà Nội ──────────────────────────
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
            Place(name="Bể bơi Cung Thể thao Hà Nội", name_ja="ハノイスポーツセンタープール",
                  address="Trần Phú, Hà Đông, Hà Nội",
                  lat=20.9712, lng=105.7765, category=PlaceCategory.pool,
                  is_indoor=True, has_japanese_support=False, rating=4.1, safety_level=2,
                  opening_hours={"T2-CN": "06:00-21:00"}, phone="024-3383-1234"),
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
            Place(name="Sân cầu lông Cầu Giấy Sport", name_ja="カウザイスポーツ バドミントン",
                  address="Dương Đình Nghệ, Cầu Giấy, Hà Nội",
                  lat=21.0312, lng=105.7963, category=PlaceCategory.badminton,
                  is_indoor=True, has_japanese_support=False, rating=4.3, safety_level=2,
                  opening_hours={"T2-CN": "06:00-22:00"}, phone="024-3756-5678"),
            # TENNIS
            Place(name="CLB Tennis Phạm Văn Bạch", name_ja="ファムバンバックテニスクラブ",
                  address="Phạm Văn Bạch, Cầu Giấy, Hà Nội",
                  lat=21.0371, lng=105.7921, category=PlaceCategory.tennis,
                  is_indoor=False, has_japanese_support=False, rating=4.2, safety_level=2,
                  opening_hours={"T2-CN": "06:00-21:00"}, phone="024-3756-3456"),
            Place(name="Sân Tennis Hồ Tây Sports", name_ja="タイホーテニスコート",
                  address="Quảng Khánh, Tây Hồ, Hà Nội",
                  lat=21.0541, lng=105.8218, category=PlaceCategory.tennis,
                  is_indoor=False, has_japanese_support=True, rating=4.5, safety_level=1,
                  opening_hours={"T2-CN": "06:00-21:30"}, phone="024-3718-4567"),
            Place(name="Câu lạc bộ Tennis Mỹ Đình", name_ja="ミーディンテニスクラブ",
                  address="Mỹ Đình, Nam Từ Liêm, Hà Nội",
                  lat=21.0192, lng=105.7656, category=PlaceCategory.tennis,
                  is_indoor=False, has_japanese_support=False, rating=4.0, safety_level=2,
                  opening_hours={"T2-CN": "05:30-21:00"}, phone="024-3768-2345"),
            Place(name="CLB Tennis Hoàng Mai", name_ja="ホアンマイテニスクラブ",
                  address="Hoàng Mai, Hà Nội",
                  lat=20.9923, lng=105.8574, category=PlaceCategory.tennis,
                  is_indoor=False, has_japanese_support=False, rating=3.9, safety_level=2,
                  opening_hours={"T2-CN": "06:00-21:00"}, phone="024-3641-6789"),
            Place(name="Sân Tennis Láng Hạ", name_ja="ランハーテニスコート",
                  address="Láng Hạ, Đống Đa, Hà Nội",
                  lat=21.0214, lng=105.8312, category=PlaceCategory.tennis,
                  is_indoor=False, has_japanese_support=True, rating=4.3, safety_level=1,
                  opening_hours={"T2-CN": "06:00-21:00"}, phone="024-3514-7890"),
            # PICKLEBALL
            Place(name="Sân Pickleball Cầu Giấy", name_ja="カウザイ ピックルボールコート",
                  address="Dịch Vọng, Cầu Giấy, Hà Nội",
                  lat=21.0389, lng=105.8002, category=PlaceCategory.pickleball,
                  is_indoor=True, has_japanese_support=True, rating=4.4, safety_level=1,
                  opening_hours={"T2-CN": "07:00-22:00"}, phone="024-3756-9012"),
            Place(name="Sân Pickleball Tây Hồ", name_ja="タイホー ピックルボールコート",
                  address="Xuân La, Tây Hồ, Hà Nội",
                  lat=21.0528, lng=105.8265, category=PlaceCategory.pickleball,
                  is_indoor=False, has_japanese_support=True, rating=4.6, safety_level=1,
                  opening_hours={"T2-CN": "06:30-21:30"}, phone="024-3718-6789"),
            Place(name="Sân Pickleball Thanh Xuân", name_ja="タインスアン ピックルボールコート",
                  address="Thanh Xuân, Hà Nội",
                  lat=20.9971, lng=105.8154, category=PlaceCategory.pickleball,
                  is_indoor=True, has_japanese_support=False, rating=4.1, safety_level=2,
                  opening_hours={"T2-CN": "07:00-21:00"}, phone="024-6251-8901"),
            Place(name="Sân Pickleball Long Biên", name_ja="ロンビエン ピックルボールコート",
                  address="Long Biên, Hà Nội",
                  lat=21.0312, lng=105.8821, category=PlaceCategory.pickleball,
                  is_indoor=False, has_japanese_support=False, rating=3.8, safety_level=2,
                  opening_hours={"T2-CN": "06:00-21:00"}, phone="024-3827-3456"),
            Place(name="Sân Pickleball Ba Đình Arena", name_ja="バーディン アリーナ ピックルボール",
                  address="Đội Cấn, Ba Đình, Hà Nội",
                  lat=21.0371, lng=105.8356, category=PlaceCategory.pickleball,
                  is_indoor=True, has_japanese_support=True, rating=4.5, safety_level=1,
                  opening_hours={"T2-T6": "07:00-22:00", "T7-CN": "06:00-22:00"},
                  phone="024-3736-7890"),
            # HOSPITAL
            Place(name="Bệnh viện Bạch Mai", name_ja="バクマイ病院",
                  address="Giải Phóng, Đống Đa, Hà Nội",
                  lat=21.0053, lng=105.8431, category=PlaceCategory.hospital,
                  is_indoor=True, has_japanese_support=False, rating=4.2, safety_level=1,
                  opening_hours={"T2-CN": "00:00-23:59"}, phone="024-3869-3731"),
            Place(name="Bệnh viện Việt Đức", name_ja="ビェットドゥック病院",
                  address="Tràng Thi, Hoàn Kiếm, Hà Nội",
                  lat=21.0265, lng=105.8492, category=PlaceCategory.hospital,
                  is_indoor=True, has_japanese_support=True, rating=4.5, safety_level=1,
                  opening_hours={"T2-CN": "00:00-23:59"}, phone="024-3825-3531"),
            Place(name="Bệnh viện Hữu Nghị Việt Xô", name_ja="ベトソー友好病院",
                  address="Trần Khánh Dư, Hai Bà Trưng, Hà Nội",
                  lat=21.0178, lng=105.8443, category=PlaceCategory.hospital,
                  is_indoor=True, has_japanese_support=False, rating=4.3, safety_level=1,
                  opening_hours={"T2-CN": "00:00-23:59"}, phone="024-3574-7215"),
            Place(name="Bệnh viện E", name_ja="E病院",
                  address="Trần Cung, Cầu Giấy, Hà Nội",
                  lat=21.0412, lng=105.8098, category=PlaceCategory.hospital,
                  is_indoor=True, has_japanese_support=False, rating=4.0, safety_level=1,
                  opening_hours={"T2-CN": "00:00-23:59"}, phone="024-3762-8662"),
            Place(name="Bệnh viện Trung ương Quân đội 108", name_ja="108中央軍病院",
                  address="Trần Hưng Đạo, Hai Bà Trưng, Hà Nội",
                  lat=21.0143, lng=105.8478, category=PlaceCategory.hospital,
                  is_indoor=True, has_japanese_support=True, rating=4.6, safety_level=1,
                  opening_hours={"T2-CN": "00:00-23:59"}, phone="024-3868-5298"),
            Place(name="Bệnh viện K Tân Triều", name_ja="Kがん病院 タントリエウ",
                  address="Tân Triều, Thanh Trì, Hà Nội",
                  lat=20.9782, lng=105.8312, category=PlaceCategory.hospital,
                  is_indoor=True, has_japanese_support=False, rating=4.1, safety_level=1,
                  opening_hours={"T2-CN": "00:00-23:59"}, phone="024-3852-0120"),
            Place(name="Bệnh viện Thanh Nhàn", name_ja="タインニャン病院",
                  address="Thanh Nhàn, Hai Bà Trưng, Hà Nội",
                  lat=21.0092, lng=105.8623, category=PlaceCategory.hospital,
                  is_indoor=True, has_japanese_support=False, rating=3.9, safety_level=1,
                  opening_hours={"T2-CN": "00:00-23:59"}, phone="024-3622-4714"),
            Place(name="Bệnh viện Phụ sản Hà Nội", name_ja="ハノイ産婦人科病院",
                  address="Chu Văn An, Ba Đình, Hà Nội",
                  lat=21.0293, lng=105.8363, category=PlaceCategory.hospital,
                  is_indoor=True, has_japanese_support=True, rating=4.4, safety_level=1,
                  opening_hours={"T2-CN": "00:00-23:59"}, phone="024-3832-2668"),
            Place(name="Bệnh viện Nhi Trung ương", name_ja="国立小児病院",
                  address="La Thành, Đống Đa, Hà Nội",
                  lat=21.0198, lng=105.8365, category=PlaceCategory.hospital,
                  is_indoor=True, has_japanese_support=False, rating=4.3, safety_level=1,
                  opening_hours={"T2-CN": "00:00-23:59"}, phone="024-3843-4943"),
            Place(name="Bệnh viện Xanh Pôn", name_ja="サンポール病院",
                  address="Chu Văn An, Ba Đình, Hà Nội",
                  lat=21.0342, lng=105.8483, category=PlaceCategory.hospital,
                  is_indoor=True, has_japanese_support=False, rating=4.0, safety_level=1,
                  opening_hours={"T2-CN": "00:00-23:59"}, phone="024-3846-4421"),
            # POLICE
            Place(name="Công an quận Hoàn Kiếm", name_ja="ホアンキエム区警察署",
                  address="Đinh Lễ, Hoàn Kiếm, Hà Nội",
                  lat=21.0289, lng=105.8523, category=PlaceCategory.police,
                  is_indoor=True, has_japanese_support=False, rating=4.0, safety_level=1,
                  opening_hours={"T2-CN": "00:00-23:59"}, phone="024-3825-3114"),
            Place(name="Công an quận Đống Đa", name_ja="ドンダー区警察署",
                  address="Đống Đa, Hà Nội",
                  lat=21.0201, lng=105.8412, category=PlaceCategory.police,
                  is_indoor=True, has_japanese_support=False, rating=4.0, safety_level=1,
                  opening_hours={"T2-CN": "00:00-23:59"}, phone="024-3512-0113"),
            Place(name="Công an quận Hai Bà Trưng", name_ja="ハイバートゥン区警察署",
                  address="Hai Bà Trưng, Hà Nội",
                  lat=21.0103, lng=105.8521, category=PlaceCategory.police,
                  is_indoor=True, has_japanese_support=False, rating=4.0, safety_level=1,
                  opening_hours={"T2-CN": "00:00-23:59"}, phone="024-3624-0113"),
            Place(name="Công an quận Ba Đình", name_ja="バーディン区警察署",
                  address="Ba Đình, Hà Nội",
                  lat=21.0343, lng=105.8401, category=PlaceCategory.police,
                  is_indoor=True, has_japanese_support=False, rating=4.1, safety_level=1,
                  opening_hours={"T2-CN": "00:00-23:59"}, phone="024-3736-0113"),
            Place(name="Công an quận Cầu Giấy", name_ja="カウザイ区警察署",
                  address="Cầu Giấy, Hà Nội",
                  lat=21.0381, lng=105.7978, category=PlaceCategory.police,
                  is_indoor=True, has_japanese_support=False, rating=4.0, safety_level=1,
                  opening_hours={"T2-CN": "00:00-23:59"}, phone="024-3756-0113"),
            Place(name="Công an quận Tây Hồ", name_ja="タイホー区警察署",
                  address="Tây Hồ, Hà Nội",
                  lat=21.0531, lng=105.8281, category=PlaceCategory.police,
                  is_indoor=True, has_japanese_support=False, rating=4.0, safety_level=1,
                  opening_hours={"T2-CN": "00:00-23:59"}, phone="024-3718-0113"),
            Place(name="Công an quận Thanh Xuân", name_ja="タインスアン区警察署",
                  address="Thanh Xuân, Hà Nội",
                  lat=20.9952, lng=105.8121, category=PlaceCategory.police,
                  is_indoor=True, has_japanese_support=False, rating=4.0, safety_level=1,
                  opening_hours={"T2-CN": "00:00-23:59"}, phone="024-3858-0113"),
            Place(name="Công an quận Hoàng Mai", name_ja="ホアンマイ区警察署",
                  address="Hoàng Mai, Hà Nội",
                  lat=20.9881, lng=105.8623, category=PlaceCategory.police,
                  is_indoor=True, has_japanese_support=False, rating=4.0, safety_level=1,
                  opening_hours={"T2-CN": "00:00-23:59"}, phone="024-3641-0113"),
            Place(name="Công an quận Long Biên", name_ja="ロンビエン区警察署",
                  address="Long Biên, Hà Nội",
                  lat=21.0331, lng=105.8923, category=PlaceCategory.police,
                  is_indoor=True, has_japanese_support=False, rating=4.0, safety_level=1,
                  opening_hours={"T2-CN": "00:00-23:59"}, phone="024-3827-0113"),
            Place(name="Công an quận Nam Từ Liêm", name_ja="ナムトゥリエム区警察署",
                  address="Nam Từ Liêm, Hà Nội",
                  lat=21.0213, lng=105.7634, category=PlaceCategory.police,
                  is_indoor=True, has_japanese_support=False, rating=4.0, safety_level=1,
                  opening_hours={"T2-CN": "00:00-23:59"}, phone="024-3768-0113"),
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
        BATCH_SIZE = 500
        for i in range(0, len(best_time_records), BATCH_SIZE):
            session.add_all(best_time_records[i:i + BATCH_SIZE])
            await session.commit()
        print(f"Seeded best_times batch {i // BATCH_SIZE + 1}/{(len(best_time_records) + BATCH_SIZE - 1) // BATCH_SIZE}")

        
-- Thêm vào bảng listings
ALTER TABLE listings ADD address_full  NVARCHAR(500) NULL;  
ALTER TABLE listings ADD lat           FLOAT         NULL;  
ALTER TABLE listings ADD lng           FLOAT         NULL;
ALTER TABLE listings ADD room_type     NVARCHAR(100) NULL;  
ALTER TABLE listings ADD posted_at     DATETIME      NULL;  

-- Thêm vào bảng listing_features
ALTER TABLE listing_features ADD has_furniture      BIT NOT NULL DEFAULT 0;  
ALTER TABLE listing_features ADD has_loft           BIT NOT NULL DEFAULT 0;  
ALTER TABLE listing_features ADD has_washer         BIT NOT NULL DEFAULT 0; 
ALTER TABLE listing_features ADD has_fridge         BIT NOT NULL DEFAULT 0;  
ALTER TABLE listing_features ADD has_elevator       BIT NOT NULL DEFAULT 0;  
ALTER TABLE listing_features ADD has_basement       BIT NOT NULL DEFAULT 0;  
ALTER TABLE listing_features ADD free_hours         BIT NOT NULL DEFAULT 0;  
ALTER TABLE listing_features ADD no_owner           BIT NOT NULL DEFAULT 0;

IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME='districts' AND COLUMN_NAME='lat'
)
BEGIN
    ALTER TABLE districts ADD lat FLOAT NULL;
    ALTER TABLE districts ADD lng FLOAT NULL;
END
GO

UPDATE districts SET lat=10.7769, lng=106.7009 WHERE district_id=1;
UPDATE districts SET lat=10.7872, lng=106.7519 WHERE district_id=2;
UPDATE districts SET lat=10.7794, lng=106.6880 WHERE district_id=3;
UPDATE districts SET lat=10.7580, lng=106.7040 WHERE district_id=4;
UPDATE districts SET lat=10.7540, lng=106.6650 WHERE district_id=5;
UPDATE districts SET lat=10.7456, lng=106.6342 WHERE district_id=6;
UPDATE districts SET lat=10.7324, lng=106.7218 WHERE district_id=7;
UPDATE districts SET lat=10.7239, lng=106.6282 WHERE district_id=8;
UPDATE districts SET lat=10.8414, lng=106.7897 WHERE district_id=9;
UPDATE districts SET lat=10.7728, lng=106.6667 WHERE district_id=10;
UPDATE districts SET lat=10.7634, lng=106.6489 WHERE district_id=11;
UPDATE districts SET lat=10.8682, lng=106.6447 WHERE district_id=12;
UPDATE districts SET lat=10.8121, lng=106.7125 WHERE district_id=13;
UPDATE districts SET lat=10.7641, lng=106.6086 WHERE district_id=14;
UPDATE districts SET lat=10.8385, lng=106.6659 WHERE district_id=15;
UPDATE districts SET lat=10.7995, lng=106.6799 WHERE district_id=16;
UPDATE districts SET lat=10.8013, lng=106.6525 WHERE district_id=17;
UPDATE districts SET lat=10.7901, lng=106.6281 WHERE district_id=18;
UPDATE districts SET lat=10.8588, lng=106.7594 WHERE district_id=19;
UPDATE districts SET lat=10.6880, lng=106.6100 WHERE district_id=20;
UPDATE districts SET lat=10.8911, lng=106.5958 WHERE district_id=21;
UPDATE districts SET lat=10.6997, lng=106.7370 WHERE district_id=22;
UPDATE districts SET lat=10.4113, lng=106.9531 WHERE district_id=23;
UPDATE districts SET lat=10.9767, lng=106.4956 WHERE district_id=24;
GO


ALTER TABLE listing_features ADD near_uni           BIT NOT NULL DEFAULT 0;
GO


ALTER VIEW ml_features AS
SELECT
    l.listing_id,
    l.price_vnd,
    l.area_m2,
    l.district_id,
    d.name                    AS district_name,
    ISNULL(l.lat, d.lat)      AS lat,
    ISNULL(l.lng, d.lng)      AS lng,
    l.room_type,
    l.posted_at,
    CASE
        WHEN l.area_m2 > 0
        THEN CAST(l.price_vnd AS FLOAT) / l.area_m2
        ELSE NULL
    END                       AS price_per_m2,
    ISNULL(f.has_wc,       0) AS has_wc,
    ISNULL(f.has_ac,       0) AS has_ac,
    ISNULL(f.has_parking,  0) AS has_parking,
    ISNULL(f.has_kitchen,  0) AS has_kitchen,
    ISNULL(f.has_balcony,  0) AS has_balcony,
    ISNULL(f.has_security, 0) AS has_security,
    ISNULL(f.has_furniture,0) AS has_furniture,
    ISNULL(f.has_loft,     0) AS has_loft,
    ISNULL(f.has_washer,   0) AS has_washer,
    ISNULL(f.has_fridge,   0) AS has_fridge,
    ISNULL(f.has_elevator, 0) AS has_elevator,
    ISNULL(f.has_basement, 0) AS has_basement,
    ISNULL(f.free_hours,   0) AS free_hours,
    ISNULL(f.no_owner,     0) AS no_owner,
    ISNULL(f.near_uni, 0) AS near_uni,

    l.scraped_at
FROM listings l
LEFT JOIN districts        d ON l.district_id = d.district_id
LEFT JOIN listing_features f ON l.listing_id  = f.listing_id
WHERE l.is_dulicate = 0
  AND l.price_vnd    > 0
  AND l.area_m2      > 0;
GO



ALTER TABLE listings ADD posted_at_raw NVARCHAR(100);

ALTER TABLE listing_features
DROP CONSTRAINT DF__listing_f__is_ma__01142BA1;

ALTER TABLE listing_features 
DROP COLUMN is_master_room;
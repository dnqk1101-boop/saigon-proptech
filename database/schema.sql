CREATE DATABASE SaigonPropTech;
GO

USE SaigonPropTech
GO

CREATE TABLE districts (
    district_id     INT             PRIMARY KEY IDENTITY(1,1),
    name            NVARCHAR(1000)  NOT NULL,
    city            NVARCHAR(100)   NOT NULL DEFAULT N'TP. Hồ Chí Minh',
    created_at      DATETIME        NOT NULL DEFAULT GETDATE()
);

INSERT INTO districts(name) VALUES
(N'Quận 1'),
(N'Quận 2'),
(N'Quận 3'),
(N'Quận 4'),
(N'Quận 5'),
(N'Quận 6'),
(N'Quận 7'),
(N'Quận 8'),
(N'Quận 9'),
(N'Quận 10'),
(N'Quận 11'),
(N'Quận 12'),
(N'Bình Thạnh'),
(N'Bình Tân'),
(N'Gò Vấp'),
(N'Phú Nhuận'),
(N'Tân Bình'),
(N'Tân Phú'),
(N'Thủ Đức'),
(N'Bình Chánh'),
(N'Hóc Môn'),
(N'Nhà Bè'),
(N'Cần Giờ'),
(N'Củ Chi');
GO


CREATE TABLE listings (
    listing_id  INT                 PRIMARY KEY IDENTITY (1,1),
    title       NVARCHAR(100)       NOT NULL,
    price_raw   NVARCHAR(100)       NULL,
    price_vnd   BIGINT              NULL,
    area_raw    NVARCHAR(100)       NULL,
    area_m2     FLOAT               NULL,
    address_raw NVARCHAR(500)       NULL,
    district_id INT                 NULL REFERENCES districts(district_id),
    source_url  NVARCHAR(1000)      NULL,
    is_dulicate BIT                 NOT NULL DEFAULT 0,
    scraped_at  DATETIME            NOT NULL DEFAULT GETDATE(),
    updated_at   DATETIME           NULL

);

CREATE INDEX idx_listings_district  ON listings(district_id);
CREATE INDEX idx_listings_scraped   ON listings(scraped_at);
CREATE INDEX idx_listings_updated   ON listings(updated_at);
GO

CREATE TABLE listing_features (
    feature_id      INT             PRIMARY KEY IDENTITY(1,1),
    listing_id      INT             NOT NULL REFERENCES listings(listing_id) ON DELETE CASCADE,
    has_wc          BIT             NOT NULL DEFAULT 0,
    has_ac          BIT             NOT NULL DEFAULT 0,
    has_parking     BIT             NOT NULL DEFAULT 0,
    has_kitchen     BIT             NOT NULL DEFAULT 0,
    has_balcony     BIT             NOT NULL DEFAULT 0,
    has_security    BIT             NOT NULL DEFAULT 0
);

CREATE INDEX idx_features_listing ON listing_features(listing_id);
GO


CREATE TABLE scrape_logs (
    log_id          INT         PRIMARY KEY IDENTITY(1,1),
    run_at          DATETIME   NOT NULL DEFAULT GETDATE(),
    pages_done      INT         NOT NULL DEFAULT 0,
    rows_inserted   INT         NOT NULL DEFAULT 0,
    rows_skipped    INT         NOT NULL DEFAULT 0,
    status          VARCHAR(20) NOT NULL DEFAULT 'running', -- running/success/failed
    error_msg       NVARCHAR(500) NULL
);
GO


CREATE OR ALTER VIEW ml_features AS 
SELECT
    l.listing_id,
    l.price_vnd,
    l.area_m2,
    l.district_id,
    d.name         AS district_name,
    
    CASE
        WHEN l.area_m2 > 0 then CAST(l.price_vnd AS FLOAT) / l.area_m2
        ELSE NULL
    END             AS price_per_m2,

    ISNULL(f.has_wc,        0)      AS has_wc,
    ISNULL(f.has_ac,        0)      AS has_ac,
    ISNULL(f.has_balcony,   0)      AS has_balcony,
    ISNULL(f.has_kitchen,   0)      AS has_kitchen,
    ISNULL(f.has_parking,   0)      AS has_parking,
    ISNULL(f.has_security,  0)      AS has_security,
    ISNULL(f.share_ownership, 0)    AS share_ownership,
    l.scraped_at

FROM listings l
LEFT JOIN districts         d ON l.district_id  = d.district_id
LEFT JOIN listing_features  f ON l.listing_id   = f.listing_id
WHERE l.is_dulicate = 0
    AND l.price_vnd > 0
    AND l.area_m2   > 0;

GO

ALTER TABLE listing_features ADD share_ownership BIT NOT NULL DEFAULT 0;

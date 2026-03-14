import sqlite3
from datetime import datetime, date

conn_layouts = sqlite3.connect('Layouts.db')
layouts_cursor = conn_layouts.cursor()

conn_metadata = sqlite3.connect('Metadata.db')
metadata_cursor = conn_metadata.cursor()

# ── snecko ──────────────────────────────────────────────────────────────
layouts_cursor.execute("""
CREATE TABLE IF NOT EXISTS snecko (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    HeaderRecordType TEXT NOT NULL,
    HeaderProcessDate TEXT NOT NULL,
    HeaderTime TEXT NOT NULL,
    ReferenceNumber TEXT NOT NULL,
    RecordType TEXT NOT NULL CHECK(RecordType = '03'),
    OfficeNumber TEXT NOT NULL,
    Agent TEXT NOT NULL,
    EffectiveDate TEXT NOT NULL CHECK(EffectiveDate != ''),
    TransactionTime TEXT NOT NULL,
    TransactionDate TEXT GENERATED ALWAYS AS (HeaderProcessDate) VIRTUAL,
    FullName TEXT NOT NULL,
    FooterRecordType TEXT NOT NULL CHECK(FooterRecordType = '93'),
    FooterAmount TEXT NOT NULL CHECK(FooterAmount != '' AND FooterAmount NOT GLOB '*[^0-9]*' AND length(FooterAmount) == 12)
)
""")

conn_layouts.commit()

metadata_cursor.execute("""
CREATE TABLE IF NOT EXISTS snecko_column_meta (
    column_name     TEXT    PRIMARY KEY,
    start_pos       INTEGER,
    length          INTEGER,
    validations     TEXT,
    is_decimal      BOOLEAN,
    decimal_pos     INTEGER
)
""")
conn_metadata.commit()

metadata_cursor.executemany("""
INSERT OR IGNORE INTO snecko_column_meta (column_name, start_pos, length, validations, is_decimal, decimal_pos) VALUES (?, ?, ?, ?, ?, ?)
""", [
    ('HeaderRecordType',  0,    2,    None,                              False, None),
    ('HeaderProcessDate', 2,    14,   None,                              False, None),
    ('HeaderTime',        10,   6,    None,                              False, None),
    ('ReferenceNumber',   16,   10,   None,                              False, None),
    ('RecordType',        0,    2,    'FixedValueOf:03',                 False, None),
    ('OfficeNumber',      2,    6,    None,                              False, None),
    ('Agent',             8,    6,    None,                              False, None),
    ('EffectiveDate',     14,   14,   'IsNotEmpty',                      False, None),
    ('TransactionTime',   22,   6,    None,                              False, None),
    ('TransactionDate',   None, None, 'valueRef:HeaderProcessDate',      False, None),
    ('FullName',          43,   30,   None,                              False, None),
    ('FooterRecordType',  0,    2,    'FixedValueOf:93',                 False, None),
    ('FooterAmount',      2,    12,   'IsNotEmpty|ConatinsOnlyCurrency', True,  10),
])
conn_metadata.commit()

# ── snecko_sample1 ──────────────────────────────────────────────────────────────
layouts_cursor.execute("""
CREATE TABLE IF NOT EXISTS snecko_sample1 (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    HeaderRecordType    TEXT NOT NULL CHECK(HeaderRecordType = '01'),
    HeaderProcessDate   TEXT NOT NULL,
    HeaderTime          TEXT NOT NULL,
    HeaderFileId        TEXT,
    RecordType          TEXT NOT NULL CHECK(RecordType = '03'),
    OfficeNumber        TEXT NOT NULL,
    Agent               TEXT NOT NULL,
    ReferenceNumber     TEXT NOT NULL,
    EffectiveDate       TEXT NOT NULL CHECK(EffectiveDate != ''),
    TransactionTime     TEXT NOT NULL,
    TransactionDate     TEXT GENERATED ALWAYS AS (HeaderProcessDate) VIRTUAL,
    FullName            TEXT NOT NULL,
    TransactionAmount   TEXT NOT NULL CHECK(TransactionAmount != ''),
    FooterRecordType    TEXT NOT NULL CHECK(FooterRecordType = '93'),
    FooterAmount        TEXT NOT NULL CHECK(FooterAmount != '')
)
""")
conn_layouts.commit()

metadata_cursor.execute("""
CREATE TABLE IF NOT EXISTS snecko_sample1_column_meta (
    column_name     TEXT    PRIMARY KEY,
    start_pos       INTEGER,
    length          INTEGER,
    validations     TEXT,
    is_decimal      BOOLEAN,
    decimal_pos     INTEGER
)
""")
conn_metadata.commit()

metadata_cursor.executemany("""
INSERT OR IGNORE INTO snecko_sample1_column_meta
    (column_name, start_pos, length, validations, is_decimal, decimal_pos) VALUES (?, ?, ?, ?, ?, ?)
""", [
    ('HeaderRecordType',  0,    2,    'FixedValueOf:01',                  False, None),
    ('HeaderProcessDate', 2,    8,    'IsNotEmpty|DateFormat:YYYYMMDD',   False, None),
    ('HeaderTime',        10,   6,    'TimeFormat:HHMMSS',                False, None),
    ('HeaderFileId',      16,   10,   None,                               False, None),
    ('RecordType',        0,    2,    'FixedValueOf:03',                  False, None),
    ('OfficeNumber',      2,    6,    'Numeric',                          False, None),
    ('Agent',             8,    6,    None,                               False, None),
    ('ReferenceNumber',   14,   12,   None,                               False, None),
    ('EffectiveDate',     26,   8,    'IsNotEmpty|DateFormat:YYYYMMDD',   False, None),
    ('TransactionTime',   34,   6,    None,                               False, None),
    ('TransactionDate',   None, None, 'valueRef:HeaderProcessDate',       False, None),
    ('FullName',          40,   30,   None,                               False, None),
    ('TransactionAmount', 70,   12,   'IsNotEmpty|Numeric',               True,  2),
    ('FooterRecordType',  0,    2,    'FixedValueOf:93',                  False, None),
    ('FooterAmount',      2,    12,   'IsNotEmpty|Numeric|ConatinsOnlyCurrency', True, 2),
])
conn_metadata.commit()

# ── snecko_minimal ───────────────────────────────────────────────────────────────
layouts_cursor.execute("""
CREATE TABLE IF NOT EXISTS snecko_minimal (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    HeaderRecordType    TEXT NOT NULL CHECK(HeaderRecordType = 'HH'),
    HeaderProcessDate   TEXT NOT NULL,
    RecordType          TEXT NOT NULL CHECK(RecordType = '03'),
    ReferenceNumber     TEXT NOT NULL,
    FullName            TEXT NOT NULL,
    TransactionAmount   TEXT,
    FooterRecordType    TEXT NOT NULL CHECK(FooterRecordType = '93'),
    FooterChecksum      TEXT NOT NULL
)
""")
conn_layouts.commit()

metadata_cursor.execute("""
CREATE TABLE IF NOT EXISTS snecko_minimal_column_meta (
    column_name     TEXT    PRIMARY KEY,
    start_pos       INTEGER,
    length          INTEGER,
    validations     TEXT,
    is_decimal      BOOLEAN,
    decimal_pos     INTEGER
)
""")
conn_metadata.commit()

metadata_cursor.executemany("""
INSERT OR IGNORE INTO snecko_minimal_column_meta
    (column_name, start_pos, length, validations, is_decimal, decimal_pos) VALUES (?, ?, ?, ?, ?, ?)
""", [
    ('HeaderRecordType',  0,    2,    'FixedValueOf:HH',                  False, None),
    ('HeaderProcessDate', 2,    8,    None,                               False, None),
    ('RecordType',        0,    2,    'FixedValueOf:03',                  False, None),
    ('ReferenceNumber',   2,    16,   None,                               False, None),
    ('FullName',          18,   40,   None,                               False, None),
    ('TransactionAmount', 58,   10,   'Numeric',                          True,  2),
    ('FooterRecordType',  0,    2,    'FixedValueOf:93',                  False, None),
    ('FooterChecksum',    2,    8,    'MatchesRegex:^[A-F0-9]{8}$',       False, None),
])
conn_metadata.commit()

# ── snecko_variation2 ────────────────────────────────────────────────────────────
layouts_cursor.execute("""
CREATE TABLE IF NOT EXISTS snecko_variation2 (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    HeaderRecordType    TEXT NOT NULL CHECK(HeaderRecordType = '01'),
    HeaderProcessDate   TEXT NOT NULL,
    RecordType          TEXT NOT NULL CHECK(RecordType = '03'),
    BranchCode          TEXT,
    AgentId             TEXT,
    RefNo               TEXT,
    CustomerEmail       TEXT,
    Status              TEXT,
    Currency            TEXT,
    Amount              TEXT NOT NULL CHECK(Amount != ''),
    TransactionDate     TEXT GENERATED ALWAYS AS (HeaderProcessDate) VIRTUAL,
    FreeText            TEXT,
    FooterRecordType    TEXT NOT NULL CHECK(FooterRecordType = '99'),
    FooterTotalCount    TEXT,
    FooterTotalAmount   TEXT NOT NULL CHECK(FooterTotalAmount != '')
)
""")
conn_layouts.commit()

metadata_cursor.execute("""
CREATE TABLE IF NOT EXISTS snecko_variation2_column_meta (
    column_name     TEXT    PRIMARY KEY,
    start_pos       INTEGER,
    length          INTEGER,
    validations     TEXT,
    is_decimal      BOOLEAN,
    decimal_pos     INTEGER
)
""")
conn_metadata.commit()

metadata_cursor.executemany("""
INSERT OR IGNORE INTO snecko_variation2_column_meta
    (column_name, start_pos, length, validations, is_decimal, decimal_pos) VALUES (?, ?, ?, ?, ?, ?)
""", [
    ('HeaderRecordType',  0,    2,    'FixedValueOf:01',                          False, None),
    ('HeaderProcessDate', 2,    14,   'DateTimeFormat:YYYYMMDDHHMMSS',            False, None),
    ('RecordType',        0,    2,    'FixedValueOf:03',                          False, None),
    ('BranchCode',        2,    5,    None,                                       False, None),
    ('AgentId',           7,    5,    None,                                       False, None),
    ('RefNo',             12,   10,   None,                                       False, None),
    ('CustomerEmail',     22,   40,   'MatchesRegex:^\\S+@\\S+\\.\\S+$',          False, None),
    ('Status',            62,   1,    'AllowedValues:A,S,C',                      False, None),
    ('Currency',          63,   3,    'AllowedValues:USD,INR,EUR',                False, None),
    ('Amount',            66,   12,   'IsNotEmpty|Numeric',                       True,  2),
    ('TransactionDate',   None, None, 'valueRef:HeaderProcessDate',               False, None),
    ('FreeText',          78,   50,   None,                                       False, None),
    ('FooterRecordType',  0,    2,    'FixedValueOf:99',                          False, None),
    ('FooterTotalCount',  2,    6,    'Numeric',                                  False, None),
    ('FooterTotalAmount', 8,    14,   'IsNotEmpty|Numeric',                       True,  2),
])
conn_metadata.commit()

# ── snecko_extended ──────────────────────────────────────────────────────────────
layouts_cursor.execute("""
CREATE TABLE IF NOT EXISTS snecko_extended (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    HeaderRecordType    TEXT NOT NULL CHECK(HeaderRecordType = 'HD'),
    HeaderProcessDate   TEXT NOT NULL,
    HeaderSequence      TEXT,
    RecordType          TEXT NOT NULL CHECK(RecordType = '03'),
    LineNumber          TEXT,
    OfficeNo            TEXT,
    AgentCode           TEXT,
    ReferenceNumber     TEXT,
    CustomerName        TEXT,
    TransactionDate     TEXT GENERATED ALWAYS AS (HeaderProcessDate) VIRTUAL,
    NetAmount           TEXT NOT NULL CHECK(NetAmount != ''),
    TaxAmount           TEXT,
    VATPercent          TEXT,
    TotalAmount         TEXT NOT NULL CHECK(TotalAmount != ''),
    Currency            TEXT,
    ChecksumRef         TEXT GENERATED ALWAYS AS (ReferenceNumber) VIRTUAL,
    FooterRecordType    TEXT NOT NULL CHECK(FooterRecordType = 'FT'),
    FooterCount         TEXT,
    FooterAmount        TEXT NOT NULL CHECK(FooterAmount != '')
)
""")
conn_layouts.commit()

metadata_cursor.execute("""
CREATE TABLE IF NOT EXISTS snecko_extended_column_meta (
    column_name     TEXT    PRIMARY KEY,
    start_pos       INTEGER,
    length          INTEGER,
    validations     TEXT,
    is_decimal      BOOLEAN,
    decimal_pos     INTEGER
)
""")
conn_metadata.commit()

metadata_cursor.executemany("""
INSERT OR IGNORE INTO snecko_extended_column_meta
    (column_name, start_pos, length, validations, is_decimal, decimal_pos) VALUES (?, ?, ?, ?, ?, ?)
""", [
    ('HeaderRecordType',  0,    2,    'FixedValueOf:HD',                              False, None),
    ('HeaderProcessDate', 2,    14,   'DateTimeFormat:YYYYMMDDHHMMSS',                False, None),
    ('HeaderSequence',    16,   6,    None,                                           False, None),
    ('RecordType',        0,    2,    'FixedValueOf:03',                              False, None),
    ('LineNumber',        2,    4,    'Numeric',                                      False, None),
    ('OfficeNo',          6,    6,    None,                                           False, None),
    ('AgentCode',         12,   6,    None,                                           False, None),
    ('ReferenceNumber',   18,   12,   None,                                           False, None),
    ('CustomerName',      30,   30,   None,                                           False, None),
    ('TransactionDate',   None, None, 'valueRef:HeaderProcessDate',                   False, None),
    ('NetAmount',         60,   12,   'IsNotEmpty|Numeric',                           True,  2),
    ('TaxAmount',         72,   10,   'Numeric',                                      True,  2),
    ('VATPercent',        82,   3,    'Numeric|Range:0-100',                          True,  2),
    ('TotalAmount',       85,   14,   'IsNotEmpty|Numeric|Computed:NetAmount+TaxAmount', True, 2),
    ('Currency',          99,   3,    'AllowedValues:INR,USD,EUR',                    False, None),
    ('ChecksumRef',       102,  8,    'valueRef:ReferenceNumber',                     False, None),
    ('FooterRecordType',  0,    2,    'FixedValueOf:FT',                              False, None),
    ('FooterCount',       2,    8,    'Numeric',                                      False, None),
    ('FooterAmount',      10,   16,   'IsNotEmpty|Numeric',                           True,  2),
])
conn_metadata.commit()

# ── inspect ────────────────────────────────────────────────────────────────────
layouts_cursor.execute("""
SELECT name, sql FROM sqlite_master WHERE type='table'
""")
for name, sql in layouts_cursor.fetchall():
    print(f"Table: {name}\nSchema: {sql}\n")
    print(type(sql))


layouts_cursor.execute("PRAGMA table_info(snecko);")
print(layouts_cursor.fetchall())

metadata_cursor.execute('SELECT * FROM snecko_column_meta;')
print(metadata_cursor.fetchall())

conn_layouts.close()
conn_metadata.close()


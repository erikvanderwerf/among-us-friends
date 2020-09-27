CREATE TABLE meta (
    hash  TEXT NOT NULL
);

CREATE TABLE users (
    rowid    INTEGER PRIMARY KEY,
    uuid     TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password TEXT
);

CREATE TABLE lobbies (
    rowid  INTEGER PRIMARY KEY,
    uuid   TEXT UNIQUE NOT NULL,
    title  TEXT NOT NULL,
    anyone INTEGER NOT NULL CHECK (anyone IN (0,1))
);

CREATE TABLE rooms (
    rowid     INTEGER PRIMARY KEY,
    lobby_id  INTEGER NOT NULL,
    uuid      TEXT UNIQUE NOT NULL,
    title     TEXT NOT NULL,

    FOREIGN KEY (lobby_id) REFERENCES lobbies (rowid)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

CREATE TABLE games (
    rowid    INTEGER PRIMARY KEY,
    room_id  INTEGER NOT NULL,
    owner    INTEGER NOT NULL,
    uuid     TEXT UNIQUE NOT NULL,
    title    TEXT NOT NULL,

    FOREIGN KEY (room_id) REFERENCES rooms (rowid)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    FOREIGN KEY (owner) REFERENCES users (rowid)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

CREATE TABLE matches (
    rowid    INTEGER PRIMARY KEY,
    room_id  INTEGER NOT NULL,
    owner    INTEGER NOT NULL,
    host     INTEGER NOT NULL,
    uuid     TEXT NOT NULL,
    title    TEXT NOT NULL,
    end_at   TEXT NOT NULL,
    players  INTEGER NOT NULL,
    mode     TEXT NOT NULL,
    map      TEXT NOT NULL,
    result   TEXT NOT NULL,
    network  TEXT NOT NULL,

    FOREIGN KEY (room_id) REFERENCES rooms (rowid)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    FOREIGN KEY (owner) REFERENCES users (rowid)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    FOREIGN KEY (host) REFERENCES users (rowid)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

CREATE TABLE results (
    rowid     INTEGER PRIMARY KEY,
    match_id  INTEGER NOT NULL,
    user_id   INTEGER NOT NULL,
    uuid      TEXT NOT NULL,
    r_time    TEXT NOT NULL,
    platform  TEXT NOT NULL,
    color     TEXT NOT NULL,
    imposter  INTEGER NOT NULL CHECK (imposter IN (0,1)),
    victory   INTEGER NOT NULL CHECK (victory IN (0,1)),
    death     INTEGER NOT NULL CHECK (death IN (0,1)),
    comments  TEXT,

    FOREIGN KEY (match_id) REFERENCES matches (rowid)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    FOREIGN KEY (user_id) REFERENCES users (rowid)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    UNIQUE(match_id, user_id)
    UNIQUE(match_id, color)
);

## RIFT Shard First parser

Takes the data dumps from http://webcdn.triongames.com/addons/assets/
(Rift_Discoveries_*.zip) and parses all the shard firsts in to a SQL database

## Use

Set up your MySQL server; add a user and give it a password; create a database.

Create the table "firsts" as below.

Copy `config.txt.dist` to `config.txt` and fill in the parameters.

Run `getdata.sh`. This will download the Discoveries zip and parse the XML files
in to the database. Schedule it in cron (every day would be the maximum).

## Requirements

* Python 3.5
* asyncio
* aiomysql
* lxml
* PCRE-enabled grep
* nocache, nice, ionice

## SQL table

    CREATE TABLE `firsts` (
     `Id` varchar(32) COLLATE utf8mb4_bin NOT NULL,
     `Kind` varchar(20) COLLATE utf8mb4_bin NOT NULL,
     `What` varchar(96) COLLATE utf8mb4_bin NOT NULL,
     `Player` varchar(32) COLLATE utf8mb4_bin NOT NULL,
     `Shard` varchar(32) COLLATE utf8mb4_bin NOT NULL,
     `Guild` varchar(128) COLLATE utf8mb4_bin DEFAULT NULL,
     `Stamp` datetime DEFAULT NULL,
      PRIMARY KEY (`Id`,`What`,`Player`,`Shard`),
      KEY `player` (`Player`),
      KEY `guild` (`Guild`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin

## RIFT Shard First parser

Takes the data dumps from http://webcdn.triongames.com/addons/assets/
(Rift_Discoveries_*.zip) and parses all the shard firsts in to a SQL database

## Requirements

* Python 3.5
* asyncio
* aiomysql
* lxml

## SQL table

    CREATE TABLE `firsts` (    `Id` varchar(32) NOT NULL,    `Kind` varchar(20) NOT NULL,    `What` varchar(96) NOT NULL,   `Player` varchar(32) NOT NULL,    `Shard` varchar(32) NOT NULL,    `Guild` varchar(128) DEFAULT NULL,    `Stamp` datetime DEFAULT NULL,    PRIMARY KEY (`Id`,`What`,`Player`,`Shard`) ) ENGINE=InnoDB DEFAULT CHARSET=utf8;

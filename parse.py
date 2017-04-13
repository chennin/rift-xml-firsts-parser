#!/usr/bin/env python3.5
#Copyright 2017 Christopher Henning

#Permission is hereby granted, free of charge, to any person obtaining a copy of
#this software and associated documentation files (the "Software"), to deal in
#the Software without restriction, including without limitation the rights to
#use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
#of the Software, and to permit persons to whom the Software is furnished to do
#so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
#FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
#COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
#IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
#CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import re
import os
import sys
from lxml import etree
import asyncio
import aiomysql
import pymysql.cursors
from pymysql.err import (Error, OperationalError)
from pathlib import Path
from six.moves import configparser

# Read config file in
mydir = os.path.dirname(os.path.realpath(__file__))
configReader = configparser.RawConfigParser()
configFile = Path(mydir + "/config.txt")
if configFile.is_file():
  configReader.read(mydir + "/config.txt")
else:
  print("Error: config file {0} not found.".format(configFile.as_posix()), file=sys.stderr)
  sys.exit(1)

config = {}
try:
  for var in ["dbuser", "dbhost", "dbpass", "db"]:
    config[var] = configReader.get("SQL",var)
except configparser.NoOptionError:
  print("Error: required configuration option {0} not found.".format(var), file=sys.stderr)
  sys.exit(2)

firsttypes = [
  { 'kind': "Achievement",        'firsttag': "FirstCompletedBy", 'nametag': "Name",        'idtag': "Id" },
  { 'kind': "ArtifactCollection", 'firsttag': "FirstCompletedBy", 'nametag': "Name",        'idtag': "Id" },
  { 'kind': "Item",               'firsttag': "FirstLootedBy",    'nametag': "Name",        'idtag': "ItemKey" },
  { 'kind': "NPC",                'firsttag': "FirstKilledBy",    'nametag': "PrimaryName", 'idtag': "Id" },
  { 'kind': "Quest",              'firsttag': "FirstCompletedBy", 'nametag': "Name",        'idtag': "QuestId" },
  { 'kind': "Recipe",             'firsttag': "FirstLearnedBy",   'nametag': "Name",        'idtag': "Id" },
]

# Connect to DB and fire off individual file parsers
async def parseall(loop):
  try:
    pool = await aiomysql.create_pool(minsize=6, host=config['dbhost'], user=config['dbuser'], password=config['dbpass'], db=config['db'], charset='utf8mb4', loop=loop)
  except pymysql.err.OperationalError as e:
    print("Error connecting to database: {0}".format(e), file=sys.stderr)
    sys.exit(3)

  parsefuncs = []
  for first in firsttypes:
    parsefuncs.append( parse(first, (await pool.acquire())) )

  # Start parsing all
  await asyncio.gather( *parsefuncs )

  # Clean up
  pool.close()
  pool.wait_closed()

# Individual file parsing function
async def parse(first, conn):
  cursor = await conn.cursor()
  # Iterative parser so we don't run out of memory
  context = etree.iterparse("{0}s.xml".format(first['kind']), events=('end',))
  toadd = []
  sql = "INSERT IGNORE INTO firsts (Id, Kind, What, Player, Shard, Guild, Stamp) VALUES (%s, %s, %s, %s, %s, %s, %s)";

  for event, elem in context:
    # <Item>, <Quest>, etc
    if elem.tag == first['kind']:
      # ID number for this
      iid = elem.find(first['idtag']).text

      # Friendly (English) name for this
      what = ""
      whatelem = elem.find(first['nametag']).find("English")
      if whatelem is not None:
        what = whatelem.text
      if what == "":
        what = "-MISSING-NAME-"

      # Find the list of who got it first
      firsts = elem.find(first['firsttag'])
      # Then parse that list
      for shards in list(firsts):
        # Remove prefix, eg Live_EU_Brisesol => Brisesol
        shard = re.sub("Live_.._", "",shards.tag)

        guildelem = shards.find("Guild")
        guild = ""
        if guildelem is not None:
          guild = guildelem.text	

        player = shards.find("Name").text
        date = shards.find("Date").text
        # Remove "T" from the provided datestamps, e.g. 2014-02-19T23:08:32
        date = re.sub("T", " ", date)

        toadd.append( (iid, first['kind'], what, player, shard, guild, date) )
        # Insert thousands of rows at once for massive speedup
        if len(toadd) > 2000:
          await cursor.executemany(sql, toadd)
          toadd = []

      # Free the just-parsed XML nodes to keep memory usage low
      elem.clear()
      while elem.getprevious() is not None:
        del elem.getparent()[0]

  # Execute any last parsed nodes
  if len(toadd) > 0:
    cursor.executemany(sql, toadd)
  # Commit once per file
  await conn.commit()
  # Clean up
  await cursor.close()
  conn.close()
#  print("Done {0}\n".format(first['kind']))

loop = asyncio.get_event_loop()
loop.run_until_complete(parseall(loop))

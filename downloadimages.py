import urllib2
import urllib
from PIL import Image
import os
import sqlite3 as sql
def database_command(command, *args): #*Args are to let assign optional arguments
    con = sql.connect('/Users/PeterPan/Documents/gameapp/userslist.db') # Establishing a connection with DB
    cur = con.cursor()
    cur.execute(command, args)
    rows = cur.fetchall() #Create a variable containing a DISCTIONARY with all data from command
    con.commit() # Save changes made to the DB
    con.close() # Close connection
    return rows
for row in database_command("select * from games"):
    fullfilename = os.path.join("/Users/PeterPan/Documents/gameapp/img/", row[1]+".jpg")
    urllib.urlretrieve("http://www.rebel.pl/"+row[6], fullfilename)

#copyright Jonathan Watkins (c) 2017
#all rights reserved

#SmartThings - Hayward Pool Bridge
#Bottle webapp

import bottle 
import json
import threading
import time
import sqlite3
import prologic_pool_system
import datetime

sth_version = "1.0.0"
sth_updated = "2018-02-19"

webapp = bottle.Bottle()

@webapp.route("/")
def index_page():
    return bottle.static_file("index.html", root="/home/pi/python/web_bottle/static")

@webapp.route("/version")
def version():
    v = { "version": sth_version, "last_updated": sth_updated }
    bottle.response.content_type="application/json"
    return json.dumps(v)
          
@webapp.route("/status")
def status():
    #todo - auth?
    lastStatus = poolsystem.getStatus()

    r = { "last_updated": datetime.datetime.now().isoformat(" "),
          "cache_reliable": False,
          "pool": (lastStatus["led"].Pool if "led" in lastStatus else False),
          "filter": (lastStatus["led"].Filter if "led" in lastStatus else False),
          "lights": (lastStatus["led"].Lights if "led" in lastStatus else False),
          "check_system": (lastStatus["led"].CheckSystem if "led" in lastStatus else False),
          "service_indicator": (lastStatus["led"].Service if "led" in lastStatus else False),
          "super_chlorinate": (lastStatus["led"].SuperChlorinate if "led" in lastStatus else False),
          "system_off": (lastStatus["led"].SystemOff if "led" in lastStatus else False),

          "salt_level": (lastStatus["salt_level"]["value"] if "salt_level" in lastStatus else "?"),
          "pool_chlorinator": (lastStatus["pool_chlorinator"]["value"] if "pool_chlorinator" in lastStatus else "?"),
          "air_temp": (lastStatus["air_temp"]["value"] if "air_temp" in lastStatus else -1),
          "pool_temp": (lastStatus["pool_temp"]["value"] if "pool_temp" in lastStatus else -1),
          "temp_unit": (lastStatus["air_temp"]["unit"] if "air_temp" in lastStatus else "?"),
          
          "messages": (lastStatus["messages"].to_array() if "messages" in lastStatus else [ ] )
          }
    
    bottle.response.content_type="application/json"
    return json.dumps(r)

@webapp.route("/toggle/lights")
def toggleLights():
    #todo auth
    poolsystem.pressKey_Lights()
    time.sleep(1) #give 1 second to let the command carry through and get back status
    bottle.redirect("/status")

@webapp.route("/toggle/filter")
def toggleLights():
    #todo auth
    poolsystem.pressKey_Filter()
    time.sleep(1) #give 1 second to let the command carry through and get back status
    bottle.redirect("/status")

poolsystem = prologic_pool_system.ProLogicSystem("/dev/ttyAMA0", None, None)
poolsystem.start()
statusLock = threading.Lock()
lastStatus = { }

def query_status():
    with statusLock:
        #queries the hayward pool system to get all the relevent status messages
        # and LED indicators and updates within the sqlite db
        lastStatus = poolsystem.getStatus()

        

#background polling
pollEvent = threading.Event()
pollEvent.clear()

def poll_task():
    while 1:
        query_status();
        #wait on timer or request to start again
        pollEvent.wait(timeout=30)
        pollEvent.clear() #reset the event


#bgthread = threading.Thread(target=poll_task)
#bgthread.setDaemon(True)
#bgthread.start()

#run webapp
try:
    print("WebApp - Starting")
    webapp.run(reloader=False, debug=False, host='0.0.0.0', port=8080, server='paste')
    webapp.close()
    print("WebApp - Shutdown")
except KeyboardInterrupt:
    print("");
    print("Closing")
except:
    raise
finally:
    print("WebApp - Cleaning up...")
    poolsystem.end()
    print("WebApp - Cleaned up")



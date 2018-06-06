# hayward-controller
Hayward Pool Controller via RS485 Serial

Simple REST API interface to broker commands to a serial port communicating over RS-485 to the "remote" ports of the Hayward Goldline Pool Controllers

## Background (for those curious)
I love home automation and when I purchased my home in 2015, I was pleased to discover that my new home's pool came with a pool controller which could switch on the filter, lights, and some high voltage auxillary relays. Additionally, it has sensors for pool temperature, air temperature, and salt levels (the pool is chlorinated via a SWG = Salt Water Generator). The remote port was unused and I immediately set to work locating a remote unit which I could place in the home (some 50+ft from the control unit) so I could turn on the light for night swimming on my way out the door and check the water temp). The remote unit was simple enough and connected to the control unit by 4 wires. The manual also mentioned that I could attach multiple remotes and that reminded me of ring networks. It took a little <del>Googling</del> sluething I discovered an RS232 adapter for the same ring network that would broker RS232 commands into the ring for home automation. Not wanting to spend more money on the adapter, I spend a short amount of time researching network protocols that would allow multiple clients on a 2 wire connection (the other 2 of the 4 provided GND and V+). This produced a short list with RS485 at the top. A $15 adapter on a large internet retailer confirmed for me that the communication was in fact performed between the client (remote) and server (controller) via RS485. The RS232 manual contained the bulk of the command instructions but there are a few subtle differences between how RS485 sends and receives vs RS232. Another quick search found that a RS485 shield was available for my spare Pi 3. And this is where this project began. 

## Current features
This is absolutely still an alpha and have yet to even complete a release - so feel free to use only as a reference for now.

### What works:
- Light on/off
- Lights status
- Salt Level parsing
- Air Temp parsing
- Water Temp parsing
- Simple HTML5 UI

### Known Bugs:
- Filter toggle does not work - likely a bit off here or there - need to debug

## Future plans
- Amazona Alexa Skill
  - Home Automation Device Hooks
- Smartthings Device Hook
  - Sensor data (Air Temp, Water Temp, Salt Levels)
  - Switch: Lights
  - Switch: Filter
  

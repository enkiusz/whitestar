#!/usr/bin/env python2

import sys, time, subprocess, threading
from struct import pack
import kismetclient

led_device='/dev/serial/by-id/pci-FTDI_USB__-__Serial-if00-port0'

print("Using monitor '%s'" % (led_device))

mon = open(led_device, "w")

# Reference: http://pop.fsck.pl/hardware/random-led-board/
def makepkt(**leds):

    print("LED packet: led1='%s' led2='%s' led3='%s' led4='%s', led5='%s' led6='%s' led7='%s' led8='%s' led9='%s'" %
           (leds.get('led1', ''), leds.get('led2', ''), leds.get('led3', ''), leds.get('led4',''), leds.get('led5', ''),
           leds.get('led6', ''), leds.get('led7', ''), leds.get('led8', ''), leds.get('led9', '')) )

    byte1=0b00000000
    byte2=0b01000000
    byte3=0b10000000

    offs=0
    for k in ('led1', 'led2', 'led3'):
        v = leds.get(k,'')
        if v == 'green':
            byte1 |= (0x01 << offs)
        if v == 'yellow':
            byte1 |= (0x01 << (offs+1))
        offs += 2

    offs=0
    for k in ('led4', 'led5', 'led6'):
        v = leds.get(k,'')
        if v == 'green':
            byte2 |= (0x01 << offs)
        if v == 'yellow':
            byte2 |= (0x01 << (offs+1))
        offs += 2

    offs=0
    for k in ('led7', 'led8', 'led9'):
        v = leds.get(k,'')
        if v == 'green':
            byte3 |= (0x01 << offs)
        if v == 'yellow':
            byte3 |= (0x01 << (offs+1))
        offs += 2

    return pack('BBB', byte1, byte2, byte3)

def onoff_blink_next(state):
    if state == '':
	return 'yellow'
    else:
	return ''

def storage_state():
    # Check if USB device is present
    try:
	rv = subprocess.call(['lsusb', '-d', '152d:2336'], stdout=open('/dev/null','w'))
	if rv == 0:
	    return 'green'
	else:
	    return ''
    except:
	return ''

kismet_server = 'localhost'
kismet_port = 2501

sources = {
	'39ed09aa-2dcd-4eab-b460-781de88f79d6': {
		'interface': 'alfa',
		'state': '',
		'lastseen': 0,
	},
	'e8d964d0-9409-408f-a1d7-01e841bae7ed': {
		'interface': 'sr71',
		'state': '',
		'lastseen': 0,
	},
	'fb187219-afd4-4be8-871a-220d16fb5cb0': {
		'interface': 'chibi',
		'state': '',
		'lastseen': 0
	}
}

def purge_sources():
    for uuid in sources:
	if (time.time() - sources[uuid]['lastseen']) > 10:
		# Source is gone if not receiving updates for 10 seconds
		sources[uuid]['state'] = ''

def update_source_state(client,uuid,error):
    if uuid in sources:
	sources[uuid]['lastseen'] = time.time()
	if error == 0:
		sources[uuid]['state'] = 'green'
	else:
		sources[uuid]['state'] = 'yellow'

kismet_lastseen = 0
def update_time(client,timesec):
    global kismet_lastseen

    kismet_lastseen = int(timesec)
    print("TIME time='%d'" % (kismet_lastseen))

def kismet_connection_state():
    if time.time() - kismet_lastseen < 5:
	return 'green'
    else:
	return ''

def log_status(client,text,flags):
    print("STATUS flags='%s' text='%s'" % (flags, text))

def log_critfail(client,id,time,message):
    print("CRITFAIL id='%s' time='%s' message='%s'" % (id,time,message))

def log_error(client,cmdid,text):
    print("ERROR cmdid='%s' text='%s'" % (cmdid,text))

def log_terminate(client,**kwargs):
    print("TERMINATE text='%s'" % (kwargs))

gps_fix = ''
def update_gps_state(client,fix):
    global gps_fix

    fix=int(fix)
    if fix == 3:
	gps_fix = 'green'
    elif fix > 0:
	gps_fix = 'yellow'
    else:
	gps_fix = ''
	print("GPS fix='%d'" % (fix))

class MonitorClient(threading.Thread):

    def run(self):
	global running
	while True:
	    try:
		print("Connecting to kismet server on '%s:%d'" % (kismet_server, kismet_port))

		k = kismetclient.Client((kismet_server, kismet_port))

		k.register_handler('TIME', update_time)
		k.register_handler('GPS', update_gps_state)
		k.register_handler('SOURCE', update_source_state)
		# Debugging
		k.register_handler('STATUS', log_status)
		k.register_handler('CRITFAIL', log_critfail)
		k.register_handler('ERROR', log_error)
		k.register_handler('TERMINATE', log_terminate)
		while True:
	    	    k.listen()
	    except Exception as e:
		print("Caught exception in kismet monitor thread: %s" % (e))
		running = False # Break main loop
		return

t = MonitorClient()
t.start()

mon.write(makepkt())
mon.flush()

watchdog = 'green'
running = True
while running:

	watchdog = onoff_blink_next(watchdog)

	purge_sources()
	mon.write(makepkt(led2=watchdog,
	    led3=kismet_connection_state(),
	    led4=gps_fix,
	    led5=sources['39ed09aa-2dcd-4eab-b460-781de88f79d6']['state'],
	    led6=sources['e8d964d0-9409-408f-a1d7-01e841bae7ed']['state'],
	    led7=sources['fb187219-afd4-4be8-871a-220d16fb5cb0']['state'],
	    led8=storage_state()
	    ))
        mon.flush()
        time.sleep(0.5)


mon.write(makepkt())
mon.flush()

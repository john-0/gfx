#!/usr/bin/env python

import pygatt
import sys, getopt

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timedelta
import httplib, urllib
import SimpleHTTPServer 
import SocketServer 
import threading
import math
import time
import socket

PORT = 8000 
FAKE_GF = False
DEBUG = False
NAME = "Grain"
SERVICE = "0000cdd0-0000-1000-8000-00805f9b34fb"
WRITE = "0003cdd2-0000-1000-8000-00805f9b0131"
NOTIFY = "0003CDD1-0000-1000-8000-00805F9B0131"

PUSHOVER_APP_KEY = None
PUSHOVER_USER_KEY = None

STATUS_SCANNING = 0
STATUS_CONNECTING = 1
STATUS_DISCONNECTED = 2
STATUS_ERROR = 3
STATUS_CONNECTED = 100

pageHead = '''
    <html>
    <head>
        <link rel="stylesheet" href="gfx.css"/>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script>
            var paused = false;
            var skip = false;
            function refresh() {
                if (paused)
                    return;
                if (skip) {
                    skip = false;
                    return;
                }
                var xhttp = new XMLHttpRequest();
                xhttp.onreadystatechange = function() {
                    if (this.readyState == 4 && this.status == 200 && !skip && !paused) {
                        document.getElementById("page-content").innerHTML = this.responseText;
                        initTimerSelects();
                    }
                };
                xhttp.open("POST", "refresh", true);
                xhttp.send();
            }
            function sendAction(action) {
                var xhttp = new XMLHttpRequest();
                xhttp.open("POST", "action/" + action, true);
                xhttp.onreadystatechange = function() {
                    if (this.readyState == 4 && this.status == 200)
                        refresh();
                };            
                xhttp.send();
            }
            function initTimerSelects() {
                var hours = document.getElementById('timer-hours');
                if (!hours || !hours.options)
                    return;
                hours.options = []
                for (var i = 0; i <= 24; i++)
                    hours.options[i] = new Option(i,i)
                hours.value = 0;
                var mins = document.getElementById('timer-minutes');
                mins.options = []
                for (var i = 0; i <= 59; i++)
                    mins.options[i] = new Option(i,i)
                mins.value = 0
            }
            document.addEventListener("DOMContentLoaded", function(event) { 
                initTimerSelects();
                setInterval(refresh, 1000);
            });
            
        </script>
    </head>
    <body>
    <div class="content" id="page-content">
'''

pageCSS = '''

    body { 
        margin: 0px; 
        font-family: "Roboto", "Helvetica Neue", sans-serif; 
        background-color: #f5f5f5;
    }

    .footer {
        padding: 5px;
        font-weight: 400;
        text-align: center;
        width: 100%;
        z-index: 10;
        position: fixed;
        left: 0;
        bottom: 0;
    }

    .footer-0 {
        background-color: #007bff;
        color: white;
    }

    .footer-1 {
        background-color: #ffc107;
        color: black;
    }

    .footer-2, .footer-3 {
        background-color: #b71c1c;
        color: white;
    }    

    .footer-100 {
        background-color: #28a745;
        color: white;
    }

    .temperature-container {
        padding-top: 50px;
        padding-bottom: 50px;
        background-color: #263238;
        color: #ffffff;
        text-align: center;
    }

    .toggle-container, .timer-container {
        padding-top: 20px;
        padding-bottom: 20px;
        text-align: center;
        font-weight: 250;
    }

    .countdown-container {
        padding-top: 50px;
        padding-bottom: 50px;
        background-color: #b0bec5;
        color: #263238;
        text-align: center;
        margin-top: 20px;
    }

    .countdown-title {
        font-size: 150%
    }

    .countdown {
        margin-bottom: 20px;
        font-size: 400%;
        font-weight: 600;
    }

    .timer-container {
        padding-top: 30px;
    }

    .temperature-value-container, .toggle-value-container, .timer-button-container {
        width: 49%; 
        max-width: 250px; 
        display:inline-block;
    }

    .temperature-value {
        text-align: center;
        font-size:  45px;
        font-weight: 500;
    }

    .temperature-value sup {
        font-size: 50%;
    }

    .temperature-desc {
        text-align: center;
        font-size:  16px;
        font-weight: 250;
    }

    .heating {
        color: #ffc107;
    }

    .temperature-controls {
        text-align: center;
	    padding-top: 20px;
    }

    .temperature-controls a {
        font-size: 30px;
        color: black;
        font-weight: 300;
        font-style: normal;
        padding: 20px;
        text-decoration: none;
    }

    .disconnect-button {
        position: absolute;
        top: 0;
        right: 0;
        padding: 10px;
        background-color: #b71c1c;
        color: white;
        font-weight: bold;
        font-size: 75%;
        cursor: pointer;
    }

    .toggle-desc {
        margin-bottom: 15px;
    }

    .modal-contents h1 {
        font-weight: 300;
    }

    .outline-button, .outline-button-small {
        background: transparent;
        border: 2px solid black;
        padding: 15px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 115%;
    }

    .outline-button-small {
        font-weight: 400;
        font-size: 100%;
    }

    .modal-contents button {
        color: #3880ff;
        background-color: white;
        border: none;
        padding: 15px 32px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        cursor: pointer;
        font-weight: 500;        
    }

    .modal-contents input {
        margin-left: 0;
        margin-right: 0;
        margin-top: 5px;
        margin-bottom: 5px;
        border-bottom: 1px solid #d9d9d9;
        color: #000);
        outline: none;
        padding-left: 0;
        padding-right: 0;
        padding-top: 10px;
        padding-bottom: 10px;
        width: 100%;
        border: 0;
        background: inherit;
        font: inherit;
        -webkit-box-sizing: border-box;
        box-sizing: border-box;
        border-bottom: 1px solid #d9d9d9;
        margin-bottom: 20px; 
    }

    .not-connected-container {
        max-width: 500px;
        text-align: center;
        margin: auto;
        padding-top: 25vh;
    }

    .connect-warning {
        margin-top: 50px;
        font-weight: 300;
        font-size: 125%;
        text-align: justify;
        padding-left: 20px;
        padding-right: 20px;
    }

    .connecting-warning {
        font-weight: 200;
        font-size: 300%;
        text-align: center;
    }

    /* Popup box BEGIN */
    .modal-background{
        background:rgba(0,0,0,.4);
        cursor:pointer;
        display:none;
        height:100%;
        position:fixed;
        text-align:center;
        top:0;
        width:100%;
        z-index:10000;
    }
    .modal-background .modal-helper {
        display:inline-block;
        height:100%;
        vertical-align:middle;
    }
    .modal-background > div {
        background-color: #fff;
        box-shadow: 10px 10px 60px #555;
        display: inline-block;
        height: auto;
        max-width: 551px;
        min-height: 100px;
        vertical-align: middle;
        width: 60%;
        position: relative;
        border-radius: 8px;
        padding: 15px 5%;
    }
    
    .switch {
        position: relative;
        display: inline-block;
        width: 60px;
        height: 34px;
    }

    .switch input {
        opacity: 0;
        width: 0;
        height: 0;
    }

    .slider {
        position: absolute;
        cursor: pointer;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: #ccc;
        -webkit-transition: .4s;
        transition: .4s;
    }

    .slider:before {
        position: absolute;
        content: "";
        height: 26px;
        width: 26px;
        left: 4px;
        bottom: 4px;
        background-color: white;
        -webkit-transition: .4s;
        transition: .4s;
    }

    input:checked + .slider.green {
        background-color: #28e070;
    }

    input:focus + .slider.green {
        box-shadow: 0 0 1px #28e070;
    }

    input:checked + .slider.red {
        background-color: #f25454;
    }

    input:focus + .slider.red {
        box-shadow: 0 0 1px #f25454;
    }

    input:checked + .slider:before {
        -webkit-transform: translateX(26px);
        -ms-transform: translateX(26px);
        transform: translateX(26px);
    }

    /* Rounded sliders */
    .slider.round {
    border-radius: 34px;
    }

    .slider.round:before {
    border-radius: 50%;
    }

    select {
        padding: 10px;
        padding-right: 5px;
        font-size: 115%;
        font-size: 16px;
        border: 1px solid #CCC;
        text-align: center;
        -webkit-appearance: none;
        -moz-appearance: none;
        appearance: none;
    }

    .blink {
        -webkit-animation: blink 1s step-end infinite;
        -moz-animation: blink 1s step-end infinite;
        -o-animation: blink 1s step-end infinite;
        animation: blink 1s step-end infinite;
    }

    @-webkit-keyframes blink {
        67% { opacity: 0 }
    }

    @-moz-keyframes blink {
        67% { opacity: 0 }
    }

    @-o-keyframes blink {
        67% { opacity: 0 }
    }

    @keyframes blink {
        67% { opacity: 0 }
    }

    progress {
        margin-top: 40px;
        -webkit-appearance: none;
        appearance: none;
        height: 30px;
        border: 2px solid black;
        max-width: 500px;
        background: transparent;
        width: 90%;
    }

    progress[value]::-webkit-progress-bar {
        background-color: transparent;
    }

    progress::-moz-progress-bar {
        background-color: black;
    }

    progress[value]::-webkit-progress-value {
        background-color: black;
    }

    *:focus {
        outline: none;
    }

}
'''

pageTemperature = '''
<div class="temperature-container">
    <div class="temperature-value-container %(currentTempClass)s">
        <div class="temperature-desc">CURRENT</div>
        <div class="temperature-value">%(current).1f<sup>&deg;%(unit)s</sup></div>
    </div>
    <div class="temperature-value-container">
        <div class="temperature-desc">TARGET</div>
        <div class="temperature-value">%(target)d<sup>&deg;%(unit)s</sup></div>
    </div>
</div>
'''

pageControls = '''
<div class="temperature-controls">
	<a href="#" onclick="sendAction('tempDown'); return false;">&#x2014;</a>
	<a href="#" onclick="paused = true; document.getElementById('select-temp-modal').style.display = 'block'; return false;">SET</a>
	<a href="#" onclick="sendAction('tempUp');" return false;>+</a>
</div>
<div class="toggle-container">
    <div class="toggle-value-container">
	<div class="toggle-desc">HEAT</div>
	<label class="switch">
	  <input type="checkbox" %(checkedHeat)s onchange="skip = true; sendAction('heat');">
	  <span class="slider red round"></span>
	</label>
    </div>
    <div class="toggle-value-container">
	<div class="toggle-desc">PUMP</div>
	<label class="switch">
	  <input type="checkbox" %(checkedPump)s onchange="skip = true; sendAction('pump');">
	  <span class="slider green round"></span>
	</label>
    </div>
</div>
'''

pageTimers = '''
<div class="timer-container">
    <div class="timer-button-container">
        <button onclick="paused = true; document.getElementById('select-timer-modal').style.display = 'block'; return false;" class="outline-button-small">SET TIMER</button>
    </div>
    <div class="timer-button-container">
        <button onclick="paused = true; document.getElementById('select-delayed-modal').style.display = 'block'; return false;" class="outline-button-small">DELAYED HEAT</button>
    </div>
</div>
'''

pageCountdown = '''
<div class="countdown-container">
    <div class="countdown">%(countdown)s</div>
    <button onclick="sendAction('cancelTimer');" class="outline-button outline-button-small">STOP TIMER</button>
    <div><progress id="timer-progress" max="%(timermax)d" value="%(timervalue)d"></progress></div>
</div>
'''

pageCountdownHeat = '''
<div class="countdown-container">
    <div class="countdown-title">DELAYED HEAT IN:</div>
    <div class="countdown">%(countdown)s</div>
    <button onclick="sendAction('cancelDelayedHeat');" class="outline-button outline-button-small">CANCEL</button>
    <div><progress id="timer-progress" max="%(timermax)d" value="%(timervalue)d"></progress></div>
</div>
'''


pageCountdownDone = '''
<div class="countdown-container">
    <div class="countdown blink">%(countdown)s</div>
    <button onclick="sendAction('cancelTimer');" class="outline-button outline-button-small">OK</button>
</div>
'''


pageModals='''
<div id="select-temp-modal" class="modal-background" onclick="if (event.target.id == 'select-temp-modal') { paused = false; document.getElementById('select-temp-modal').style.display = 'none'; }">
    <span class="modal-helper"></span>
    <div class="modal-contents">
        <h1>Set Target Temp</h1>
        <div>
            <input placeholder="Target Temperature" type="number" id="target-temperature" value="%(target)d"/>
        </div>
        <div style="text-align: right">
            <button onclick="paused = false; document.getElementById('select-temp-modal').style.display = 'none';">CANCEL</button>
            <button onclick="paused = false; document.getElementById('select-temp-modal').style.display = 'none'; var v = document.getElementById('target-temperature').value; sendAction('setTemp/' + v);">OK</button>
        </div>
    </div>
</div>
<div id="select-timer-modal" class="modal-background" onclick="if (event.target.id == 'select-timer-modal') { paused = false; document.getElementById('select-timer-modal').style.display = 'none'; }">
    <span class="modal-helper"></span>
    <div class="modal-contents">
        <h1>Set Timer</h1>
        <div style="font-weight: 300px">
             <select id="timer-hours"></select> hours
             <select id="timer-minutes"></select> minutes
        </div>
        <div style="text-align: right">
            <button onclick="paused = false; document.getElementById('select-timer-modal').style.display = 'none';">CANCEL</button>
            <button onclick="paused = false; document.getElementById('select-timer-modal').style.display = 'none'; var h = document.getElementById('timer-hours').value; var m = document.getElementById('timer-minutes').value; m = parseInt(m) + (parseInt(h) * 60); sendAction('timer/' + m);">OK</button>
        </div>
    </div>
</div>
<div id="select-delayed-modal" class="modal-background" onclick="if (event.target.id == 'select-delayed-modal') { paused = false; document.getElementById('select-delayed-modal').style.display = 'none'; }">
    <span class="modal-helper"></span>
    <div class="modal-contents">
        <h1>Set Delayed Heat</h1>
        <div style="font-weight: 300px">
            <input type="date" id="delayed-date" name="date" value="%(today)s" min="%(today)s" max="%(maxday)s" required />
            <input type="time" id="delayed-time" name="time" value="%(time)s"  required />
        </div>
        <div style="text-align: right">
            <button onclick="paused = false; document.getElementById('select-delayed-modal').style.display = 'none';">CANCEL</button>
            <button onclick="paused = false; document.getElementById('select-delayed-modal').style.display = 'none'; var d = document.getElementById('delayed-date').value; var t = document.getElementById('delayed-time').value; console.log(d); console.log(t); sendAction('delayed/' + d + '-' + t);">OK</button>
        </div>
    </div>
</div>
'''

pageConnect='''
    <div class="not-connected-container">
        <button class="outline-button" onclick="sendAction('connect')">
            CONNECT TO GRAINFATHER
        </button>
        <div class="connect-warning">
            Make sure your Grainfather is powered on and in range. If you are connected to the Grainfather using the Grainfather app, disconnect, as
            the Grainfather can only be connected to one device at a time
        </div>
    </div>
'''

pageScanning='''
    <div class="not-connected-container">
        <div class="connecting-warning">
            PLEASE WAIT...
        </div>
    </div>
'''

pageDisconnect='''
    <div class="disconnect-button" onclick="sendAction('disconnect');">[x] Disconnect</div>
'''

pageFooter='''
    <div class="footer footer-%(class)s">
        %(msg)s
    </div>
'''

pageEnd = '''</div>
</body></html>'''


def push(title, message):
    if not PUSHOVER_APP_KEY or not PUSHOVER_USER_KEY:
        return
    conn = httplib.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
    urllib.urlencode({
        "token": PUSHOVER_APP_KEY,
        "user": PUSHOVER_USER_KEY,
        "message": message,
        "title": title
    }), { "Content-type": "application/x-www-form-urlencoded" })
    conn.getresponse()

class GFTimer():

    def __init__(self):
        self.h = 0
        self.m = 0
        self.s = 0
        self.initial = 0
        self.current = 0
        self.finished = False
        self.on = False
        self.notified = False

    def __getitem__(self, item):
        return getattr(self, item)

class GFXConnector():
  
    def __init__(self):
        self.current = 0
        self.target = 0
        self.pump = False
        self.heat = False
        self.delayedHeat = False
        self.lastBroadcast = 0
        self.timer = GFTimer()
        self.setStatus(STATUS_SCANNING, 'Scanning')        
        self.adapter = pygatt.backends.GATTToolBackend()
        self.adapter.start()
        
    def handle_data(self, handle, value):
        self.lastBroadcast = time.time()
        if len(value) != 17:
            return;
        try:
            value = value.replace('Z', '')
            values = value[1:].split(',')
            if chr(value[0]) == 'T':
                on = int(values[0]) > 0
                mins = int(values[1])
                s = int(values[3])
                if s < 60 and mins > 0:
                    mins = mins - 1
                if s == 60:
                    s = 0
                initial = int(values[2]) * 60
                if self.delayedHeat:
                    initial -= 60
                current = initial - (mins * 60) - s
                h = math.floor(mins / 60)
                m = mins % 60

                self.timer.h = h
                self.timer.m = m
                self.timer.s = s
                self.timer.current = current
                self.timer.initial = initial
                self.timer.finished = on and int(values[2]) == 0
                self.timer.on = on

                if self.timer.finished and not self.timer.notified:
                    self.timer.notified = True
                    if self.delayedHeat:
                        push("Grainfather", "Heating Started")
                    else:
                        push("Grainfather", "Timer Finished")
              
                elif not self.timer.finished:
                    self.timer.notified = False

            elif chr(value[0]) == 'X':
                self.target = float(values[0])
                self.current = float(values[1])

            elif chr(value[0]) == 'Y':
                self.heat = int(values[0]) == 1
                self.pump = int(values[1]) == 1
                self.delayedHeat = int(values[7]) == 1

            # elif chr(value[0]) == 'W':                    
                

        except:
            e = sys.exc_info()[0]
            print "Failed to process input"
            print(e)

        if DEBUG:
            print(value)
    
    def scan(self):
        self.setStatus(STATUS_SCANNING, 'Scanning')
        threading.Thread(target=self._scan).start()
    
    def __getitem__(self, item):
        return getattr(self, item)

    def _scan(self):
        try:
            devices = self.adapter.scan(run_as_root=True, timeout=3)
            for device in devices:
                if device['name'] == NAME:
                    self.setStatus(STATUS_CONNECTING, 'Connecting')
                    try:
                        if DEBUG:
                            print("Connecting...")
                        self.device = self.adapter.connect(device['address'])
                        if DEBUG:
                            print("Connected")
                        self.setStatus(STATUS_CONNECTED, 'Connected')
                        self.device.subscribe(NOTIFY, callback=self.handle_data)            
                        self.beep()
                        return
                    except pygatt.exceptions.NotConnectedError:
                        print("failed to connect to %s" % device)
                        self.setStatus(STATUS_ERROR, 'Failed to connect')
                        continue
            self.setStatus(STATUS_DISCONNECTED, 'No Grainfather found')
        except:
            e = sys.exc_info()[0]
            self.setStatus(STATUS_ERROR, 'Failed to scan devices: ' + e)

    def disconnect(self):
        self.lastBroadcast = 0
        if self.device:
            self.setStatus(STATUS_DISCONNECTED, 'Disconnected')
            self.device.disconnect()
            self.device = None

    def stop(self):
        self.adapter.stop()

    def setStatus(self, status, msg):
        self.status = status
        self.msg = msg

    def isHeating(self):
        return self.heat and self.current < self.target
  
    def setTemp(self, temp):
        self._send("$%i," % temp)

    def beep(self):
        self._send("!")

    def togglePump(self):
        self._send("P")
    
    def quitSession(self):
        self._send("Q1")

    def cancel(self):
        self._send("C0,")

    def cancelTimer(self):
        self._send("C")

    def pause(self):
        self._send("G")
    
    def setTimer(self, minutes):
        self._send("S%i" % minutes)

    def toggleHeat(self):
        self._send("H")

    def tempUp(self):
        self._send("U")

    def tempDown(self):
        self._send("D")

    def setDelayedHeat(self, minutes):
        self._send("B%i,0," % minutes)

    def pressSet(self):
        self._send("T")


    def _send(self, cmd):
        if FAKE_GF:
            return
        if self.device:
            b = bytes(cmd.ljust(19))
            self.device.char_write(WRITE, bytearray(b), wait_for_response=False)


class GFXRequestHandler(BaseHTTPRequestHandler):

    def _set_headers(self):
        self.send_response(self.status)
        if self.path == '/gfx.css':
            self.send_header('Content-type', 'text/css')
        else:
            self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        self.status = 200
        self._set_headers()
        if DEBUG:
            print(self.path)
        if self.path == '/gfx.css':
            self.wfile.write(pageCSS)
        elif self.path == '/':
            self.wfile.write(self._full_page())

    def do_HEAD(self):
        self._set_headers()
        
    def do_POST(self):
        body = None
        if self.path == '/refresh':
            if gf.lastBroadcast and time.time() - gf.lastBroadcast > 5:
                gf.disconnect()
            body = self._body()
        elif self.path.startswith('/action/'):
            self._handleAction(self.path[8:])
            return ''
        self.status = 200 if not FAKE_GF else 204
        self._set_headers()
        if body:
            self.wfile.write(body)
    
    def _handleAction(self, action):
        if DEBUG:
            print(action)

        if action == 'tempUp':
            gf.tempUp()

        elif action == 'tempDown':
            gf.tempDown()

        elif action == 'heat':
            gf.toggleHeat()

        elif action == 'pump':
            gf.togglePump()

        elif action == 'connect':
            gf.scan()

        elif action == 'disconnect':
            gf.disconnect()

        elif action == 'cancelTimer':
            gf.cancelTimer()

        elif action == 'cancelDelayedHeat':
            gf.pressSet()

        elif action.startswith('setTemp/'):
            gf.setTemp(int(action[8:]))
        
        elif action.startswith('timer/'):
            gf.setTimer(int(action[6:]))

        elif action.startswith('delayed/'):
            arg = action[8:]
            time = datetime.strptime(arg, '%Y-%m-%d-%H:%M')
            now = datetime.now()
            if now > time:
                return
            diff = time - now
            mins = (diff.days * 1440) + (diff.seconds / 60)
            if mins > 0:
                gf.setDelayedHeat(mins)

    def _full_page(self):
        return pageHead + self._body() + pageEnd

    def _body(self):
        controls = ''
        top = ''
        timers = ''
        modals = ''
        if gf == None:
            return ""
        if gf.status == STATUS_CONNECTED:
            args = self._pageArguments()
            top = pageTemperature % args
            top = top + pageDisconnect
            controls = pageControls % args
            timerPg = pageTimers
            if gf.timer.on:
                if not gf.timer.finished:
                    timerPg = pageCountdownHeat if gf.delayedHeat else pageCountdown
                else:
                    timerPg = pageCountdownDone
            timers = timerPg % args
            modals = pageModals % args
        if gf.status == STATUS_DISCONNECTED or gf.status == STATUS_ERROR:
            top = pageConnect
        if gf.status == STATUS_CONNECTING or gf.status == STATUS_SCANNING:
            top = pageScanning
        footer = pageFooter % { 'class': gf.status, 'msg': gf.msg }
        return top + controls + timers + modals + footer

    def _pageArguments(self):
        currentTempClass = 'heating' if gf.isHeating() else 'not-heating'
        checkedHeat = 'checked' if gf.heat else ''
        checkedPump = 'checked' if gf.pump else ''
        d = datetime.now()
        today = d.strftime("%Y-%m-%d")
        time = d.strftime("%H:%M")
        d = d + timedelta(days=7) 
        maxday = d.strftime("%Y-%m-%d")
        countdown = "%(h)02d:%(m)02d:%(s)02d" % gf.timer if gf.timer.h else "%(m)02d:%(s)02d" % gf.timer
        return { 'unit': 'C', 
                'target': gf.target, 
                'current': gf.current, 
                'currentTempClass': currentTempClass,
                'checkedHeat': checkedHeat,
                'checkedPump': checkedPump,
                'today': today, 
                'maxday': maxday,
                'timermax': gf.timer.initial,
                'timervalue': gf.timer.current,
                'countdown': countdown,
                'time': time
            }

def getLocalIp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

opts, args = getopt.getopt(sys.argv[1:],"p:d",["port=", "fake", "push-app=", "push-user="])
for opt, arg in opts:
    if opt == '--fake':
        FAKE_GF = True
    elif opt == '--push-app':
        PUSHOVER_APP_KEY = arg
    elif opt == '--push-user':
        PUSHOVER_USER_KEY = arg
    elif opt in ('-p', '--port'):
        PORT = int(arg)
    elif opt == '-d':
        DEBUG = True



gf = None
def initGF():
    global gf
    gf = GFXConnector()
    gf.scan()

if FAKE_GF:
    gf = GFXConnector()
    gf.current = 20
    gf.target = 30
    gf.status = STATUS_CONNECTED

else:
    threading.Thread(target=initGF).start()

    


httpd = SocketServer.TCPServer(("", PORT), GFXRequestHandler)
print "Server available at:"
print "http://%(host)s:%(port)d" % { 'host': getLocalIp(), 'port': PORT }
print "http://%(host)s:%(port)d" % { 'host': socket.gethostname(), 'port': PORT }
httpd.serve_forever()

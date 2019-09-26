# gfx
Grainfather signal extender - Connects to your Grainfather and starts an http server allowing you to control it from any device connected to your home wifi network

This is meant to be ran on a raspberry pi close to your Grainfather (or any other linux system that can run python). I tried to include everything in a single file and have minimal dependencies. Only basic functions are currently supported

Please note that the Grainfather can only be connected to one device at a time, so if you are connected to it using the mobile app, gfx will not be able to connect to it vice versa.

<img src="/screens/screen2.jpg" height="480" width="270"> |
<img src="/screens/screen3.jpg" height="480" width="270"> | <img src="/screens/screen4.jpg" height="480" width="270">

# Requirements

```bash
sudo apt install python-pip
sudo pip install pygatt
sudo pip install pexpect
```

# Usage

```bash
sudo python gfx.py -p [port number] --push-user [pushover user key] --push-app [pushover app key]
```

All arguments are optional
-p = http server port, default is 8000
--push-app = Pushover app key, add in order to receive push notifications
--push-user = Pushover user key, add in order to receive push notifications

# To Do

- [ ] Add support for Fahrenheit
- [ ] Add support for recipes
- [ ] Importing recipes from Beersmith and Brewfather
- [ ] Custom mash profiles

# Acknowledgements

Inspired by [GFConnect](https://github.com/BladeRunner68/GFConnect)
 
# License
This project is licensed under the MIT License - see the LICENSE file for details

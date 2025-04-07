# ButtonBoxManager
DIY button interfacer with arduino nano 

This python script is made to interface 12 buttons that can trigger keyboard shorcuts or custom commands
It use 

Python dependances:
 -
 <pre>pip install pyautogui pyserial</pre>
 <pre>sudo apt install python3-tk</pre>

Here is the hardware:  
 -
<img src="png/ButtonBox.png" alt="ButtonBox" width="50%"/>

Soldering:
 -
<img src="png/soldering.png" alt="Soldering" width="50%"/>



Screenshots:
 -
Ether choose between multiple pages or just one page mode
<div align="left">
  <img src="png/screen1.png" alt="Image 1" width="40%"/>
  <img src="png/screen2.png" alt="Image 2" width="40%"/>
</div>

Flash Arduino:
 -
You need to flash arduino_nano_rom.ino using arduino IDE
 Open arduino ide and select your board, then
 File -> Open -> then open arduino_nano_rom.ino
 <img src="png/arduinoIDEinstall1.png.png" alt="Soldering" width="50%"/>

 Clic upload
 <img src="png/arduinoIDEinstall2.png.png" alt="Soldering" width="50%"/>

Config file:
 -
You can edit max pages in the config.json 
Rest of config can be done in the gui.

Launch:
 -
 - in powershell, launch
 <pre> python.exe path/to/ButtonBox/ButtonBoxManager.py </pre>

to be added:
 -
- Command line / no head program
- packed to exe
- choose buttons number
- linux compatiblility
- custom png instead of button + desc
- multi language support
- who knows...

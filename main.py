# ////////////////////////////////////////////////////////////////
# //                     IMPORT STATEMENTS                      //
# ////////////////////////////////////////////////////////////////

import math
import sys
import time
import threading
from threading import Thread

from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import *
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.slider import Slider
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.animation import Animation
from functools import partial
from kivy.config import Config
from kivy.core.window import Window
from pidev.kivy import DPEAButton
from pidev.kivy import PauseScreen
from time import sleep
from kivy.properties import ObjectProperty
import RPi.GPIO as GPIO
from pidev.stepper import stepper
from pidev.Cyprus_Commands import Cyprus_Commands_RPi as cyprus

# ////////////////////////////////////////////////////////////////
# //                      GLOBAL VARIABLES                      //
# //                         CONSTANTS                          //
# ////////////////////////////////////////////////////////////////
ON = False
OFF = True
HOME = True
TOP = False
OPEN = False
CLOSE = True
YELLOW = .180, 0.188, 0.980, 1
BLUE = 0.917, 0.796, 0.380, 1
DEBOUNCE = 0.1
INIT_RAMP_SPEED = 150
RAMP_LENGTH = 725


# ////////////////////////////////////////////////////////////////
# //            DECLARE APP CLASS AND SCREENMANAGER             //
# //                     LOAD KIVY FILE                         //
# ////////////////////////////////////////////////////////////////
class MyApp(App):
    def build(self):
        self.title = "Perpetual Motion"
        return sm


Builder.load_file('main.kv')
Window.clearcolor = (.1, .1, .1, 1)  # (WHITE)

cyprus.open_spi()

# ////////////////////////////////////////////////////////////////
# //                    SLUSH/HARDWARE SETUP                    //
# ////////////////////////////////////////////////////////////////
sm = ScreenManager()
ramp = stepper(port=0, speed=INIT_RAMP_SPEED)


# ////////////////////////////////////////////////////////////////
# //                       MAIN FUNCTIONS                       //
# //             SHOULD INTERACT DIRECTLY WITH HARDWARE         //
# ////////////////////////////////////////////////////////////////

# ////////////////////////////////////////////////////////////////
# //        DEFINE MAINSCREEN CLASS THAT KIVY RECOGNIZES        //
# //                                                            //
# //   KIVY UI CAN INTERACT DIRECTLY W/ THE FUNCTIONS DEFINED   //
# //     CORRESPONDS TO BUTTON/SLIDER/WIDGET "on_release"       //
# //                                                            //
# //   SHOULD REFERENCE MAIN FUNCTIONS WITHIN THESE FUNCTIONS   //
# //      SHOULD NOT INTERACT DIRECTLY WITH THE HARDWARE        //
# ////////////////////////////////////////////////////////////////
class MainScreen(Screen):
    version = cyprus.read_firmware_version()
    staircaseSpeedText = '0'
    rampSpeed = INIT_RAMP_SPEED
    staircaseSpeed = 40



    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.initialize()

    gate_position = 0
    speed = 0
    gate = ObjectProperty(DPEAButton)
    def toggleGate(self):

        if self.ids.gate.text == "Open Gate":
            cyprus.set_servo_position(2, .5)
            self.ids.gate.text = "Close Gate"
            sleep(1)
        elif self.ids.gate.text == "Close Gate":
            cyprus.set_servo_position(2, 0)
            self.ids.gate.text = "Open Gate"
            sleep(1)

    def gate_switch(self):

        Thread(target=self.toggleGate).start()
    staircase = ObjectProperty(DPEAButton)
    # WHY ARE YOU SO RANDOM
    def toggleStaircase(self):
        if self.ids.staircase.text == "Staircase On":
            cyprus.set_pwm_values(1, period_value=100000, compare_value=100000
                                  , compare_mode=cyprus.LESS_THAN_OR_EQUAL)
            self.ids.staircase.text = "Staircase Off"

        elif self.ids.staircase.text == "Staircase Off":
            cyprus.set_pwm_values(1, period_value=100000, compare_value=0
                                  , compare_mode=cyprus.LESS_THAN_OR_EQUAL)
            self.ids.staircase.text = "Staircase On"

    def stairs(self):
        Thread(target=self.toggleStaircase()).start()

    ramp_speed = 0
    def toggleRamp(self):

        self.s0.start_relative_move(28)
        while self.s0.isBusy():
            sleep(.3)
        self.s0.go_until_press(0, 64000)
        sleep(3)

    def ramp_switch(self):
        Thread(target=self.toggleRamp()).start()

    def auto(self):
        cyprus.set_servo_position(2, 0)
        cyprus.set_pwm_values(1, period_value=100000, compare_value=100000
                              , compare_mode=cyprus.LESS_THAN_OR_EQUAL)
        sleep(8)
        cyprus.set_servo_position(2, .5)
        sleep(0.7)
        cyprus.set_servo_position(2, 0)
        sleep(1.2)
        cyprus.set_pwm_values(1, period_value=100000, compare_value=0
                              , compare_mode=cyprus.LESS_THAN_OR_EQUAL)
        Thread(target=self.motor_two()).start()

    def motor_two(self):
        print("MOVE THE RAMP")
        self.s0 = stepper(port=0, micro_steps=32, hold_current=20, run_current=20, accel_current=20, deaccel_current=20,
                          steps_per_unit=200, speed=3)
        self.s0.start_relative_move(28)
        while self.s0.isBusy():
            sleep(.3)
        self.s0.go_until_press(0, 64000)

# HH
    def ru(self):
        Thread(target=self.auto()).start()

    def setRampSpeed(self, speed):
        pass

    def setStaircaseSpeed(self, speed):
        cyprus.set_pwm_values(1, period_value=100000, compare_value=speed
                              , compare_mode=cyprus.LESS_THAN_OR_EQUAL)

    def initialize(self):
        cyprus.initialize()
        cyprus.setup_servo(2)
        self.s0 = stepper(port=0, micro_steps=32, hold_current=20, run_current=20, accel_current=20, deaccel_current=20,
                     steps_per_unit=200, speed=3)

    def resetColors(self):
        self.ids.gate.color = YELLOW
        self.ids.staircase.color = YELLOW
        self.ids.ramp.color = YELLOW
        self.ids.auto.color = BLUE

    def quit(self):
        print("Exit")
        MyApp().stop()


sm.add_widget(MainScreen(name='main'))

# ////////////////////////////////////////////////////////////////
# //                          RUN APP                           //
# ////////////////////////////////////////////////////////////////

MyApp().run()
cyprus.close_spi()

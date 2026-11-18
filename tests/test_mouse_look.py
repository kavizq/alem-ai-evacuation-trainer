import unittest
from types import SimpleNamespace
from campaign import Campaign

class Window:
    def __init__(self,warp):
        self.warp=warp
        self.x,self.y=400,300
    def getProperties(self):
        return SimpleNamespace(getMouseMode=lambda:0,getForeground=lambda:True,getXSize=lambda:800,getYSize=lambda:600)
    def getPointer(self,index):
        return SimpleNamespace(getX=lambda:self.x,getY=lambda:self.y,getInWindow=lambda:True)
    def movePointer(self,index,x,y):
        if self.warp: self.x,self.y=x,y
        return self.warp

class MouseLookTests(unittest.TestCase):
    def test_look_with_and_without_pointer_warp(self):
        for warp in (True,False):
            window=Window(warp)
            game=SimpleNamespace(win=window,mouse_locked=True,mouse_primed=False,heading=0,pitch=0,
                                 keys=dict.fromkeys(('arrow_left','arrow_right','arrow_up','arrow_down'),False))
            Campaign.update_look(game,.016)
            window.x+=20
            window.y+=10
            Campaign.update_look(game,.016)
            self.assertAlmostEqual(game.heading,-3)
            self.assertAlmostEqual(game.pitch,-1.2)

    def test_property_notification_preserves_mouse_tracking(self):
        window=Window(True)
        game=SimpleNamespace(win=window,window_foreground=True,mouse_primed=True,previous_pointer=(400,300))
        Campaign.window_changed(game,window)
        self.assertTrue(game.mouse_primed)

"""Closing cards and an original quiet synthesized soundtrack."""
import math
import struct
import wave
from pathlib import Path
from platform_paths import panda_path
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode

CARDS = (
    "Congratulations! You’ve completed our game!",
    "A special thanks from the developers of this game goes to Dilnura Ali.",
    "Thank you for all your hard work this term; we are very grateful to you—without you, we wouldn’t have understood these subjects nearly as well!",
)


def soundtrack():
    path=Path(__file__).with_name('audio')/'credits.wav'
    if path.exists():
        return path
    rate=22050
    duration=40
    chords=((48,52,55,59),(45,48,52,55),(41,45,48,52),(43,47,50,55))
    samples=bytearray()
    for i in range(rate*duration):
        t=i/rate
        chord=chords[int(t//5)%4]
        beat=t%1.25
        note=chord[int(t/1.25)%4]+12
        frequency=440*2**((note-69)/12)
        melody=math.sin(math.tau*frequency*t)*math.exp(-beat*2.5)*(1-math.exp(-beat*35))
        pad=sum(math.sin(math.tau*440*2**((n-69)/12)*t) for n in chord)/4
        chord_envelope=min(1,(t%5)*1.5)*min(1,(5-t%5)*1.5)
        fade=min(1,t/3,(duration-t)/4)
        samples.extend(struct.pack('<h',int(32767*fade*(.10*melody+.065*pad*chord_envelope))))
    with wave.open(str(path),'wb') as output:
        output.setparams((1,2,rate,0,'NONE','not compressed'))
        output.writeframes(samples)
    return path


class Credits:
    def __init__(self,game):
        self.game=game
        aspect=game.getAspectRatio()
        self.background=game.card(-aspect,1,aspect*2,2,(.02,.035,.045,.96))
        self.background.setBin('fixed',40)
        self.text=OnscreenText(parent=game.aspect2d,text='',pos=(0,.15),scale=.064,
                              align=TextNode.ACenter,fg=(.95,.94,.88,1),mayChange=True)
        self.text.setFont(game.question_font)
        self.text.setWordwrap(38)
        self.text.setBin('fixed',41)
        self.footer=OnscreenText(parent=game.aspect2d,text='R  /  Play again',pos=(0,-.78),scale=.035,fg=(.6,.73,.76,1))
        self.footer.setBin('fixed',41)
        self.music=game.loader.loadSfx(panda_path(soundtrack()))
        self.started=False
        self.hide()

    def hide(self):
        self.background.hide()
        self.text.hide()
        self.footer.hide()
        self.music.stop()
        self.started=False

    def update(self,time):
        if time<10:
            return
        if not self.started:
            self.started=True
            self.game.set_stair_hud(False)
            self.game.sounds['ambient'].stop()
            self.music.play()
            self.background.show()
            self.text.show()
            self.footer.show()
        elapsed=time-10
        index=0 if elapsed<7 else (1 if elapsed<17 else 2)
        start=(0,7,17)[index]
        end=(7,17,40)[index]
        alpha=min(1,(elapsed-start)/1.2)
        if index<2:
            alpha=min(alpha,max(0,(end-elapsed)/.8))
        self.text.setText(CARDS[index])
        self.text.setFg((.95,.94,.88,max(0,alpha)))

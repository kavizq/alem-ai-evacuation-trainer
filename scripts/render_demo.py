"""Record real game renders using scripted ordinary movement and captions.

Optional dependency: pip install imageio-ffmpeg==0.8.1
Run from the project root: python scripts/render_demo.py --output docs/DEMO_VIDEO.mp4
"""
import argparse
import math
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from panda3d.core import loadPrcFileData,TextNode
loadPrcFileData('', 'window-type offscreen\naudio-library-name null\nwin-size 1152 720')
from direct.gui.OnscreenText import OnscreenText
from training import Trainer
from navigation import walking_path
import imageio_ffmpeg


def run(output):
    output=Path(output).resolve();output.parent.mkdir(parents=True,exist_ok=True)
    scratch=ROOT/'verification';scratch.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch) as folder:
        folder=Path(folder)
        game=Trainer('smoke',data_dir=folder)
        game.clock.setMode(game.clock.MNonRealTime);game.clock.setDt(.02)
        game.mouse_locked=False
        game.ui_controls.hide();game.ui_message.hide();game.ui_event.hide()
        aspect=game.getAspectRatio()
        background=game.card(-aspect,-.53,aspect*2,.47,(.025,.045,.07,.98));background.setBin('fixed',70)
        caption=OnscreenText(parent=game.aspect2d,text='',pos=(0,-.67),align=TextNode.ACenter,
                            scale=.043,fg=(.97,.98,1,1),mayChange=True)
        caption.setFont(game.question_font);caption.setWordwrap(73);caption.setBin('fixed',71)
        raw=folder/'capture.mp4'
        command=[imageio_ffmpeg.get_ffmpeg_exe(),'-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1152x720','-r','10','-i','-',
                 '-vf','vflip','-c:v','libx264','-preset','veryfast','-crf','23','-pix_fmt','yuv420p',str(raw)]
        encoder=subprocess.Popen(command,stdin=subprocess.PIPE)
        ticks=0;frames=0
        def step():
            nonlocal ticks,frames
            game.tick(None);ticks+=1
            if ticks%5==0:
                game.graphicsEngine.renderFrame();game.graphicsEngine.renderFrame()
                data=game.win.getScreenshot().getRamImageAs('RGB')
                encoder.stdin.write(bytes(data));frames+=1
        def hold(seconds,text=None):
            if text:caption.setText(text)
            for _ in range(round(seconds/.02)):step()
        def walk(target):
            path=walking_path(game.position[:2],target,game.can_walk)
            assert path,('unreachable',game.floor,target)
            for x,y in path[1:]:
                for _ in range(80):
                    dx,dy=x-game.position[0],y-game.position[1]
                    if math.hypot(dx,dy)<.055:break
                    game.heading=math.degrees(math.atan2(-dx,dy));game.keys['w']=True;step()
                else:raise AssertionError(('stuck',game.floor,game.position,(x,y)))
            game.keys['w']=False
        try:
            hold(9,'ALEM AI EVACUATION TRAINER\nPractise route choices when warnings are uncertain.\nAutomated demonstration of the local application.')
            game.skip_intro()
            caption.setText('A fictional smoke alert interrupts the lecture.\nElevators are offline. Find the cyan route terminal.')
            walk((9.,-17.));game.interact()
            hold(12,'A* finds two routes through the actual game geometry.\nThe shorter route is 25 m. The alternative is 27 m.')
            hold(12,'Bayesian inference updates the 20% prior.\nWith 80% sensitivity and 20% false alarms, ALERT gives 50% blockage risk.')
            game.answer(3)
            hold(14,'MDP value iteration considers the next states and a blocked-attempt penalty.\nIt recommends the slightly longer alternative. Press 1 to use it.')
            game.answer(1)
            for floor in (4,3,2,1):
                if floor!=4:
                    caption.setText('A new floor has its own sensor reading and route decision.\nThe upper-right plan comes from the same collisions as player movement.')
                    walk((9.,-17.));game.interact()
                    if floor==3:
                        hold(7,'NO ALERT reduces the modeled risk to 5.88%.\nA small remaining risk can still justify a short detour.')
                    else:hold(3)
                    game.answer(1)
                if floor==2:
                    hold(3,'Now the exercise changes after the route has been selected.')
                    old=game.selected_side;game.trigger_update()
                    assert game.selected_side!=old
                    hold(9,'The planned exit becomes unavailable.\nADEKA removes it from the available actions and draws a replacement route.')
                caption.setText('Follow the cyan floor guide and use the selected stairs.\nThe moving student characters share the chosen destination.')
                walk(game.gate_targets[game.selected_side]);game.interact()
                if floor>1:hold(6.1)
            assert game.ending=='success'
            hold(12,'The summary records time, distance and route choices.\nModel risk scores support discussion. Learning effectiveness still needs a user study.')
        finally:
            encoder.stdin.close();encoder.wait();game.destroy()
        assert encoder.returncode==0
        duration=frames/10
        # Fit the complete scripted demonstration into the required 2-3 minutes.
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-y','-loglevel','error','-i',str(raw),
                        '-vf',f'setpts={150/duration:.8f}*PTS','-r','15','-c:v','libx264','-preset','veryfast','-crf','22',
                        '-pix_fmt','yuv420p','-movflags','+faststart',str(output)],check=True)
        print(f'Video: {output}; original playback {duration:.1f}s, delivered approximately 150s',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='docs/DEMO_VIDEO.mp4')
    run(parser.parse_args().output)

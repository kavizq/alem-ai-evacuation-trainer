"""Check the bundled narration and its playback through Panda3D."""
import json
from pathlib import Path
from types import SimpleNamespace
import wave
from panda3d.core import AudioManager, AudioSound
from platform_paths import panda_path
from speech import _approved_voice_bank, _recording_path, speak, stop_speech


def run():
    root=Path(__file__).resolve().parents[1]
    bank=_approved_voice_bank()
    assert bank is not None,'Approved voice bank is missing'
    manager=AudioManager.createAudioManager()
    assert manager.isValid(),'No valid local audio manager'
    game=SimpleNamespace(voice=None,voice_sound=None,voice_muted=False,
                         voice_manifest={},loader=SimpleNamespace(loadSfx=manager.getSound))
    paths=set()
    for message in bank['lines']:
        path,active=_recording_path(game,message)
        assert active and path is not None,message
        paths.add(path)
    for side in ('Left','Right'):
        for length,risk in ((0,0),(27,50),(125,100)):
            line=f'{side} route selected, {length} m. Modeled blockage risk {risk}%. Follow the cyan guide. U checks for a route update.'
            path,active=_recording_path(game,line)
            assert active and path is not None,line
            paths.add(path)
    for path in paths:
        with wave.open(str(path),'rb') as audio:
            assert audio.getframerate()==24000 and audio.getnframes()>0
        sound=manager.getSound(panda_path(path))
        assert sound.status()==AudioSound.READY and sound.length()>0,path
    welcome=next(line for line in bank['lines'] if line.startswith('Welcome to Qairu.'))
    path,_=_recording_path(game,welcome)
    with wave.open(str(path),'rb') as audio:
        assert audio.getnframes()/audio.getframerate()<8.,'Welcome overlaps the next lecture cue'
    assert speak(game,welcome)=='recording'
    manager.update()
    assert game.voice_sound.status()==AudioSound.PLAYING
    stop_speech(game)
    assert speak(game,'Unrecorded future message.')=='text'
    assert game.voice is None
    manager.shutdown()
    result={'passed':True,'static_messages':len(bank['lines']),'dynamic_patterns':len(bank['patterns']),'voice_files':len(paths),'panda_audio_ready':True,'welcome_under_8_s':True}
    (root/'verification/voice_checks.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))


if __name__=='__main__':run()

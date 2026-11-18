"""Play the original recordings on every platform, with offline OS speech.

Original recorded lines always take priority. New training messages can use
the installed English system voice. No text is sent to a network service.
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys
from panda3d.core import ConfigVariableString
from platform_paths import panda_path


WINDOWS_SPEECH = r'''
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$line = [Console]::In.ReadToEnd()
Add-Type -AssemblyName System.Speech
$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
$english = $speaker.GetInstalledVoices() | Where-Object {
    $_.Enabled -and $_.VoiceInfo.Culture.Name -eq 'en-US'
} | Sort-Object { if ($_.VoiceInfo.Name -match 'Zira') { 0 } else { 1 } } | Select-Object -First 1
if ($english) { $speaker.SelectVoice($english.VoiceInfo.Name) }
$speaker.Speak($line)
$speaker.Dispose()
'''


def stop_speech(game):
    sound = getattr(game, 'voice_sound', None)
    if sound is not None:
        sound.stop()
        game.voice_sound = None
    process = getattr(game, 'voice', None)
    if process is not None and process.poll() is None:
        try:
            process.terminate()
        except OSError:
            pass
    game.voice = None


def speak(game, message):
    stop_speech(game)
    if getattr(game, 'voice_muted', False):
        return 'muted'
    # Automated offscreen checks must not start speech outside the null mixer.
    if ConfigVariableString('audio-library-name').getValue() == 'null':
        return 'disabled'
    filename = game.voice_manifest.get(message)
    recording = Path(__file__).with_name('audio')/'adeka_en'/filename if filename else None
    if recording is not None and recording.is_file():
        if not hasattr(game, 'speech_cache'):
            game.speech_cache = {}
        if filename not in game.speech_cache:
            game.speech_cache[filename] = game.loader.loadSfx(panda_path(recording))
        game.voice_sound = game.speech_cache[filename]
        game.voice_sound.play()
        return 'recording'
    command = None
    options = {'stdout': subprocess.DEVNULL, 'stderr': subprocess.DEVNULL}
    if sys.platform == 'win32':
        executable = shutil.which('powershell.exe')
        if executable:
            command = [executable, '-NoLogo', '-NoProfile', '-NonInteractive',
                       '-Command', WINDOWS_SPEECH]
            options.update(stdin=subprocess.PIPE, text=True, encoding='utf-8',
                           creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    elif sys.platform == 'darwin' and shutil.which('say'):
        command = ['say', message]
    else:
        executable = shutil.which('espeak-ng') or shutil.which('espeak')
        if executable:
            command = [executable, message]
    if command is None:
        return 'text'
    try:
        game.voice = subprocess.Popen(command, **options)
        if sys.platform == 'win32':
            game.voice.stdin.write(message)
            game.voice.stdin.close()
        return 'system'
    except (OSError, ValueError):
        stop_speech(game)
        return 'text'

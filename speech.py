"""Play approved local narration, with compatibility for the original project."""
from functools import lru_cache
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from panda3d.core import ConfigVariableString
from platform_paths import panda_path


@lru_cache(maxsize=1)
def _approved_voice_bank():
    path = Path(__file__).with_name('audio')/'adeka_f5'/'manifest.json'
    try:
        bank = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(bank, dict) or bank.get('version') != 1 or bank.get('approved') is not True:
            return None
        if not isinstance(bank.get('lines'), dict):
            return None
        bank['compiled_patterns'] = [(re.compile(item['pattern']), item)
                                     for item in bank.get('patterns', [])]
        return bank
    except (OSError, ValueError, TypeError, KeyError, re.error):
        return None


def _recording_path(game, message):
    bank = _approved_voice_bank()
    if bank is not None:
        entry = bank['lines'].get(message)
        if entry is None:
            entry = next((item for pattern, item in bank['compiled_patterns']
                          if pattern.fullmatch(message)), None)
        filename = entry.get('file') if isinstance(entry, dict) else None
        if isinstance(filename, str) and Path(filename).name == filename:
            path = Path(__file__).with_name('audio')/'adeka_f5'/filename
            if path.is_file():
                return path, True
        # Keep the chosen voice consistent; an unknown line remains subtitled.
        return None, True
    filename = game.voice_manifest.get(message)
    path = Path(__file__).with_name('audio')/'adeka_en'/filename if filename else None
    return path if path is not None and path.is_file() else None, False


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
    recording, approved = _recording_path(game, message)
    if recording is not None:
        if not hasattr(game, 'speech_cache'):
            game.speech_cache = {}
        key = str(recording)
        try:
            if key not in game.speech_cache:
                game.speech_cache[key] = game.loader.loadSfx(panda_path(recording))
            game.voice_sound = game.speech_cache[key]
            if game.voice_sound is not None:
                game.voice_sound.play()
                return 'recording'
        except (OSError, RuntimeError):
            pass
        return 'text'
    if approved:
        return 'text'
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

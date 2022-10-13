import wave
import json
from os import walk
import sys
from itertools import repeat
import string
import re

from word import Word
from line import Line
from pdfLoad import pdfPositionHandling

from vosk import Model, KaldiRecognizer, SetLogLevel
from pydub import AudioSegment

import multiprocessing as mp

f = open("settings.json")
settings = json.load(f)
f.close()


def parseAudio(fileName, model, return_dict):
    if not ".mp3" in fileName:
        pass
        return

    audio_wav = fileName.replace(".mp3", ".wav")

    sound = AudioSegment.from_mp3(fileName)
    sound.export(audio_wav, format="wav")

    wf = wave.open(audio_wav, "rb")
    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)

    print("Parsing file {}".format(fileName))

    # get the list of JSON dictionaries
    results = []
    # recognize speech using vosk model
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            part_result = json.loads(rec.Result())
            results.append(part_result)
    part_result = json.loads(rec.FinalResult())
    results.append(part_result)

    numWords = 0

    # convert list of JSON dictionaries to list of 'Word' objects
    for sentence in results:
        if len(sentence) == 1:
            # sometimes there are bugs in recognition
            # and it returns an empty dictionary
            # {'text': ''}
            continue
        for obj in sentence['result']:
            w = Word(obj, audio_wav)  # create custom Word object

            if not w.word in return_dict:
                return_dict[w.word] = []
                numWords += 1
            return_dict[w.word].append(w)

    wf.close()  # close audiofile

    print("Found {} unique words in file {}".format(
        numWords, audio_wav.split("/")[-1]))

    pass


def parseAudioDirectory(audio_path, model):
    wordMapping = {}

    for root, subFolders, files in walk(audio_path):
        print("Parsing files in folder {}".format(root))

        fileNames = [root + "/" + f for f in files]

        manager = mp.Manager()
        return_dict = manager.dict(wordMapping)

        assert mp.get_start_method() == "fork", "Requires 'forking' operating system"
        processes = []
        for file in fileNames:
            p = mp.Process(target=parseAudio, args=(file, model, return_dict))
            processes.append(p)
            p.start()

        for p in processes:
            p.join()

        print("Done parsing files in folder {}".format(root))

        wordMapping = return_dict

    print("Found {} total unique words".format(len(wordMapping.keys())))
    return return_dict


def parsePDF(fileName, keepPunctuation=False):
    # load the pdf
    pdf = pdfPositionHandling()
    text = pdf.parsepdf(fileName)

    conversations = []
    character = ""
    currentLineText = ""
    for line in text.split("\n"):
        line = line.strip()
        if any(substring in line for substring in settings["excludeWords"]):
            continue

        line = re.sub(r'[0-9]', " ", line)
        line = re.sub(r'\([^()]*\)', "", line)
        line = re.sub(r'\([^[]]*\)', "", line)

        if not keepPunctuation:
            line = line.translate(str.maketrans(
                "", "", string.punctuation)).strip()
        if (line == ""):
            continue

        newCharacter = ""
        for name in settings["names"]:
            if not name in line or line.index(name) > 0:
                continue
            newCharacter = name
            break

        if newCharacter != "":
            if character != "" and currentLineText.strip() != "":
                l = Line(character, currentLineText.lower())
                conversations.append(l)
                currentLineText = ""

            character = newCharacter
        else:
            currentLineText += line+" "

    return conversations


def main():

    # check args
    if len(sys.argv) < 2:
        print("Usage: {} audio_folder ?model_type".format(sys.argv[0]))
        exit(1)

    # parse all lines from pdf scripts
    lines = []
    for script in settings["scripts"]:
        print("Parsing {}...".format(script), end="")
        lines += parsePDF(script)
        print(" done, {} lines".format(len(lines)))
    print("Parsed {} total lines".format(len(lines)))

    # load the vosk model
    print("Loading model...", end="")
    model_type = sys.argv[2] if len(sys.argv) > 2 else settings["defaultModel"]
    model_path = settings["models"][model_type] or settings["models"]["full"]
    SetLogLevel(-1)
    model = Model(model_path)
    print(" done")

    # parse all audio files
    print("Parsing audio files...")
    audio_path = sys.argv[1]
    wordMapping = parseAudioDirectory(audio_path, model)

    print("Starting analysis with {} words".format(len(wordMapping.keys())))


if __name__ == "__main__":
    main()

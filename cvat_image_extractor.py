#!/usr/bin/env python3

import sys
import xml.etree.ElementTree as ET
import numpy as np
import cv2
import os


def getTracksNodeForFrame(documentRoot, frameIndex):
    tracks = documentRoot.findall('track')
    if tracks is None:
        return None

    foundTracks = []

    for track in tracks:
        box = track.find('box')
        if box is not None:
            if int(box.get('frame')) == frameIndex:
                foundTracks.append(track)

    return foundTracks


def extractROI(frame, xtl, ytl, xbr, ybr, padding):
    _xtl = max(0, xtl-padding)
    _ytl = max(0, ytl-padding)
    _xbr = min(frame.shape[1]-1, xbr+padding)
    _ybr = min(frame.shape[0]-1, ybr+padding)
    return frame[_ytl:_ybr, _xtl:_xbr]




# ------- MAIN -------
def main():
    if len(sys.argv) < 2:
        print()
        print(" INVALID ARGUMENTS")
        print()
        print(" --ant      |  file with annotations by cvat")
        print()
        print(" OPTIONAL:")
        print(" --video    |  video file name. different video file name than specified in annotation file")
        print(" --padding  |  in pixels. extract additional area around roi, if present")
        print(" --ft       |  time to display current frame. 0 -> no display")
        exit(1)

    annotationFile = ""
    videoFile = ""
    padding = 0
    frameTime = 10

    skipIteration = False
    for i in range(1, len(sys.argv)):
        arg = sys.argv[i]

        if skipIteration:
            skipIteration = False
            continue

        if sys.argv[i] == "--ant":
            annotationFile = sys.argv[i+1]
            skipIteration = True

        elif sys.argv[i] == "--video":
            vidoeFile = sys.argv[i+1]
            skipIteration = True

        elif sys.argv[i] == "--padding":
            padding = int(sys.argv[i+1])
            skipIteration = True

        elif sys.argv[i] == "--ft":
            frameTime = int(sys.argv[i+1])
            skipIteration = True

        else:
            print("ERROR: unknown argument " + arg)

    try:
        tree = ET.parse(annotationFile)
        global root
        root = tree.getroot()
    except FileNotFoundError:
        print("ERROR: could not load xml file")
        exit(1)


    filePath = str(root.find('meta').find('source').text)
    filePathParts = filePath.split('/')
    fileName = filePathParts[len(filePathParts)-1]

    capture = cv2.VideoCapture(fileName)


    frameCounter = 0
    labelCountsDict = {}
    while capture.isOpened():
        ret, frame = capture.read()
        if frame is None:
            break
        if frameTime != 0:
            cv2.imshow("Entire Frame", frame)

        currentTracks = getTracksNodeForFrame(root, frameCounter)
        if len(currentTracks) > 0:
            print("frame " + currentTracks[0].find('box').get('frame'), end='')

            for currentTrack in currentTracks:
                labelCountsDict.setdefault(currentTrack.get('label'), 0)
                print(" | " + currentTrack.get('label'), end='')
                print()
                xtl = round(float(currentTrack.find('box').get('xtl')))
                ytl = round(float(currentTrack.find('box').get('ytl')))
                xbr = round(float(currentTrack.find('box').get('xbr')))
                ybr = round(float(currentTrack.find('box').get('ybr')))
                roi = extractROI(frame, xtl, ytl, xbr, ybr, padding)
                display_roi = roi.copy()
                cv2.rectangle(display_roi, (padding, padding), (display_roi.shape[1]-1-padding, display_roi.shape[0]-1-padding), (0, 255, 0))
                if frameTime != 0:
                    cv2.imshow("ROI", display_roi)
                directory = "cvat_ie_output/" + currentTrack.get('label') + "/"
                if not os.path.exists(directory):
                    os.makedirs(directory)
                cv2.imwrite(directory + str(labelCountsDict[currentTrack.get('label')]) + ".png", roi)
                labelCountsDict[currentTrack.get('label')] += 1
        if frameTime != 0:
            cv2.waitKey(frameTime)
        frameCounter+=1


    capture.release()
    cv2.destroyAllWindows()


try:
    main()
except KeyboardInterrupt:
    exit(0)

exit(0)
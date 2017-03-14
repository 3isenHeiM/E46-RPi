#!/usr/bin/env python
# -*- coding: utf-8 -*-

# IMPORTS
import os
import sys
import time
from mpd import (MPDClient, CommandError)
from socket import error as SocketError
from tinytag import TinyTag


##
HOST = 'localhost'
PORT = '6600'
PASSWORD = False
CON_ID = {'host':HOST, 'port':PORT}
##

## BUSINESS CD BUTTONS
B1 = 'i'
B2 = 'p'
B3 = 'n'
B4 = 'v'
B5 = 's'
B6 = 'q'
Bnext = '>'
Bprev = '<'
Bplus = '+'
Bminus = '-'
Brnd = 'r'

# TODO add long push and short push to add functions
# TODO Beware of the path of the files
# TODO Add the timer to come back to the original display of the song.
# TODO defind other displaytyle to browse via Artists, and on on
# TODO Define a info Mode to display titles/time, artist...


rootDir = '/home/pi/Music'


# Choose to display when browsing : artist /title / (following TinyTag)
displaytype = 'title'


def scan_dir(files, dir):

	for f in os.listdir(dir):
		f = os.path.join(dir, f)
		if os.path.isdir(f):
			print("Folder found : %s"% f)
			scan_dir(files, f)
		# Make a list of all mp3 files
		elif os.path.splitext(f)[1] == ".mp3":
			files.append(f)
	return(files)


def next_element(currentElement, up) :
	try :
		(_, dirnames, filenames) = iter(os.walk(os.path.dirname(currentElement))).next()
		dirnames.sort()
		filenames.sort()
		listElements = dirnames + filenames
	except StopIteration:
		# If directory to walk on does not exists :
		listElements = currentElement

	# Remove hidden elements (start with .)
	listElements = [x for x in listElements if not x.startswith('.')]

	# Find the index in the list of the displayed name.
	(basepath, elementName) = os.path.split(currentElement)
	indexInList = listElements.index(elementName)

	# Set the way to parse the list.
	if not up :
		if indexInList != len(listElements) -1 :
			nextElement = listElements[indexInList+1]
		else :
			nextElement = listElements[0]
	else :
		if indexInList != 0 :
			nextElement = listElements[indexInList-1]
		else :
			nextElement = listElements[-1]

	toReturn = os.path.join(basepath, nextElement)
	return(toReturn)

## Some functions
def mpdConnect(client, con_id):
	# Simple wrapper to connect MPD.
	try:
		client.connect(**con_id)
	except SocketError:
		return False
	return True

def mpdAuth(client, secret):
	# Authenticate
	try:
		client.password(secret)
	except CommandError:
		return False
	return True
##

def main():
	currentDir = rootDir
	playDir = rootDir
	displayDir = 'hello'
	toScreen = 'Welcome'

	## MPD object instance
	client = MPDClient()
	if mpdConnect(client, CON_ID):
		print('Connected to MPD')
		client.update()
		client.rescan()
	else:
		print('Fail to connect MPD server.')
		sys.exit(1)

	# Auth if password is set non False
	if PASSWORD:
		if mpdAuth(client, PASSWORD):
			print('Pass auth!')
		else:
			print('Error trying to pass auth.')
			client.disconnect()
			sys.exit(2)


	watchdog=False
	currentFile = rootDir

	# Get the stats if Player is stopped
	status = client.status()
	if (status['state'] !='stop'):
		currentFile = os.path.join(rootDir, client.currentsong()['file'])

	displayDir = currentFile	#os.path.basename(currentFile)


	while(not watchdog):
		print('----- BEGIN -----')
		status = client.status()

		print('|  \x1B[0;31;40m' + toScreen + '\x1B[0m  |')
		#print(toScreen)

		# Wait for event.
		#client.idle()
		#client.send_idle()

		if (status['state']=='play' or status['state']=='pause'):
			currentFile = os.path.join(rootDir, client.currentsong()['file'])

		print('currentFile \t%s'%currentFile)
		print('displayDir \t%s' %displayDir)


		text=raw_input("(n)ext (p)lay/pause (s)top (r)andom pre(v)ious (q)uit volume : u/d ")



		#if (text == B1):
		#print(client.currentsong())

		if (text == B3):
			client.next()
			toScreen = client.currentsong()['title']

		if (text == B2):
			if (status['state']=='play'):
				client.pause()
				toScreen = "Pause"
			elif (status['state']=='stop' or status['state']=='pause'):
				client.play()
				toScreen = client.currentsong()['title']

		if (text == Brnd):
			if (status['random']=='0'):
				client.random(1)
				toScreen ='Rnd on'
				#print(status['random'])
			elif (status['random']=='1'):
				client.random(0)
				toScreen ='Rnd off'

		if (text == B4):
			client.previous()
			toScreen = client.currentsong()['title']

		if (text == B5):
			client.stop()
			toScreen = 'Stopped'

		if (text == B6):
			client.stop()
			watchdog=True

		if (text == "u"):
			status = client.status()
			volume = int(status['volume'])
			if (volume < 95):
				volume += 5
				toScreen ="Vol "+ str(volume)
			else :
				volume = 100
				toScreen = "Vol max"
			client.setvol(volume)

		if (text == "d"):
			status = client.status()
			volume = int(status['volume'])
			if (volume > 5):
				volume -= 5
				toScreen ="Vol "+ str(volume)
			else :
				volume = 0
				toScreen = "Vol off"
			client.setvol(volume)

		if (text == Bplus):
			if displayDir != rootDir :
				displayDir = next_element(displayDir, 0)
			#print displayDir
			if displayDir.endswith('.mp3') :
				# Display the artist ID3 tag of the next song.
				tag = TinyTag.get(displayDir)
				if tag.title :
					toScreen = tag.title	#getattr(self,displaytype)
				else : toScreen = os.path.basename(displayDir)
			else :
				(_, toScreen )= os.path.split(displayDir)


		if (text == Bminus):
			if displayDir != rootDir :
				# Get the next elements in the same folder
				displayDir = next_element(displayDir, 1)

			if displayDir.endswith('.mp3') :
				# Display the artist ID3 tag of the next song.
				tag = TinyTag.get(displayDir)
				toScreen = tag.title	#getattr(self,displaytype)
			else :
				(_, toScreen )= os.path.split(displayDir)

		if (text == Bprev):
			#print rootDir
			if displayDir != rootDir :
				displayDir = os.path.dirname(displayDir)
				toScreen = os.path.basename(displayDir)
			# print displayDir
			# toScreen = os.path.basename(displayDir)

		if (text == Bnext):
			if os.path.isdir(displayDir) :
			# if folder, enter it
				sortedFileList = sorted(os.listdir(displayDir))
				# Check is not empty folder.
				if sortedFileList != []:
					#remove items beginning with '.'
					sortedFileList = [x for x in sortedFileList if not x.startswith('.') ]
					#print sortedFileList

					firstElement = os.path.join(displayDir,sortedFileList[0])
					if os.path.isdir(firstElement) :
						#print('firstFolder \t%s' %os.path.relpath(firstElement, displayDir))
						toScreen = os.path.basename(firstElement)
						#print('toScreen \t%s' %toScreen)
					else :
						(_, file_extension) = os.path.splitext(firstElement)
						if file_extension == '.mp3' :
							tag = TinyTag.get(firstElement)
							if tag.title :
								toScreen = tag.title
							else :
								toScreen = os.path.basename(firstElement)
					displayDir = firstElement

			elif (os.path.isfile(displayDir) ):

				(_, file_extension) = os.path.splitext(displayDir)
				if file_extension == '.mp3' :
					# if .mp3 file, clear next tracks, add it and play it
					client.clear()

					# Add songs after it in the playlist
					(_, _, filenames) = os.walk(os.path.dirname(displayDir)).next()
					filenames.sort()

					# get the File name :
					(absDirName, fileName) = os.path.split(displayDir)

					# Find its position in the folder array
					indexFile = filenames.index(fileName)

					# Add the next songs in the playlist (+1 because current file already added)
					for index in range(0, len(filenames)) :
						#print('index  \t%s' %index)
						file2add = os.path.join(os.path.relpath(absDirName, rootDir), filenames[index])

						# Remove './' if files begins with it.
						if file2add[0:2] == "./" :
							tempString = ''
							tempString = file2add[2:]
							file2add = tempString

						#print('file2add  \t%s' %file2add)
						client.add(file2add)


					client.play(indexFile)



	## disconnect
	client.disconnect()
	print("Disconnected")
	sys.exit(0)

if __name__ == "__main__":
	main()

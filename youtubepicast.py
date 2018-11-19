debugLevel = 0
screenName = ""
screenApp = ""
screenId = ""
screenUid = "2a026ce9-4429-4c5e-8ef5-0101eddf5671"
bindVals = {}
currentCmdIndex = 999
ofs = 0
playlistinfo = {}
curTime = 0
startTime = 0
curVideoId = ""
curVideo = ""
ctt = ""
curListId = ""
curListVideos = ""
curList = []
curIndex = 0
playState = "1"
currentVolume = "100"


def main():
	global debugLevel, screenName, screenApp, screenId, screenUid, bindVals, ofs

	if screenId == "":
		screenId = requests.get("https://www.youtube.com/api/lounge/pairing/generate_screen_id").text
	print "screen_id: " + screenId

	loungeToken = requests.post("https://www.youtube.com/api/lounge/pairing/get_lounge_token_batch",
		data= {
			'screen_ids': screenId
		}).json()['screens'][0]
	print "lounge_token: " + loungeToken['loungeToken'] + " " + str(int(loungeToken['expiration']) / 1000)

	bindVals = {
		"device":        "LOUNGE_SCREEN",
		"id":            screenUid,
		"name":          screenName,
		"app":           screenApp,
		"theme":         "cl",
		"mdx-version":   "2",
		"loungeIdToken": loungeToken['loungeToken'],
		"VER":           "8",
		"v":             "2",
		"RID":           "1337",
		"AID":           "42",
		"zx":            "xxxxxxxxxxxx",
		"t":             "1",
	}

	r = requests.post("https://www.youtube.com/api/lounge/bc/bind?{}".format(urllib.urlencode(bindVals)),
		data= {
			'count': {"0"}
		}).text
	decodeBindStream(r)


	newpid = os.fork()
	if newpid != 0:
		while True:
			pairingCode(loungeToken['loungeToken'],loungeToken['screenId'])
			time.sleep(300)

	
	while True:
		errCount = 0
		bindValsGet = copy.copy(bindVals)
		bindValsGet["RID"] = "rpc"
		bindValsGet["CI"] = "0"
		response = requests.get("https://www.youtube.com/api/lounge/bc/bind?{}".format(urllib.urlencode(bindValsGet)), stream=True)


		# TODO: thread for every chunck of data readed
		for data in response.iter_content(9999):
			ofs+=1
			decodeBindStream(data)
			


def pairingCode(loungeToken, screenId):
	global screenApp

	code = requests.post("https://www.youtube.com/api/lounge/pairing/get_pairing_code?ctx=pair",
		data = {
			"access_type":  "permanent",
			"app":          screenApp,
			"lounge_token": loungeToken,
			"screen_id":    screenId,
			"screen_name":  screenName,
		}).text

	print "pairing_code " + code[0:3] + "-" + code[3:6] + "-" + code[6:9] + "-" + code[9:]
	return

def decodeBindStream(r):
	for line in ast.literal_eval("["+r.split('[', 1)[1]):
		genericCmd(int(line[0]), line[1][0], line[1][1:])
	return


def genericCmd(index, cmd, paramsList):
	global currentCmdIndex, bindVals, curTime, curVideoId, curListId, ctt, curIndex, currentVolume, curVideo, curListVideos, curList, playState, startTime

	#dbgPrintln(index, cmd, paramsList)
	if currentCmdIndex > 0 and index <= currentCmdIndex:
		dbprintlng("Already seen " + str(index))

	currentCmdIndex = index
	if cmd == "noop":
		print "noop"

		try:


			duration = str(curVideo["duration"]).split(":")
			duration = int(duration[0])*60 + int(duration[1])

			# start getting the real url of next video 45 seconds before the current one ends
			if time.time() > (startTime + duration) - 45:

				if curIndex+1 < len(curList) :
					print "next"
					curIndex += 1
					curTime = 0
					
					curVideoId = curList[curIndex]
					curVideo = curListVideos[curIndex]
					
					url = os.popen('youtube-dl -g -f mp4 https://www.youtube.com/watch?v='+curVideoId).read()

					os.system('killall omxplayer.bin')
					os.system('omxplayer -o hdmi "' + str(url.strip("\n")) + '" < /dev/null &')

					startTime = time.time()
					
					postBind("nowPlaying", {
						"videoId":      curVideoId,
						"currentTime":  "0",
						"ctt":          ctt,
						"listId":       curListId,
						"currentIndex": str(curIndex),
						"state":        "1",
					})
					playState = "1"
					postBind("onStateChange", {
						"currentTime": "0",
						"state":       "1",
						"duration":    str(curVideo["duration"]),
						"cpn":         "foo",
					})


					print "video " + curVideoId
				else:
					postBind("nowPlaying", {})
					print "stop"


		except Exception as e:
			pass

	elif cmd == "c":
		bindVals['SID'] = str(paramsList[0])
		print "option_sid " + str(paramsList[0])
	elif cmd == "S":
		bindVals['gsessionid'] = str(paramsList[0])
		print "option_gsessionid " + str(paramsList[0])
	elif cmd == "remoteConnected":
		print "remote_join " + str(paramsList[0]["id"]) + " " + str(paramsList[0]["name"])
	elif cmd == "remoteDisconnected":
		print "remote_leave " + str(paramsList[0]["id"])
	elif cmd == "getNowPlaying":

		curTime = 1

		if curVideoId == "":
			postBind("nowPlaying", {})
		else:
			postBind("nowPlaying", {
				"videoId":      curVideoId,
				"currentTime":  str(curTime),
				"ctt":          ctt,
				"listId":       curListId,
				"currentIndex": str(curIndex),
				"state":        playState,
			})

	elif cmd == "setPlaylist":
		data = paramsList[0]
		curVideoId = data["videoId"]
		curListId = data["listId"]
		info = getListInfo(curListId)
		curListVideos = info["video"]
		currentTime = data["currentTime"]
		videoIds = data["videoIds"]
		curList = videoIds.split(",")
		curVideo = curListVideos[0]

		if data["currentIndex"] != None :
			curIndex = int(data["currentIndex"])

		curTime = float(currentTime)

		ctt = data["ctt"]

		print "set playlist"

		url = os.popen('youtube-dl -g -f mp4 https://www.youtube.com/watch?v='+curVideoId).read()

		os.system('killall omxplayer.bin')
		os.system('omxplayer -o hdmi "' + str(url.strip("\n")) + '" < /dev/null &')
		
		startTime = time.time()

		postBind("nowPlaying", {
			"videoId":      curVideoId,
			"currentTime":  currentTime,
			"ctt":          ctt,
			"listId":       curListId,
			"currentIndex": str(curIndex),
			"state":        "1",
		})
		playState = "1"
		postBind("onStateChange", {
			"currentTime": str(currentTime),
			"state":       "1",
			"duration":    str(curVideo["duration"]),
			"cpn":         "foo",
		})


		print "video " + curVideoId
		

	elif cmd == "updatePlaylist":

		data = paramsList[0]
		curListId = data["listId"]
		if "videoIds" in data :
			videoIds = data["videoIds"]
			curList = videoIds.split(",")
			if curIndex >= len(curList) :
				curIndex = len(curList) - 1
		else :
			curList = []
			curIndex = 0
		info = getListInfo(curListId)
		curListVideos = info["video"]

		print "playlist updated"



	elif cmd == "play":
		
		omxdbus("org.mpris.MediaPlayer2.Player.PlayPause")

		playState = "1"
		startTime = time.time() - curTime

		postBind("onStateChange", {
			"currentTime": str(curTime),
			"state":       "1",
			"duration":    str(curVideo["duration"]),
			"cpn":         "foo",
		})

		print "play"

	elif cmd == "pause":

		omxdbus("org.mpris.MediaPlayer2.Player.PlayPause")
		
		playState = "2"
		curTime = time.time() - startTime
		postBind("onStateChange", {
			"currentTime": str(curTime),
			"state":       "2",
			"duration":    str(curVideo["duration"]),
			"cpn":         "foo",
		})

	
	elif cmd == "seekTo":

		newTime = paramsList[0]["newTime"]
		startTime = time.time() - float(newTime)
		omxdbus('org.mpris.MediaPlayer2.Player.SetPosition objpath:/not/used int64:'+newTime+'000000')

		postBind("onStateChange", {
			"currentTime": newTime,
			"state":       playState,
			"duration":    str(curVideo["duration"]),
			"cpn":         "foo",
		})

		print "seek to " + str(newTime)
	elif cmd == "stopVideo":

		omxdbus("org.mpris.MediaPlayer2.Player.Stop")
		
		postBind("nowPlaying", {})
		print "stop"
	elif cmd == "next":

		print "next"

		if curIndex+1 < len(curList) :
			curIndex += 1
			curTime = 0
			
			curVideoId = curList[curIndex]
			curVideo = curListVideos[curIndex]
			
			url = os.popen('youtube-dl -g -f mp4 https://www.youtube.com/watch?v='+curVideoId).read()

			os.system('killall omxplayer.bin')
			os.system('omxplayer -o hdmi "' + str(url.strip("\n")) + '" < /dev/null &')
			
			startTime = time.time()

			postBind("nowPlaying", {
				"videoId":      curVideoId,
				"currentTime":  "0",
				"listId":       curListId,
				"ctt":          ctt,
				"currentIndex": str(curIndex),
				"state":        "1",
			})
			playState = "1"
			postBind("onStateChange", {
				"currentTime": "0",
				"state":       "1",
				"duration":    str(curVideo["duration"]),
				"cpn":         "foo",
			})


			print "video " + curVideoId

	elif cmd == "next" and alreadyNext:
		alreadyNext = False


	elif cmd == "previous":

		print "previous"
		
		if curIndex > 0:
			curIndex -= 1
			curTime = 0
			
			curVideoId = curList[curIndex]
			curVideo = curListVideos[curIndex]
			
			url = os.popen('youtube-dl -g -f mp4 https://www.youtube.com/watch?v='+curVideoId).read()

			os.system('killall omxplayer.bin')
			os.system('omxplayer -o hdmi "' + str(url.strip("\n")) + '" < /dev/null &')

			startTime = time.time()
			
			postBind("nowPlaying", {
				"videoId":      curVideoId,
				"currentTime":  "0",
				"listId":       curListId,
				"ctt":          ctt,
				"currentIndex": str(curIndex),
				"state":        "1",
			})
			playState = "1"
			postBind("onStateChange", {
				"currentTime": "0",
				"state":       "1",
				"duration":    str(curVideo["duration"]),
				"cpn":         "foo",
			})


			print "video " + curVideoId

	elif cmd == "getVolume":
		postBind("onVolumeChanged", {"volume": currentVolume, "muted": "false"})
	elif cmd == "setVolume":
		currentVolume = paramsList[0]["volume"]

		
		volume = '1.0'
		if int(currentVolume) < 100:
			volume = '0.'+currentVolume

		omxdbus('org.freedesktop.DBus.Properties.Set string:"org.mpris.MediaPlayer2.Player" string:"Volume" double:'+volume)

		print "set_volume " + currentVolume
		postBind("onVolumeChanged", {"volume": currentVolume, "muted": "false"})

	else:
		pass
	return

def omxdbus(dbus):
	os.system('export DBUS_SESSION_BUS_ADDRESS=`cat /tmp/omxplayerdbus.${USER:-root}`; export DBUS_SESSION_BUS_PID=`cat /tmp/omxplayerdbus.${USER:-root}.pid`; dbus-send --print-reply=literal --session --reply-timeout=100 --dest=org.mpris.MediaPlayer2.omxplayer /org/mpris/MediaPlayer2 '+dbus+' >/dev/null')


def postBind(sc, params):
	global ofs, bindVals
	postVals = {
		"count": "1",
		"ofs": str(ofs),
		"req0__sc": sc
	}
	for param in params:
		postVals["req0_"+param] = params[param]
	bindVals["RID"] = "1337"
	return requests.post("https://www.youtube.com/api/lounge/bc/bind?{}".format(urllib.urlencode(bindVals)), data=postVals)


def getListInfo(listId):
	return requests.get("https://www.youtube.com/list_ajax?style=json&action_get_list=1&list=" + listId).json()


def dbprintlng(line):
	global debugLevel
	if debugLevel >= 1:
		if debugLevel >= 2:
			print "debug - " + str(time.strftime("%H:%M:%S")) + " - " + line
		else:
			print "debug - " + line


if __name__=="__main__":
	import argparse, requests, urllib, ast, time, os, copy

	parser = argparse.ArgumentParser(description='Cast youtube to your tv')
	parser.add_argument('-d', dest='debugLevel', type=int, default=0, help='Debug information level. 0 = off; 1 = full cmd info; 2 = timestamp prefix')
	parser.add_argument('-n', dest='screenName', type=str, default="python youtube TV", help='Display Name')
	parser.add_argument('-i', dest='screenApp', type=str, default="python-youtube-TV-v1", help='App Name')
	parser.add_argument('-s', dest='screenId', type=str, default="", help='Screen ID (will be generated if empty)')

	args = parser.parse_args()
	debugLevel = args.debugLevel
	screenName = args.screenName
	screenApp = args.screenApp
	screenId = args.screenId
	main()
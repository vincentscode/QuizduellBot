import os
import base64
import cv2
import subprocess
import numpy as np
import threading
from PIL import Image
import pytesseract
import argparse
import cv2
import os
import requests 
from bs4 import BeautifulSoup
from googlesearch import search 
from fuzzysearch import find_near_matches
import threading as th

keep_going = True
def key_capture_thread():
	global keep_going
	while True:
		input()
		keep_going = False

th.Thread(target=key_capture_thread, args=(), name='key_capture_thread', daemon=True).start()


def sendTouch(touchX, touchY):
	os.system(f"adb shell input tap {touchX} {touchY}")

def sendTap(event,x,y,flags,param):
	if event == cv2.EVENT_LBUTTONDOWN:
		print("send tap", x, y)
		sendTouch(x/scale_factor, y/scale_factor)

cv2.namedWindow('Android')
cv2.setMouseCallback('Android', sendTap)

image = None
scale_factor = 0.25

class ImageUpdaterThread(threading.Thread):
	def run(self):
		global image
		while True:
			pipe = subprocess.Popen("adb shell screencap -p", stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
			image_bytes = pipe.stdout.read().replace(b'\r\n', b'\n')
			image = cv2.imdecode(np.fromstring(image_bytes, np.uint8), cv2.IMREAD_COLOR)

updaterThread = ImageUpdaterThread()
updaterThread.start()

question_coords_fac025 = [15, 113, 236, 137]
question_coords_fac025 = [int(y / 0.25) for y in question_coords_fac025]

answer_coords_fac025 = [
	[5, 272, 128, 90],
	[133, 272, 128, 90],
	[5, 363, 128, 90],
	[133, 363, 128, 90],
]
answer_coords_fac025 = [[int(y / 0.25) for y in x] for x in answer_coords_fac025]

border = 25

last_q = ""
while True:
	if image is not None:
		resz = image # cv2.resize(image, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_AREA)
		
		itr = 0
		answers = {}
		for acoords in answer_coords_fac025:
			sub = cv2.bitwise_not(cv2.cvtColor(resz[acoords[1]+border:acoords[1]+acoords[3]-border, acoords[0]+border:acoords[0]+acoords[2]-border], cv2.COLOR_BGR2GRAY))
			
			sub = cv2.threshold(sub, 0, 255,
				cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
			itr += 1
			# cv2.imshow(f"Answer {itr}", sub)
			# cv2.moveWindow(f"Answer {itr}", 400+150*itr, 100)

			cv2.imwrite(f"tempansw{itr}.png", sub)
			text = pytesseract.image_to_string(Image.open(f"tempansw{itr}.png"))
			#os.remove(f"tempansw{itr}.png")
			answers[text] = 0

		sub = cv2.cvtColor(resz[question_coords_fac025[1]:question_coords_fac025[1]+question_coords_fac025[3], question_coords_fac025[0]:question_coords_fac025[0]+question_coords_fac025[2]], cv2.COLOR_BGR2GRAY)
		cv2.imshow("Question", sub)

		cv2.imwrite(f"quest.png", sub)
		question = pytesseract.image_to_string(Image.open(f"quest.png")).replace("\n", " ").replace("\r", " ")
		#os.remove(f"tempansw{itr}.png")

		if last_q != question and len(question) > 4 and len(''.join(list(answers.keys()))) > 7:
			print("OCR", "->", question, "(" + ', '.join(answers.keys()) + ")")
			for result_url in search(question, tld="de", num=5, stop=5, pause=2):
				try:
					print(result_url)
					if "pdf" in result_url:
						continue 
					r = requests.get(result_url)
					for ak in answers:
						answers[ak] += r.text.count(ak)
				except:
					pass
				for a in sorted(answers.items(), key=lambda kv: kv[1], reverse=True):
					print(a[0], a[1])
			keep_going = True
		last_q = question
		# cv2.imshow("Android", resz)

	if cv2.waitKey(2) & 0xFF == 27:
		break
cv2.destroyWindow("")
#! python3
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

from keycodes import *  # for VK_XXX constants
from textService import *
from .cin import Cin

import io
import os.path
import time

# from libchewing/include/global.h
CHINESE_MODE = 1
ENGLISH_MODE = 0
FULLSHAPE_MODE = 1
HALFSHAPE_MODE = 0

# 選單項目和語言列按鈕的 command ID
ID_SWITCH_LANG = 1
ID_SWITCH_SHAPE = 2
ID_SETTINGS = 3
ID_MODE_ICON = 4

MAX_CHAR_LENGTH = 5

class TerryCJTextService(TextService):
	# compositionChar: a, b, c, d...
	# compositionString: 日, 月, 金, 木, 水, 火, 土...
	compositionChar = ''

	def __init__(self, client):
		TextService.__init__(self, client)
		self.curdir = os.path.abspath(os.path.dirname(__file__))
		self.datadir = os.path.join(self.curdir, "data")
		self.icon_dir = self.curdir
		self.candidates = []
		self.langMode = CHINESE_MODE
		self.shapeMode = -1
		self.lastKeyDownCode = 0
		self.lastKeyDownTime = 0.0

		newcj_path = os.path.join(self.curdir, "thcj.cin")
		with io.open(newcj_path, encoding='utf-8') as fs:
			self.cin = Cin(fs)
		# TODO: Can newcj.cin be loaded only at the first time the input method is initialized?
		print('Finish loading')

	# 輸入法被使用者啟用
	def onActivate(self):
		TextService.onActivate(self)
		self.customizeUI(candFontSize=24, candPerRow=1)

		if self.cin.getSelection():
			self.setSelKeys(self.cin.getSelection())

		# 切換中英文

		icon_name = "chi.ico" if self.langMode == CHINESE_MODE else "eng.ico"
		self.addButton("switch-lang",
			icon=os.path.join(self.icon_dir, icon_name),
			tooltip="中英文切換",
			commandId=ID_SWITCH_LANG
		)

		# Windows 8 以上已取消語言列功能，改用 systray IME mode icon
		if self.client.isWindows8Above:
			self.addButton("windows-mode-icon",
				icon=os.path.join(self.icon_dir, icon_name),
				tooltip="中英文切換",
				commandId=ID_MODE_ICON
			)

	def onDeactivate(self):
		TextService.onDeactivate(self)
		self.lastKeyDownCode = 0
		self.removeButton("switch-lang")

	def filterKeyUp(self, keyEvent):
		# 剛才最後一個按下的鍵，和現在放開的鍵，都是 Shift
		if self.lastKeyDownCode == VK_SHIFT and keyEvent.keyCode == VK_SHIFT:
			pressedDuration = time.time() - self.lastKeyDownTime
			# 按下和放開的時間相隔 < 0.5 秒
			if pressedDuration < 0.5:
				self.toggleLanguageMode()  # 切換中英文模式
		self.lastKeyDownCode = 0
		self.lastKeyDownTime = 0.0
		return False

	def filterKeyDown(self, keyEvent):
		# 使用者開始輸入，還沒送出前的編輯區內容稱 composition string
		# isComposing() 是 False，表示目前編輯區是空的
		# 若正在編輯中文，則任何按鍵我們都需要送給輸入法處理，直接 return True
		# 另外，若使用 "`" key 輸入特殊符號，可能會有編輯區是空的
		# 但選字清單開啟，輸入法需要處理的情況
		self.lastKeyDownCode = keyEvent.keyCode
		if self.lastKeyDownTime == 0.0:
			self.lastKeyDownTime = time.time()

		# TODO: 是否讓Ctrl+A, Ctrl+C, Ctrl+V 在這時可以用？
		if self.isComposing() or self.showCandidates:
			return True
		# --------------   以下都是「沒有」正在輸入中文的狀況   --------------

		# 如果按下 Alt, Ctrl, Shift 鍵
		if keyEvent.isKeyDown(VK_MENU) or keyEvent.isKeyDown(VK_CONTROL) or keyEvent.isKeyDown(VK_SHIFT):
			return False

		# 不論中英文模式，NumPad 都允許直接輸入數字，輸入法不處理
		if keyEvent.isKeyToggled(VK_NUMLOCK):  # NumLock is on
			# if this key is Num pad 0-9, +, -, *, /, pass it back to the system
			if keyEvent.keyCode >= VK_NUMPAD0 and keyEvent.keyCode <= VK_DIVIDE:
				return False  # bypass IME

		# 不管中英文模式，只要是全形，輸入法都需要進一步處理(英數字從半形轉為全形)
		if self.shapeMode == FULLSHAPE_MODE:
			return (keyEvent.isPrintableChar() or keyEvent.keyCode == VK_SPACE)
		# --------------   以下皆為半形模式   --------------

		# 如果是英文半形模式，輸入法不做任何處理
		if self.langMode == ENGLISH_MODE:
			return False
		# --------------   以下皆為中文模式   --------------

		# 中文模式下開啟 Capslock，須切換成英文
		if keyEvent.isKeyToggled(VK_CAPITAL):
			# 如果此按鍵是英文字母，中文模式下要從大寫轉小寫，需要輸入法處理
			if keyEvent.isChar() and chr(keyEvent.charCode).isalpha():
				return True
			# 是其他符號或數字，則視同英文模式，不用處理
			else:
				return False

		# 檢查按下的鍵是否為自由大新定義的符號
		if self.cin.isInKeyName(chr(keyEvent.charCode).lower()):
			return True

		# 其餘狀況一律不處理，原按鍵輸入直接送還給應用程式
		return False

	def onKeyDown(self, keyEvent):
		candidates = self.candidates
		# 大寫 Decimal
		charCode = keyEvent.charCode
		# 小寫 Decimal
		keyCode = keyEvent.keyCode
		charStr = chr(charCode)
		charStrLow = charStr.lower()

		if not self.isComposing():
			if keyCode == VK_RETURN or keyCode == VK_BACK:
				return False

		if self.cin.isInKeyName(charStrLow):
			self.compositionChar += charStrLow
			keyname = self.cin.getKeyName(charStrLow)
			self.setCompositionString(self.compositionString + keyname)
			self.setCompositionCursor(len(self.compositionString))

		if keyCode == VK_ESCAPE and (self.showCandidates or len(self.compositionChar) > 0):
			self.setShowCandidates(False)
			self.resetComposition()

		if self.cin.isInCharDef(self.compositionChar):
			candidates = self.cin.getCharDef(self.compositionChar)
		elif len(self.compositionChar) > MAX_CHAR_LENGTH:
			self.resetComposition()

		if candidates:
			print("candidates are {}".format(",".join(candidates)))
			self.setCandidateList(candidates)
			self.setShowCandidates(True)
			candCursor = self.candidateCursor  # 目前的游標位置
			candCount = len(self.candidateList)  # 目前選字清單項目數
			# TODO: use %selkey in newcj.cin instead of ord('0') and ord('9')
			if keyCode >= ord('0') and keyCode <= ord('9'):
				i = keyCode - ord('1')
				if i < len(candidates):
					cand = candidates[i]
					self.setCommitString(cand)
					self.resetComposition()
			elif keyCode == VK_UP:  # 游標上移
				if candCursor > 0:
					candCursor -= 1
			elif keyCode == VK_DOWN:  # 游標下移
				if (candCursor + 1) < candCount:
					candCursor += 1
			elif keyCode == VK_RETURN:  # 按下 Enter 鍵
				# 找出目前游標位置的選字鍵 (1234..., asdf...等等)
				cand = candidates[candCursor]
				self.setCommitString(cand)
				self.resetComposition()
				candCursor = 0
			 # 更新選字視窗游標位置
			self.setCandidateCursor(candCursor)
		else:
			self.setShowCandidates(False)

		if keyCode == VK_OEM_1 or keyCode == VK_OEM_2 or keyCode == VK_OEM_5 or keyCode == VK_OEM_COMMA or keyCode == VK_OEM_PERIOD :
			if len(candidates) >= 1:
				self.setCommitString(candidates[0])
				self.resetComposition()

		# 按下空白或字碼超過5個時，將組成的字送出
		if keyCode == VK_SPACE or len(self.compositionString) > MAX_CHAR_LENGTH:
			if len(candidates) >= 1:
				self.setCommitString(candidates[0])
				self.resetComposition()
			else:
				self.showMessage("查無字根...", 3)
		# 刪掉一個字碼
		elif keyCode == VK_BACK:
			if self.compositionString != "":
				self.showMessage("", 0)
				self.setCompositionString(self.compositionString[:-1])
				self.compositionChar = self.compositionChar[:-1]
				if self.cin.isInCharDef(self.compositionChar):
					candidates = self.cin.getCharDef(self.compositionChar)
					self.setCandidateList(candidates)
					self.setShowCandidates(True)
				else:
					self.setShowCandidates(False)
		return True

	def onCommand(self, commandId, commandType):
		print("onCommand", commandId, commandType)

		if commandId == ID_SWITCH_LANG:  # 切換中英文模式
			self.toggleLanguageMode()
		elif commandId == ID_MODE_ICON:  # windows 8 mode icon
			self.toggleLanguageMode()  # 切換中英文模式

	def isNumberChar(self, keyCode):
		return keyCode >= 0x30 and keyCode <= 0x39

	def resetComposition(self):
		self.compositionChar = ''
		self.setCompositionString('')
		self.setShowCandidates(False)

	# 依照目前輸入法狀態，更新語言列顯示
	def updateLangButtons(self):
		icon_name = "chi.ico" if self.langMode == CHINESE_MODE else "eng.ico"
		icon_path = os.path.join(self.icon_dir, icon_name)
		self.changeButton("switch-lang", icon=icon_path)

		if self.client.isWindows8Above:  # windows 8 mode icon
			# FIXME: we need a better set of icons to meet the
			#        WIndows 8 IME guideline and UX guidelines.
			self.changeButton("windows-mode-icon", icon=icon_path)

	# 切換中英文模式
	def toggleLanguageMode(self):
		if self.langMode == CHINESE_MODE:
			self.langMode = ENGLISH_MODE
		elif self.langMode == ENGLISH_MODE:
			self.langMode = CHINESE_MODE
		self.updateLangButtons()

		# 鍵盤開啟/關閉時會被呼叫 (在 Windows 10 Ctrl+Space 時)
	def onKeyboardStatusChanged(self, opened):
		TextService.onKeyboardStatusChanged(self, opened)
		if opened: # 鍵盤開啟
			self.resetComposition()
		else: # 鍵盤關閉，輸入法停用
			# 若選字中，隱藏選字視窗
			if self.showCandidates:
				self.setShowCandidates(False)
			# self.hideMessage() # hide message window, if there's any
			self.compositionChar = ''
			self.setCompositionString('')

		# Windows 8 systray IME mode icon
		if self.client.isWindows8Above:
			# 若鍵盤關閉，我們需要把 widnows 8 mode icon 設定為 disabled
			self.changeButton("windows-mode-icon", enable=opened)
			self.changeButton("switch-lang", enable=opened)
		# FIXME: 是否需要同時 disable 其他語言列按鈕？
		
import os

def existKey(map, key):
	return True if (key in map) else False;

def splitByTabSpace(line):
	tokens = line.split(' ')
	if len(tokens) > 1:
		return tokens
	else:
		return line.split('\t')

KEYNAME_BEGIN = 0x01
KEYNAME_END = 0x02
CHARDEF_BEGIN = 0x03
CHARDEF_END = 0x04



class NewCJContext:
	chardef = dict()
	keyname = dict()
	properties = dict()
	state = ''

	def __init__(self):
		pass

	def loadTokens(self):
		lib_path = os.path.join(os.path.dirname(__file__), "newcj.txt")
		fo = open(lib_path, mode="r", encoding="utf-8")
		print("Name of the file: ", fo.name);
		while True:
			line = fo.readline();
			if not line:
				break;
			# print("Read Line: %s" % (line))
			tokens = splitByTabSpace(line)
			if tokens[0][0] == '%':
				# properties
				if tokens[0][1:] == 'keyname':
					tokens[1] = tokens[1].replace('\n', '')
					if tokens[1] == 'begin':
						state = KEYNAME_BEGIN
					elif tokens[1] == 'end':
						state = KEYNAME_END
				elif tokens[0][1:] == 'chardef':
					tokens[1] = tokens[1].replace('\n', '')
					if tokens[1] == 'begin':
						state = CHARDEF_BEGIN
					elif tokens[1] == 'end':
						state = CHARDEF_END
			elif(tokens[0][0] == '#'):
				# comment
				continue
			else:
				if state == CHARDEF_BEGIN:
					outputWord = tokens[1].replace('\n', '');
					if existKey(self.chardef, tokens[0]):
						self.chardef[tokens[0]].append(outputWord);
					else:
						# new token
						self.chardef[tokens[0]] = [outputWord];
				elif state == KEYNAME_BEGIN:
					outputWord = tokens[1].replace('\n', '');
					self.keyname[tokens[0]] = outputWord;

		# Close opend file
		fo.close();

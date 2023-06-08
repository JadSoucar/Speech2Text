import os, sys
import requests # conda
import re
import string
from tqdm import tqdm

class Pronounce(object):
	url = "http://www.speech.cs.cmu.edu/cgi-bin/tools/lmtool/run"
	dict_re = re.compile(r"\d+\.dic")
	other_pr = re.compile(r"(.*)\(\d+\)$")
	vowel_re = re.compile(r"AA|AE|AH|AO|AW|AY|EH|ER|EY|IH|IY|OW|OY|UH|UW")

	def __init__(self, words=None):
		if words:
			self.words = words
		else:
			self.words = []

	def add(self, word):
		self.words.append(word)

	def p(self, one_letter = False,add_fake_stress=False):
		w_upper = [w.upper() for w in self.words]
		
		punc_map = dict((ord(c), None) for c in string.punctuation)
		w_nopunc = [s.translate(punc_map) for s in w_upper]

		file = {'corpus': ('words.txt', " ".join(w_nopunc))}

		res = requests.post(Pronounce.url,
							data={"formtype": "simple"},
							files=file, allow_redirects=True)
		base_url = res.url
		text = res.text
		dict_path = Pronounce.dict_re.search(text).group(0)
		res = requests.get(base_url + dict_path)
		
		# generate output dict
		pronunciations = {}
		for line in res.text.split('\n'):
			if len(line) > 0:
				pr = line.split('\t')
				match = Pronounce.other_pr.match(pr[0])
				if match:
					pr[0] = match.group(1)
				idx = w_nopunc.index(pr[0])
				orig = self.words[idx]
				upword = w_upper[idx]
				
				if add_fake_stress:
					pr[1] = re.sub(Pronounce.vowel_re, r"\g<0>0", pr[1])
				
				if orig in pronunciations:
					pronunciations[orig].append(pr[1])
				else:
					pronunciations[orig] = [upword, pr[1]]


		output_for_ipa = ''
		for ix,letter in enumerate([w for w in self.words]):
			if letter == '&':
				aph = ['AE1 N D']
			elif letter.isspace():
				aph = ['*']
			else:
				aph = pronunciations[letter]
			

			if ix == 0:
				output_for_ipa = aph[-1]
			else:
				output_for_ipa = output_for_ipa +' * '+ aph[-1]


			if one_letter:
				break

		return  output_for_ipa.strip(' ')


def type_of_word(word):
	#checks if acronym (0) , hybrid acronym (1) , non-acronym (2)
	word = clean(word)
	if word.isupper():
		return 0
	elif sum([1 if sub_word.isupper() else 0 for sub_word in word.split(' ')])>0:
		return 1
	else:
		return 2
	
def clean(word):
	word = word.replace('`','')
	word = word.replace("'",'')
	word = word.replace('*','')
	word = word.replace('^','')
	word = word.replace('-','')
	word = word.replace('.',' ')
	word = word.replace('/','')
	return word

def eng_to_arp(sample):
	sample = sample.lower().strip(' ')
	sample = clean(sample)
	sample = sample.replace('&','and')
	with open('temp.wlist','w') as f:
		f.writelines(sample.split(' '))

	os.system("phonetisaurus-apply --model g2p/Phonetisaurus/example/train/model.fst --word_list temp.wlist > results.wlist")
	os.remove('temp.wlist')
	with open('results.wlist','r') as f:
		data = f.readlines() 

	arp_sample = ''
	for ix,word in enumerate(data):
		arp = re.findall('(?<=\t)[A-Z0-9\s]*',word)[0].replace('\n','')
		if ix == 0:
			arp_sample = arp
		else:
			arp_sample = arp_sample + ' * '+ arp
	
	return arp_sample

	
def get_acronym_arp(word):
	one_letter = False
	word = clean(word).strip(' ')
	if len(word)==1:
		word = word+'A'
		one_letter = True
	pr = Pronounce(word)
	return pr.p(one_letter = one_letter,add_fake_stress = True)


def get_hybrid_arp(word):
	word = clean(word)
	arp_list = []
	for subword in word.split(' '):
		if subword.isupper():
			arp_list.append(get_acronym_arp(subword))
		else:
			arp_list.append(eng_to_arp(subword))
	
	arp = ' * '.join(arp_list)
	return arp


def format_arp(arp):
	form_arp = ' '.join(['{'+subword.strip(' ')+'}' for subword in arp.split('*')])
	form_arp = form_arp.replace('{}','')

	#replacments 
	form_arp = form_arp.replace('{IH1 NG K}','{IH2 N K AO1 R P ER0 EY2 T IH0 D}')
	form_arp = form_arp.replace('{EH1 L T IY1 D IY1}','{L IH1 M IH0 T IH0 D}')
	return form_arp

def get_arp(word,word_type):
	try:
		arp = ''
		if word_type == 0:
			arp = get_acronym_arp(word)
		elif word_type == 1:
			arp = get_hybrid_arp(word)
		elif word_type == 2:
			arp = eng_to_arp(word)
		else:
			arp = 'type_not_suported'

		return format_arp(arp)

	except Exception as e:
		print(e)
		return 'error'



from fastapi import FastAPI
app = FastAPI()


@app.get("/eng2arp/{words}/{output}")
def first_example(words,output):
	all_info = {}
	string_rep = ''
	for word in tqdm(words.split(' ')):
		word_type = type_of_word(word)
		arp = get_arp(word,word_type)
		all_info[word] = arp
		string_rep += (arp + ' ')

	os.remove('results.wlist')

	if output == 'dic':
		return {'arpabet':all_info}
	elif output == 'string':
		return {'arpabet': string_rep}
	else:
		return {'ERROR': "options for output are 'dic' and 'string'"}


if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument('--words', type=str)
	parser.add_argument('--output', type=str)
	args = parser.parse_args()


	all_info = {}
	string_rep = ''
	for word in tqdm(args.words.split(' ')):
		word_type = type_of_word(word)
		arp = get_arp(word,word_type)
		all_info[word] = arp
		string_rep += (arp + ' ')

	os.remove('results.wlist')

	if args.output == 'dic':
		print ({'arpabet':all_info})
	elif args.output == 'string':
		print ({'arpabet': string_rep})
	else:
		print ({'ERROR': "options for output are 'dic' and 'string'"})


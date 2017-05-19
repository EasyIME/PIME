# python3
# Copyright (C) 2017 Hong Jen Yee (PCMan) <pcman.tw@gmail.com>
#
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

import sys
import struct
import math

# reference: https://www.ptt.cc/bbs/Liu/M.1164374563.A.41C.html
# ftp://mail.im.tku.edu.tw/%A7U%B1%D0/bearhero/prog/%A8%E4%A5%A6/JavaWorld/%E5F%BD%BC%A6%CC5.6/SUPPORT/README.TXT


cin_head = '''%gen_inp 
%ename liu
%cname 嘸蝦米
%encoding UTF-8 
%selkey 0123456789 
%keyname begin
a Ａ
b Ｂ
c Ｃ
d Ｄ
e Ｅ
f Ｆ
g Ｇ
h Ｈ
i Ｉ
j Ｊ
k Ｋ
l Ｌ
m Ｍ
n Ｎ
o Ｏ
p Ｐ
q Ｑ
r Ｒ
s Ｓ
t Ｔ
u Ｕ
v Ｖ
w Ｗ
x Ｘ
y Ｙ
z Ｚ
, ，
. ．
' ’
[ 〔
] 〔
%keyname end
%chardef begin
'''

cin_tail = "%chardef end"


def convert_liu_unitab(tab_filename, out_filename):
    idx_to_key = " abcdefghijklmnopqrstuvwxyz,.'[]"
    with open(tab_filename, "rb") as f:
        # read 32x32 uint16 2-d array index table
        key_table = struct.unpack("1025H", f.read(1025 * 2))
        n_words = key_table[-1]  # read uint16 word_count

        # read 2 x word_count bits
        high_bits = f.read(math.ceil(n_words * 2 /8))

        # read word_count bits
        unknown_bits = f.read(math.ceil(n_words / 8))

        # read word_count bits
        is_simple_bits = f.read(math.ceil(n_words / 8))

        # read words
        words = []
        for i in range(n_words):
            word_data = f.read(3)

            # convert bytes to binary strings for ease of handling
            bin_word = "".join(["{:08b}".format(w) for w in word_data])

            key3 = int(bin_word[0:5], 2)
            key4 = int(bin_word[5:10], 2)

            # get low bits
            bin_low_word = bin_word[10:24]

            # get high bits
            i_byte, start_bit = divmod(i * 2, 8)  # 2 bits per word
            bin_high_word = "{:08b}".format(high_bits[i_byte])[start_bit: start_bit + 2]

            # concate the high and low bits and generate the unicode value
            bin_word = bin_high_word + bin_low_word
            word_val = int(bin_word, 2)
            try:
                word = chr(word_val)
            except Exception as e:
                word = ''
                print(e)
            words.append((key3, key4, word))
        words.append((0, 0, None))  # add a mark for end of list

    # According to some users, there might be some variations in the format of liu tabs among versions.
	# We do some simple checks to ensure that we correctly read from the head of the table
    for n_skip in range(0, 32):
        word = words[n_skip][2]
        if word in "對夺对対": # the first word in liu should be one of these four characters
            break
    if n_skip:
        words = words[n_skip:]

    # generate output
    with open(out_filename, "w", encoding="utf-8") as out:
        out.write(cin_head)
        # entries 0 - 31 of key table are useless, skip them
        for i_key in range(32, len(key_table) - 1):
            key1, key2 = divmod(i_key, 32)
            # enumerate words starts with (key1, key2)
            i_start_word = key_table[i_key]
            i_next_word = key_table[i_key + 1]
            # print(i_start_word, i_next_word)
            for i in range(i_start_word, i_next_word):
                (key3, key4, word) = words[i]
                if not word:
                    continue
                # convert keys from indices to ASCII codes (skip 0:space).
                keys = [idx_to_key[k] for k in (key1, key2, key3, key4) if k != 0]
                try:
                    out.write("{} {}\n".format("".join(keys), word))
                except Exception as e:
                    print(e)
        out.write(cin_tail)


def main():
    if len(sys.argv) < 3:
        print("liu_unitab2cin.py <liu-uni.tab file> <out *.cin file>")
        return
    tab_filename = sys.argv[1]
    out_filename = sys.argv[2]
    convert_liu_unitab(tab_filename, out_filename)


if __name__ == "__main__":
    main()

import os

def txt_to_rtf(txt_path, rtf_path):
    with open(txt_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    rtf_lines = [
        r"{\rtf1\ansi\ansicpg1252\deff0\nouicompat\deflang1033{\fonttbl{\f0\fnil\fcharset0 Segoe UI;}{\f1\fnil\fcharset136 Microsoft JhengHei;}}",
        r"{\colortbl ;\red0\green0\blue0;\red30\green30\blue30;}",
        r"\viewkind4\uc1\pard\sl276\slmult1\f0\fs20\lang1033"
    ]

    for line in lines:
        line = line.rstrip('\r\n')
        # Escape RTF special characters
        escaped = ""
        for char in line:
            code = ord(char)
            if char in ('\\', '{', '}'):
                escaped += '\\' + char
            elif code < 128:
                escaped += char
            else:
                escaped += f"\\u{code}?"
        rtf_lines.append(f"{escaped}\\par")

    rtf_lines.append("}")

    with open(rtf_path, 'w', encoding='ascii') as out:
        out.write('\n'.join(rtf_lines) + '\n')

    print(f"Generated {rtf_path} ({os.path.getsize(rtf_path)} bytes)")

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    txt_to_rtf(os.path.join(base_dir, 'LICENSE.txt'), os.path.join(base_dir, 'installer', 'License.rtf'))

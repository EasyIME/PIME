import os
import hashlib
import sys

def generate_wxs(dir_path, component_group_id, directory_ref_id, var_name, output_file, exclude_dirs=None, exclude_files=None):
    exclude_dirs = set(exclude_dirs or [])
    exclude_files = set(exclude_files or [])
    
    rel_dirs = {}
    dir_id_map = { '': directory_ref_id }
    
    for root, dirs, files in os.walk(dir_path):
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
        
        rel_root = os.path.relpath(root, dir_path)
        if rel_root == '.':
            rel_root = ''
            
        if rel_root not in dir_id_map:
            h = hashlib.md5(rel_root.replace('\\', '/').encode('utf-8')).hexdigest()[:16]
            dir_id_map[rel_root] = f"dir_{component_group_id}_{h}"
            
        rel_dirs[rel_root] = [f for f in files if f not in exclude_files and not f.startswith('.')]

    lines = []
    lines.append('<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs">')
    
    sorted_dirs = sorted([d for d in rel_dirs.keys() if d != ''], key=lambda x: (x.count(os.sep), x))
    
    if sorted_dirs:
        lines.append('  <Fragment>')
        lines.append(f'    <DirectoryRef Id="{directory_ref_id}">')
        parent_children = {}
        for d in sorted_dirs:
            parent = os.path.dirname(d)
            parent_children.setdefault(parent, []).append(d)
            
        def write_dir_tree(parent_rel, indent):
            for child_rel in sorted(parent_children.get(parent_rel, [])):
                dirname = os.path.basename(child_rel)
                cid = dir_id_map[child_rel]
                has_kids = child_rel in parent_children
                if has_kids:
                    lines.append(f'{indent}<Directory Id="{cid}" Name="{dirname}">')
                    write_dir_tree(child_rel, indent + '  ')
                    lines.append(f'{indent}</Directory>')
                else:
                    lines.append(f'{indent}<Directory Id="{cid}" Name="{dirname}" />')

        write_dir_tree('', '      ')
        lines.append('    </DirectoryRef>')
        lines.append('  </Fragment>')
        
    lines.append('  <Fragment>')
    lines.append(f'    <ComponentGroup Id="{component_group_id}">')
    
    file_counter = 0
    for rel_d in sorted(rel_dirs.keys()):
        files = rel_dirs[rel_d]
        target_dir_id = dir_id_map[rel_d]
        for f in sorted(files):
            file_counter += 1
            rel_file_path = os.path.join(rel_d, f) if rel_d else f
            h = hashlib.md5(rel_file_path.replace('\\', '/').encode('utf-8')).hexdigest()[:16]
            cmp_id = f"cmp_{component_group_id}_{h}"
            file_id = f"fil_{component_group_id}_{h}"
            var_part = "$(var." + var_name + ")"
            file_source = f"{var_part}\\{rel_file_path}"
            
            lines.append(f'      <Component Id="{cmp_id}" Directory="{target_dir_id}" Guid="*">')
            lines.append(f'        <File Id="{file_id}" KeyPath="yes" Source="{file_source}" />')
            lines.append('      </Component>')
            
    lines.append('    </ComponentGroup>')
    lines.append('  </Fragment>')
    lines.append('</Wix>')
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as out:
        out.write('\n'.join(lines) + '\n')
    print(f"Generated {output_file}: {file_counter} files across {len(rel_dirs)} dirs.")

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    stage_dir = os.path.join(base_dir, 'build', 'stage')
    target_installer_dir = os.path.join(base_dir, 'installer', 'PIME_Core', 'Harvest')
    
    # 1. Python Base (excluding input_methods and cinbase)
    generate_wxs(
        dir_path=os.path.join(stage_dir, 'python'),
        component_group_id='PythonBaseComponents',
        directory_ref_id='INSTALLFOLDER_PYTHON',
        var_name='PythonDir',
        output_file=os.path.join(target_installer_dir, 'Harvest_PythonBase.wxs'),
        exclude_dirs=['input_methods', 'cinbase', '__pycache__']
    )
    
    # 2. Cinbase Base (excluding cin and json)
    generate_wxs(
        dir_path=os.path.join(stage_dir, 'python', 'cinbase'),
        component_group_id='CinbaseBaseComponents',
        directory_ref_id='INSTALLFOLDER_CINBASE',
        var_name='CinbaseDir',
        output_file=os.path.join(target_installer_dir, 'Harvest_CinbaseBase.wxs'),
        exclude_dirs=['cin', '__pycache__', 'json']
    )
    
    # 3. Node Base (excluding input_methods)
    generate_wxs(
        dir_path=os.path.join(stage_dir, 'node'),
        component_group_id='NodeBaseComponents',
        directory_ref_id='INSTALLFOLDER_NODE',
        var_name='NodeDir',
        output_file=os.path.join(target_installer_dir, 'Harvest_NodeBase.wxs'),
        exclude_dirs=['input_methods']
    )
    
    # Python Input Methods
    py_ims = [
        ('chewing', 'IM_Chewing', 'INSTALLFOLDER_CHEWING', 'ChewingDir'),
        ('checj', 'IM_Checj', 'INSTALLFOLDER_CHECJ', 'ChecjDir'),
        ('cheliu', 'IM_Cheliu', 'INSTALLFOLDER_CHELIU', 'CheliuDir'),
        ('chearray', 'IM_Chearray', 'INSTALLFOLDER_CHEARRAY', 'ChearrayDir'),
        ('chedayi', 'IM_Chedayi', 'INSTALLFOLDER_CHEDAYI', 'ChedayiDir'),
        ('chepinyin', 'IM_Chepinyin', 'INSTALLFOLDER_CHEPINYIN', 'ChepinyinDir'),
        ('chesimplex', 'IM_Chesimplex', 'INSTALLFOLDER_CHESIMPLEX', 'ChesimplexDir'),
        ('chephonetic', 'IM_Chephonetic', 'INSTALLFOLDER_CHEPHONETIC', 'ChephoneticDir'),
        ('cheez', 'IM_Cheez', 'INSTALLFOLDER_CHEEZ', 'CheezDir'),
        ('cheeng', 'IM_Cheeng', 'INSTALLFOLDER_CHEENG', 'CheengDir'),
        ('braille_chewing', 'IM_BrailleChewing', 'INSTALLFOLDER_BRAILLE_CHEWING', 'BrailleChewingDir'),
        ('rime', 'IM_Rime', 'INSTALLFOLDER_RIME', 'RimeDir'),
    ]
    
    for folder, cg, dref, vname in py_ims:
        generate_wxs(
            dir_path=os.path.join(stage_dir, 'python', 'input_methods', folder),
            component_group_id=cg,
            directory_ref_id=dref,
            var_name=vname,
            output_file=os.path.join(target_installer_dir, f'Harvest_IM_{folder}.wxs'),
            exclude_dirs=['__pycache__', '.git']
        )
        
    # Node Input Methods
    node_ims = [
        ('McBopomofo', 'IM_McBopomofo', 'INSTALLFOLDER_MCBOPOMOFO', 'McBopomofoDir'),
        ('McFoxim', 'IM_McFoxim', 'INSTALLFOLDER_MCFOXIM', 'McFoximDir'),
        ('McTabim', 'IM_McTabim', 'INSTALLFOLDER_MCTABIM', 'McTabimDir'),
        ('emojime', 'IM_Emojime', 'INSTALLFOLDER_EMOJIME', 'EmojimeDir'),
    ]
    
    for folder, cg, dref, vname in node_ims:
        src = os.path.join(stage_dir, 'node', 'input_methods', folder)
        if os.path.exists(src):
            exclude = ['.git']
            if folder == 'emojime':
                exclude.append('node_modules')
            generate_wxs(
                dir_path=src,
                component_group_id=cg,
                directory_ref_id=dref,
                var_name=vname,
                output_file=os.path.join(target_installer_dir, f'Harvest_IM_{folder}.wxs'),
                exclude_dirs=exclude
            )
        else:
            print(f"Skipping {folder} because {src} does not exist yet.")

    # Generate JSON components
    ime_json_map = {
        'chepinyin': ["thpinyin.json", "pinyin.json", "roman.json", "thpinyin.txt"],
        'chesimplex': ["simplecj.json", "simplex.json", "simplex5.json"],
        'cheez': ["ez.json", "ezsmall.json", "ezmid.json", "ezbig.json", "ezphrase.txt"],
        'chephonetic': ["thphonetic.json", "CnsPhonetic.json", "bpmf.json", "thphonetic.txt"],
        'checj': ["checj.json", "mscj3.json", "mscj3-ext.json", "cj-ext.json", "cnscj.json", "thcj.json", "newcj3.json", "cj5.json", "newcj.json", "scj6.json", "cj-fast.json", "thcj.txt"],
        'chedayi': ["thdayi.json", "dayi4.json", "dayi3.json", "thdayi.txt"],
        'chearray': ["tharray.json", "array30.json", "ar30-big.json", "array40.json", "tharray.txt"],
        'shared': ["gpl.txt"]
    }
    
    json_lines = []
    json_lines.append('<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs">')
    json_lines.append('  <Fragment>')
    json_lines.append('    <DirectoryRef Id="INSTALLFOLDER_CINBASE">')
    json_lines.append('      <Directory Id="dir_cinbase_json" Name="json" />')
    json_lines.append('    </DirectoryRef>')
    json_lines.append('  </Fragment>')
    
    for ime, files in ime_json_map.items():
        json_lines.append('  <Fragment>')
        json_lines.append(f'    <ComponentGroup Id="Cinbase_Json_{ime}" Directory="dir_cinbase_json">')
        for f in files:
            file_path = os.path.join(stage_dir, 'python', 'cinbase', 'json', f)
            if os.path.exists(file_path):
                h = hashlib.md5(f.encode('utf-8')).hexdigest()[:16]
                cmp_id = f"cmp_json_{ime}_{h}"
                file_id = f"fil_json_{ime}_{h}"
                json_lines.append(f'      <Component Id="{cmp_id}" Guid="*">')
                json_lines.append(f'        <File Id="{file_id}" KeyPath="yes" Source="$(var.CinbaseDir)\\json\\{f}" />')
                json_lines.append('      </Component>')
        json_lines.append('    </ComponentGroup>')
        json_lines.append('  </Fragment>')
    
    json_lines.append('</Wix>')
    
    json_output_file = os.path.join(target_installer_dir, 'Harvest_CinbaseJson.wxs')
    with open(json_output_file, 'w', encoding='utf-8') as out:
        out.write('\n'.join(json_lines) + '\n')
    print(f"Generated {json_output_file} for separated JSON dictionaries.")

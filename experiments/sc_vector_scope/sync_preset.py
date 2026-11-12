# Mirrors the Describe words and Input facts from build.py into preset.json (plain python, outside TouchDesigner):
#     python experiments/sc_vector_scope/sync_preset.py          writes preset.json
#     python experiments/sc_vector_scope/sync_preset.py --check  exits 1 if preset.json is out of step with build.py
# The words live in TAKES in build.py; preset.json only copies them for the website.
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AS_PROCESSOR = ('Redraws the picture with an oscilloscope beam: as 64 glowing scan lines pushed up by its brightness, '
                'as a stack of 32 audio waveform traces that are bright where it is bright, or as a slow ridged landscape '
                'built one row at a time.')


def main():
    spec = importlib.util.spec_from_file_location('vs_build', os.path.join(HERE, 'build.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    path = os.path.join(HERE, 'preset.json')
    preset = json.load(open(path, encoding='utf-8'))
    before = json.dumps(preset, sort_keys=True)
    assert len(preset['takes']) == len(mod.TAKES), 'preset.json and TAKES have different numbers of takes'
    for i, (p, t) in enumerate(zip(preset['takes'], mod.TAKES)):
        p['words'] = [w.replace('\n', ' / ') for w in mod.describe_words(t)]
    preset['accepts_input'] = True
    preset['as_processor'] = AS_PROCESSOR
    preset['input_takes'] = [i for i, t in enumerate(mod.TAKES) if dict(mod.TAKE_DEFAULT, **t)['inmode']]
    if '--check' in sys.argv:
        same = json.dumps(preset, sort_keys=True) == before
        print('preset.json', 'in step' if same else 'OUT OF STEP with build.py')
        return 0 if same else 1
    # one take per line, as the file was
    lines = ['{']
    for k, v in preset.items():
        if k == 'takes':
            lines.append(' "takes": [')
            lines += ['  ' + json.dumps(t, ensure_ascii=False) + (',' if i < len(v) - 1 else '') for i, t in enumerate(v)]
            lines.append(' ],')
        else:
            lines.append(' ' + json.dumps(k) + ': ' + json.dumps(v, ensure_ascii=False) + ',')
    lines[-1] = lines[-1].rstrip(',')
    lines.append('}')
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')
    json.load(open(path, encoding='utf-8'))
    print('wrote', path)
    return 0


if __name__ == '__main__':
    sys.exit(main())

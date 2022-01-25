import os
import sys
import json
import logging
import subprocess

from math import floor

class Segmenter(object):
    def __init__(self, alignment_file, audio_file, out_path):
        if os.path.isfile(alignment_file) and os.path.isfile(audio_file):
            self.audio_file = audio_file
            self.alignment = json.load(open(alignment_file))
            self.out_path = out_path
            if not os.path.isdir(out_path):
                os.makedirs(out_path)
        else:
            msg = "audio file or alignment file doesn't exist:"\
                  "\n  %s\n  %s"%(audio_file, alignment_file)
            raise IOError(msg)

    def segment_audio(self):
        base_name = '.'.join(os.path.basename(self.audio_file).split('.')[:-1])
        for cue in self.alignment:
            self.segment_cue(cue, base_name)

    def segment_cue(self, cue, base_name):
        start_end = [float(x)/1000 for x in [cue['start'], cue['end']]]
        duration = '%2.2f'%(start_end[1]-start_end[0])
        file_name = '_'.join([base_name, str(start_end[0]), str(start_end[1])])+'.wav'
        file_path = os.path.join(out_path, file_name)
        args = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'panic',\
                '-i', self.audio_file, '-ss', str(start_end[0]), \
                '-t', duration, '-ac', '1', '-ar', '16000', file_path]
        cue['segment_path'] = file_path
        if os.path.isfile(file_path):
            msg = "%s already exists skipping"%file_path
            print(msg)
            #logging.debug(msg)
        else:
            subprocess.call(args)
            print(' '.join(args))
            if not os.path.isfile(file_path):
                msg = "File not created from ffmpeg operation %s"%file_path
                #logging.error(msg)
                raise IOError(msg)

    def export(self, local_data_path):
        '''Exports the segments for labelstudio format
        '''
        cue_exports = []
        for cue in self.alignment: 
            if cue['segment_path'].startswith(local_data_path):
                file_uri = cue['segment_path'].replace(local_data_path,
                                                       '/data/local-files/?d=')
            else:
                file_uri = cue['segment_path']
            data = {
                'data': {'audio': file_uri},
                'predictions': [{
                    'result': [{
                              'from_name': 'transcription',
                              'to_name': 'audio',
                              'type': 'textarea',
                              'value': {'text': cue['aligned-raw']}
                              }],
                    'score': 1.0
                     }]
                   }
            cue_exports.append(data)

        with open('task.json', 'w') as out:
            json.dump(cue_exports, out, indent=2)

if __name__ == "__main__":
    audio = sys.argv[2]
    alignment = sys.argv[1]
    out_path = sys.argv[3]
    segmenter = Segmenter(alignment, audio, out_path)
    segmenter.segment_audio()
    segmenter.export('/home/baybars/label_data/')

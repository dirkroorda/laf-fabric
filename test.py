from etcbc.lib import Transcription

tr = Transcription()

t = 'DAF DAC'
h = tr.hebrew(t)
tb = tr.trans(h)

print("{}\n{}\n{}".format(t, h, tb))


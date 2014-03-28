from laf.fabric import LafFabric
from laf.names import FabricError
from etcbc.preprocess import prepare

WORKDIR = './example-data/etcbc-gen11'
LAFDIR = WORKDIR

fabric = LafFabric(
    work_dir=WORKDIR,
    laf_dir=LAFDIR,
    save=False,
    verbose='DETAIL',
)

fabric.load('bhs3-tiny.txt.hdr', '--', 'plain', {"features": ("otype",""), "primary": True})
exec(fabric.localnames.format(var='fabric'))
text = ''
for n in NN(test=F.otype.v, value='word'):
    text += '['+']['.join([p[1] for p in P.data(n)])+']'
close()
expected = '''[בְּ][רֵאשִׁ֖ית][בָּרָ֣א][אֱלֹהִ֑ים][אֵ֥ת][הַ][שָּׁמַ֖יִם][וְ][אֵ֥ת][הָ][אָֽרֶץ][אֶתֵּ֤ן][בַּ][מִּדְבָּר֙][][אֶ֣רֶז][שִׁטָּ֔ה][וַ][הֲדַ֖ס][וְ][עֵ֣ץ][שָׁ֑מֶן][אָשִׂ֣ים][בָּ][עֲרָבָ֗ה][][בְּרֹ֛ושׁ][תִּדְהָ֥ר][וּ][תְאַשּׁ֖וּר][יַחְדָּֽו]'''
with open('x.txt', 'w') as h: h.write('{}\n{}'.format(text, expected))
print("EQUAL? {}".format(text == expected))


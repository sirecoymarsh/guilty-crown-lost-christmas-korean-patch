# Authored translation: Codex internal. Source recovery: user game audio; STT is not accepted translation.
from pathlib import Path
R=Path(__file__).resolve().parents[1]
rows=[]
def add(track,block):
 for l in block.strip().splitlines():
  a,b,src,ko=l.split('|');rows.append((track,float(a),float(b),src,ko))
add('lxbgm01','''39.1|44.7|Die Ruinenstadt ist immer noch schön|폐허가 된 도시는 여전히 아름다워
44.7|50.2|Ich warte lange Zeit auf deine Rückkehr|네가 돌아오기를 오래도록 기다려
50.2|55.6|In der Hand ein Vergissmeinnicht|손에는 물망초 한 송이
59.2|64.0|It might be just like a bird in the cage|새장 속 새와 같을지도 몰라
64.3|68.3|How could I reach to your heart|어떻게 해야 네 마음에 닿을까
69.8|73.5|I need you to be stronger than anyone|네가 누구보다 강해지기를 바라
73.5|77.8|I release my soul so you feel my song|내 노래를 느끼도록 영혼을 풀어놓아
77.8|83.3|Regentropfen sind meine Tränen|빗방울은 내 눈물
83.3|88.7|Wind ist mein Atem und mein Erzählung|바람은 내 숨결이자 내 이야기
88.7|93.7|Zweige und Blätter sind meine Hände|가지와 잎사귀는 내 두 손
93.7|98.8|Denn mein Körper ist in Wurzeln gehüllt|내 몸은 뿌리에 감싸여 있으니
99.1|104.0|Wenn die Jahreszeit des Tauens kommt|얼음이 녹는 계절이 오면
104.0|109.1|Werde ich wach und singe ein Lied|나는 깨어나 노래를 불러
109.4|116.9|Das Vergissmeinnicht, das du mir gegeben hast, ist hier|네가 내게 준 물망초는 여기 있어
118.8|123.8|Erinnerst du dich noch? Erinnerst du dich noch|아직 기억하니? 아직 기억하니
123.8|128.8|An dein Wort, das du mir gegeben hast?|네가 내게 했던 그 약속을?
128.8|133.8|Erinnerst du dich noch? Erinnerst du dich noch|아직 기억하니? 아직 기억하니
133.8|137.4|An den Tag, an dem du mir…?|네가 내게… 그날을?
137.4|143.5|Wenn die Jahreszeit des Vergissmeinnichts kommt|물망초의 계절이 오면
143.5|147.0|Singe ich ein Lied|나는 노래를 불러
147.1|152.0|Wenn die Jahreszeit des Vergissmeinnichts kommt|물망초의 계절이 오면
152.0|155.4|Rufe ich dich|너를 불러
158.8|163.5|Erinnerst du dich noch? Erinnerst du dich noch|아직 기억하니? 아직 기억하니
163.5|168.4|An dein Wort, das du mir gegeben hast?|네가 내게 했던 그 약속을?
168.4|173.2|Erinnerst du dich noch? Erinnerst du dich noch|아직 기억하니? 아직 기억하니
173.2|177.0|An den Tag, an dem du mir…?|네가 내게… 그날을?
177.0|182.8|It could be the whole of the problem change your body|너를 바꾸는 모든 문제가 될지도 몰라
184.4|188.4|I need you to be stronger than anyone|네가 누구보다 강해지기를 바라
188.5|193.8|I release my soul so you can feel my breath|내 숨결을 느끼도록 영혼을 풀어놓아
193.8|197.0|Feel my move|내 움직임을 느껴 봐
199.8|204.6|Regentropfen sind meine Tränen|빗방울은 내 눈물
204.6|209.7|Wind ist mein Atem und mein Erzählung|바람은 내 숨결이자 내 이야기
209.7|214.8|Zweige und Blätter sind meine Hände|가지와 잎사귀는 내 두 손
214.8|219.8|Denn mein Körper ist in Wurzeln gehüllt|내 몸은 뿌리에 감싸여 있으니
220.0|225.0|Wenn die Jahreszeit des Tauens kommt|얼음이 녹는 계절이 오면
225.0|230.0|Werde ich wach und singe ein Lied|나는 깨어나 노래를 불러
230.0|239.0|Das Vergissmeinnicht, das du mir gegeben hast, ist hier|네가 내게 준 물망초는 여기 있어''')
add('lxbgm18','''1.8|8.5|Erinnerst du dich noch? Erinnerst du dich noch|아직 기억하니? 아직 기억하니
8.5|15.5|An dein Wort, das du mir gegeben hast?|네가 내게 했던 그 약속을?
16.3|22.0|Erinnerst du dich noch? Erinnerst du dich noch|아직 기억하니? 아직 기억하니
22.0|28.0|An den Tag, an dem du mir…?|네가 내게… 그날을?
30.0|36.7|Die Ruinenstadt ist immer noch schön|폐허가 된 도시는 여전히 아름다워
37.3|44.8|Ich warte lange Zeit auf deine Rückkehr|네가 돌아오기를 오래도록 기다려
46.1|53.1|In der Hand ein Vergissmeinnicht|손에는 물망초 한 송이
57.7|64.2|Regentropfen sind meine Tränen|빗방울은 내 눈물
64.7|71.7|Wind ist mein Atem und mein Erzählung|바람은 내 숨결이자 내 이야기
71.8|78.1|Zweige und Blätter sind meine Hände|가지와 잎사귀는 내 두 손
78.1|86.4|Denn mein Körper ist in Wurzeln gehüllt|내 몸은 뿌리에 감싸여 있으니
86.5|93.4|Wenn die Jahreszeit des Tauens kommt|얼음이 녹는 계절이 오면
94.5|101.7|Werde ich wach und singe ein Lied|나는 깨어나 노래를 불러
101.7|111.9|Das Vergissmeinnicht, das du mir gegeben hast|네가 내게 준 물망초는
111.9|116.7|Ist hier|여기 있어''')
add('lxsong01','''6.4|12.5|隔離されて行く この世界の外で|격리되어 가는 이 세계 밖에서
12.5|18.2|それを嘲笑うのが定めなのか？|그걸 비웃는 것이 운명인가?
18.7|25.3|この胸を不意に刺す 抜けない棘じゃ|불시에 가슴을 찌르는 뽑히지 않는 가시로는
25.3|31.3|痛みさえも もう感じなくなった|이제 아픔조차 느낄 수 없게 됐어
45.0|51.0|孤独な檻の中で 力求めた|고독한 우리 안에서 힘을 갈구했어
51.0|56.7|夜ごと繰り返される閉塞感|밤마다 되풀이되는 막막함
57.8|63.8|傍らの君に 肩寄せていたのは|곁에 있는 네게 어깨를 기댄 건
63.8|69.4|愛し合うためじゃなく 生き抜くため|서로 사랑하려고가 아니라 살아남으려고
70.0|76.7|そっと抱き寄せるなんて 全く出来ずに|살며시 끌어안지도 못한 채
76.7|82.2|力の限り掴み 壊してきた|온 힘을 다해 움켜쥐고 부숴 왔어
82.2|88.0|きっとそれは叶わぬ夢|분명 그건 이룰 수 없는 꿈
89.3|96.0|もっと違った？ そんな答えはなかった|다른 길도 있었을까? 그런 답은 없었어
96.0|102.8|喧噪の夜は去り 沈黙の朝が来る|소란스러운 밤은 가고 침묵의 아침이 와
102.8|107.0|淘汰の風に煽られて|도태의 바람에 휩쓸려
108.3|111.8|過去は押しつぶされ|과거는 짓눌려 부서지고
112.3|114.7|未来も見えず|미래도 보이지 않아
115.4|120.0|現在に残されたものは|지금 남겨진 것은
121.0|124.0|罪と罰|죄와 벌
134.6|141.0|隔離されて行く この世界の中で|격리되어 가는 이 세계 안에서
141.0|147.0|それを受け止めるのが定めなのか？|그걸 받아들이는 것이 운명인가?
160.0|165.0|きっとこれは終わらぬ夢|분명 이건 끝나지 않을 꿈
166.6|171.5|いっそ罪の想いもどこかへ|차라리 죄의 기억도 어딘가로
171.5|173.0|サヨナラ……|잘 있어……
173.0|176.5|崩壊する秩序|무너져 가는 질서
176.5|180.0|亡者どもがしがみつく|망자들이 매달려
180.0|184.0|神様になんてなれずに|신 따위는 되지도 못한 채
185.3|188.7|逃げながら見つけた|도망치며 찾아낸
189.6|192.0|希望の種|희망의 씨앗
192.4|197.3|君が繋いだ世界で……|네가 이어 준 세계에서……
197.6|201.0|生きて行く|살아갈 거야''')
add('lxsong02','''21.7|24.5|未来＝虚ろな夜|미래는 공허한 밤
24.5|29.0|手招きだけが闇に浮かんでる|손짓만이 어둠 속에 떠 있어
29.0|32.7|秒針は冷たく|초침은 차갑게
32.7|37.2|俺のかすれた声をかき消す|내 쉰 목소리를 지워 버려
43.4|45.0|Show me what's wrong|무엇이 잘못됐는지 알려 줘
45.0|48.0|It causes this pain|그것이 이 아픔을 불러와
48.2|52.8|時は破裂する|시간은 터져 버려
53.0|57.5|まるで終わりの始まり|마치 끝의 시작처럼
57.8|60.0|Where am I?|난 어디에 있지?
66.8|69.0|現在＝どこにも不明|현재는 어디에서도 알 수 없어
69.0|73.4|間違いはなくココにあるはずの|분명 여기에 있어야 할
73.4|77.2|触れられるものが真実|손에 닿는 것이 진실이야
77.3|81.0|たとえそれが痛みでも|그게 아픔이라 해도
87.1|89.7|Show me what's wrong|무엇이 잘못됐는지 알려 줘
89.7|92.5|It causes this pain|그것이 이 아픔을 불러와
92.5|96.5|俺は加速する|나는 가속해
96.8|101.6|まるでジェットコースター|마치 롤러코스터처럼
101.8|104.0|To my grave|내 무덤으로
170.0|172.8|Show me what's wrong|무엇이 잘못됐는지 알려 줘
172.8|176.0|It causes this pain|그것이 이 아픔을 불러와
176.0|179.7|時は破裂する|시간은 터져 버려
179.7|185.0|まるで終わりの始まり|마치 끝의 시작처럼
185.3|187.4|Where am I?|난 어디에 있지?
187.4|190.8|It causes this pain|그것이 이 아픔을 불러와
190.8|194.5|俺は加速する|나는 가속해
194.5|199.7|まるでジェットコースター|마치 롤러코스터처럼
199.8|202.0|To my grave|내 무덤으로''')
# The game audio has an instrumental break, not the album's third verse; no invented words there.
(R/'data/lyrics.tsv').write_text('\n'.join('|'.join(map(str,x)) for x in rows)+'\n','utf-8')
print('authored',len(rows),'cues')

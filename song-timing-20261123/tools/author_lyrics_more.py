# All Korean lines authored by Codex internal; repeated phrases reuse the same accepted text.
from author_lyrics import R,rows,add

def repeat(track,original,intervals):
 assert len(original)==len(intervals)
 for x,(a,b) in zip(original,intervals):rows.append((track,a,b,x[3],x[4]))
add('lxbgm04','''10.2|12.4|Locked and loaded, ready to go|장전 완료, 출격 준비 끝
12.4|14.9|If you take us on then under you go|우릴 상대한다면 무너지는 건 너희야
14.9|17.4|The plan is simple, we fight to win|계획은 단순해, 이기기 위해 싸운다
17.4|20.0|Try to take our freedom, let the battle begin|우리 자유를 뺏어 봐, 싸움을 시작하자''')
ready=rows[-4:]
repeat('lxbgm04',ready,[(101,103.3),(103.3,105.8),(105.8,108.3),(108.3,110.8)])
repeat('lxbgm04',ready,[(111,113.4),(113.4,115.9),(115.9,118.4),(118.4,121.2)])
add('lxbgm04','''29.5|33.0|See the world's been broken, we've lost too much already|세상은 부서졌어, 이미 너무 많이 잃었지
33.0|35.9|Time is still ticking, people need to be ready|시간은 흐르고 있어, 모두 준비해야 해
35.9|38.0|Take back what they took from you|그들이 빼앗은 걸 되찾아
38.0|41.2|Search for the truth, break the limits they place on you|진실을 찾아, 그들이 씌운 한계를 깨뜨려
41.2|43.1|Never give up on your friends|친구들을 절대 포기하지 마
43.1|45.4|Show 'em how you do|네가 어떻게 하는지 보여 줘
45.8|47.6|We'll get 'em all free|우리가 모두를 해방할 거야
48.3|50.0|It's time to get freed|이젠 자유로워질 시간이야
59.6|61.5|Since we can't go back|돌아갈 수 없으니
61.5|63.3|We gotta move forward|앞으로 나아가야 해
63.3|65.7|Learn how to do that to see where we're going|어떻게 나아갈지 배워, 우리가 갈 곳을 보게
65.7|68.0|My friends by my side, we'll stand|친구들과 함께 우린 버틸 거야
68.0|70.0|Even when you close in|너희가 몰려와도
70.0|73.1|'Cause you know, you can't keep us down, we won't give in|우릴 누를 순 없어, 우린 굴복하지 않아
73.1|76.0|You can't keep us down, we won't stand for what you're doing|우릴 누를 순 없어, 너희 짓을 두고 보지 않아
76.0|78.4|You can't keep us down, we won't give in|우릴 누를 순 없어, 우린 굴복하지 않아
78.4|80.9|You can't keep us down, we won't give in|우릴 누를 순 없어, 우린 굴복하지 않아
81.8|83.3|We can't go back|우린 돌아갈 수 없어
84.4|86.1|We gotta move forward|앞으로 나아가야 해
87.0|89.6|Learn how to do that to see where we're going|어떻게 나아갈지 배워, 우리가 갈 곳을 보게
89.6|93.3|Because, you see, my friends by my side, we will stand|친구들이 곁에 있으니 우린 버틸 거야
93.3|95.0|Even when you close in|너희가 몰려와도
95.0|98.3|You can't keep us down, we won't give in|우릴 누를 순 없어, 우린 굴복하지 않아
98.3|101.0|You can't keep us down, we won't stand for what you're doing|우릴 누를 순 없어, 너희 짓을 두고 보지 않아
137.2|139.1|Fact or fiction|진실인가, 거짓인가
139.1|141.3|Truth is that the surprise attack made us all victims|분명한 건 그 기습에 우리 모두 희생됐다는 것
141.3|144.3|We lost many but still carry on living strong|많은 이를 잃었어도 우린 꿋꿋이 살아가
144.3|146.9|Though you did your best to take our freedom|너희가 자유를 빼앗으려 온 힘을 쏟았어도
146.9|149.3|We want it back for good|우린 그 자유를 영원히 되찾고 싶어
149.3|151.9|We don't believe that you came to help with a cure|치료해 주러 왔다는 너희 말은 믿지 않아
151.9|155.2|Turn us on each other to insure your own word as bond|우릴 서로 싸우게 해 너희 말만 믿게 하지
155.2|157.5|But our only response is rebellion|하지만 우리의 대답은 저항뿐이야
162.3|164.7|Push your propaganda if you must|선전이 필요하다면 어디 해 봐
164.7|167.2|Steal the government we don't trust|우리가 믿지 않는 정부를 빼앗아 봐
167.2|169.9|Tell the world you came to save us?|세상엔 우릴 구하러 왔다고 말하겠지?
169.9|172.3|Take your time, we're armoring up|천천히 해 봐, 우린 무장하고 있으니
172.3|174.9|We can't get back all we've lost|잃은 모든 걸 되찾을 수는 없지만
174.9|177.3|But we'll recover what we can|되찾을 수 있는 건 되찾겠어
177.3|180.0|The fight we bring is to set things right|우린 모든 걸 바로잡으려 싸우는 거야
180.0|182.4|Doesn't matter what you try, we will stand|무슨 짓을 해도 우린 버틸 거야
183.2|185.0|Because we can't go back|우린 돌아갈 수 없으니까
186.0|187.8|We gotta move forward|앞으로 나아가야 해
188.6|191.4|Learn how to do that to see where we're going|어떻게 나아갈지 배워, 우리가 갈 곳을 보게
192.2|194.9|My friends by my side, we will stand|친구들과 함께 우린 버틸 거야
194.9|196.7|Even when you close in|너희가 몰려와도
197.3|200.1|You can't keep us down, we won't give in|우릴 누를 순 없어, 우린 굴복하지 않아
200.1|203.2|You can't keep us down, we won't stand for what you're doing|우릴 누를 순 없어, 너희 짓을 두고 보지 않아
203.5|205.2|Because we can't go back|우린 돌아갈 수 없으니까
206.1|208.0|We gotta move forward|앞으로 나아가야 해
208.8|211.6|Learn how to do that to see where we're going|어떻게 나아갈지 배워, 우리가 갈 곳을 보게
211.6|215.2|Know that my friends by my side, we will stand|친구들과 함께 우린 버틸 거란 걸 알아 둬
215.2|217.3|Even when you close in|너희가 몰려와도
217.3|220.2|You can't keep us down, we won't give in|우릴 누를 순 없어, 우린 굴복하지 않아
220.2|223.4|You can't keep us down, we won't stand for what you're doing|우릴 누를 순 없어, 너희 짓을 두고 보지 않아
225.9|228.0|This is my guilty crown|이것이 나의 길티 크라운
230.9|233.0|I'll fight for what I believe|내가 믿는 것을 위해 싸우겠어
235.9|238.1|This is my guilty crown|이것이 나의 길티 크라운
240.4|243.5|I'll fight with my friends to set my friends free|친구들과 싸워 친구들을 해방하겠어''')
add('lxbgm05','''15.2|19.6|You have a king of the power, yeah you got it|네게는 왕의 힘이 있어, 그래, 네 것이야
19.6|23.8|Somebody might be a flower, yeah you got it|누군가는 꽃일지도 몰라, 그래, 알겠지
23.8|27.8|It's time to get ready, all you have really|이제 준비할 때야, 네가 가진 모든 걸
27.8|31.2|Time to share, take your chance|함께 나눌 때야, 기회를 잡아
31.2|35.8|It could be the whole of the problem change your body|너를 바꾸는 모든 문제가 될지도 몰라
35.8|39.8|But I need you to be stronger than anyone|하지만 네가 누구보다 강해지기를 바라
39.8|42.5|It's time now to speed up|이젠 속도를 낼 때야
42.5|45.8|All you have to do is make some friends|네가 할 일은 친구를 만드는 것뿐
48.9|52.4|We might be just like a bird in cage|우린 새장 속 새와 같을지도 몰라
53.0|55.6|How could I reach to your heart?|어떻게 해야 네 마음에 닿을까?
55.6|60.4|Coming soon, how can you dance like a clown in the tent?|곧 시작이야, 천막 속 광대처럼 춤출 수 있니?
60.4|67.6|You can change yourself until you'll find the seventh friend|일곱 번째 친구를 찾을 때까지 넌 달라질 수 있어
68.2|72.6|Here we go, come with me, then you open your mind|자, 나와 함께 가자, 그러면 마음이 열릴 거야
72.6|76.8|Here we go, moving on, grooving on, grooving on|자, 나아가, 리듬을 타, 리듬을 타
76.8|79.7|Then we know we'll never see each other again|그러면 알게 되겠지, 우린 다신 만나지 못해
79.7|84.8|Just look so fine, all of your friends with hearts|참 멋져 보여, 진심을 가진 네 친구들 모두
92.5|96.9|You have a king of the right hand, yeah you got it|네 오른손엔 왕의 힘이 있어, 그래, 네 것이야
96.9|101.1|Somebody might be a flower, yeah you got it|누군가는 꽃일지도 몰라, 그래, 알겠지
101.1|103.5|It's time to get ready|이제 준비할 때야
103.5|106.9|All you have to do is make some friends|네가 할 일은 친구를 만드는 것뿐
109.9|113.4|We might be just like a bird in cage|우린 새장 속 새와 같을지도 몰라
113.4|116.7|How could I reach to your heart?|어떻게 해야 네 마음에 닿을까?
117.2|121.4|Coming soon, how can you dance like a clown in the tent?|곧 시작이야, 천막 속 광대처럼 춤출 수 있니?
121.7|128.6|You can change yourself until you'll find the seventh friend|일곱 번째 친구를 찾을 때까지 넌 달라질 수 있어
129.3|133.7|Here we go, come with me, then you open your mind|자, 나와 함께 가자, 그러면 마음이 열릴 거야
133.7|137.9|Here we go, moving on, grooving on, grooving on|자, 나아가, 리듬을 타, 리듬을 타
137.9|140.7|Then we know we'll never see each other again|그러면 알게 되겠지, 우린 다신 만나지 못해
140.7|145.9|Just look so fine, all of your friends with hearts|참 멋져 보여, 진심을 가진 네 친구들 모두
147.4|152.8|Yeah, I've never got satisfied, no|그래, 난 한 번도 만족한 적 없어
155.5|161.0|Yeah, it's gonna be getting worse, no|그래, 점점 더 나빠지겠지
169.8|174.1|Here we go, shaking the ground, then you open yourself|자, 땅을 흔들어, 그러면 너 자신을 열게 돼
174.1|178.5|Here we go, moving on, grooving on, grooving on|자, 나아가, 리듬을 타, 리듬을 타
178.5|181.4|Then we know we'll never see each other again|그러면 알게 되겠지, 우린 다신 만나지 못해
181.4|186.1|Just look so fine, all of your friends with hearts|참 멋져 보여, 진심을 가진 네 친구들 모두
186.1|190.7|Here we go, come with me, then you open your mind|자, 나와 함께 가자, 그러면 마음이 열릴 거야
190.7|194.8|Here we go, moving on, grooving on, grooving on|자, 나아가, 리듬을 타, 리듬을 타
194.8|197.6|Then we know we'll never see each other again|그러면 알게 되겠지, 우린 다신 만나지 못해
197.6|203.0|Just look so fine, all of your friends with hearts|참 멋져 보여, 진심을 가진 네 친구들 모두''')
add('lxbgm12','''18.7|23.8|Oh take a look in the mirror, you look so sad|거울을 봐, 네 모습이 너무 슬퍼 보여
25.5|31.3|It's so cold like that winter market we used to go|우리가 다니던 겨울 시장처럼 너무 추워
33.4|38.8|I don't cry anymore but I feel so hurt|더는 울지 않지만 너무 아파
40.0|44.1|So I don't need you too close to me|그러니 내게 너무 가까이 오지 않아도 돼
44.1|47.9|You don't hear me, so you said|넌 내 말이 들리지 않는다고 했지
47.9|53.5|I don't know why things have changed since yesterday|어제 이후 왜 모든 게 달라졌는지 모르겠어
56.2|60.1|This could be love again|다시 사랑할 수 있을지도 몰라
60.1|63.8|All I need is you|내게 필요한 건 너뿐이야
63.8|71.3|Come back, I'm waiting anytime the heavy rains come|돌아와, 폭우가 쏟아질 때마다 기다리고 있어
71.3|75.1|Still I miss days with you|아직도 너와 함께한 날들이 그리워
75.1|79.3|I can't look into your face|네 얼굴을 똑바로 볼 수 없어
80.1|85.3|Oh feeling blue and looking back again|우울한 마음에 다시 뒤돌아봐
89.2|93.0|Please come back to me|제발 내게 돌아와 줘''')
release=rows[-13:]
repeat('lxbgm12',release,[(118.5,123.2),(125.1,130.6),(133.3,138.3),(139.5,143.5),(143.5,147.2),(147.2,152.7),(153.7,157.7),(157.7,161.6),(161.6,169.4),(169.4,173.0),(173,176.9),(176.9,182.7),(186.6,190.2)])
add('lxbgm12','''213.1|218.0|To stay with you always|언제나 너와 함께 있고 싶어
219.2|221.5|You're the world to me|너는 내게 세상 전부야
221.5|224.0|And dreaming on|그리고 계속 꿈을 꿔
224.6|228.4|So you can take my sword for you|그러니 널 위해 내 검을 가져가도 돼
228.4|233.1|Oh how do you feel so fine|어떻게 그렇게 괜찮을 수 있니
233.1|235.8|You're the world to me|너는 내게 세상 전부야
235.8|238.7|And dream on|그리고 계속 꿈을 꿔
239.2|243.6|You stole my heart so long ago|넌 오래전에 내 마음을 훔쳤지
244.1|246.9|Oh I release my soul|내 영혼을 풀어놓아
246.9|250.2|So you feel my song|네가 내 노래를 느낄 수 있도록''')
add('lxbgm16','''24.0|26.7|You can call my name|내 이름을 불러도 돼
27.3|29.6|Whenever you're feeling down and blue|기운이 없고 우울할 때면 언제든
29.6|32.2|You don't know how to smile|어떻게 웃어야 할지 모르겠지
32.2|36.5|I know how hard it is|얼마나 힘든지 알아
36.5|38.8|I'll make you feel alright|내가 괜찮아지게 해 줄게
38.8|42.0|I remember the day|그날을 기억해
42.0|47.2|I sat with you in this corner|이 모퉁이에서 너와 함께 앉았던 날
50.6|53.3|Alone in front of you|네 앞에 홀로 서서
53.3|57.2|Oh, I don't know the words|무슨 말을 해야 할지 모르겠어
57.2|60.3|Because anywhere is your home|어디든 네 집이니까
60.3|65.2|Your sweet home|네 따스한 집
65.2|69.5|No matter where you are|네가 어디에 있든
72.0|77.0|This thing, it's home, it's incredible|여기가 집이라니, 믿기지 않아
77.0|83.5|All my friends came home again|내 친구들이 모두 집으로 돌아왔어
84.7|91.0|Sometimes you cannot avoid the heavy snow|때로는 거센 눈보라를 피할 수 없어
91.0|94.5|As long as you're alive|살아 있는 한
97.7|100.4|You might lose your luck|운이 따라 주지 않을지도 몰라
100.4|104.1|Whenever you're feeling down and blue|기운이 없고 우울할 때면 언제든
104.1|106.4|You don't know how to smile|어떻게 웃어야 할지 모르겠지
106.4|110.5|I know how hard it is|얼마나 힘든지 알아
110.5|112.6|I'll make you feel alright|내가 괜찮아지게 해 줄게
112.6|115.7|I remember the day|그날을 기억해
115.7|121.0|I sat with you in this corner|이 모퉁이에서 너와 함께 앉았던 날
122.8|126.2|I touched your feeling inside|네 안의 마음에 닿았어
126.2|129.1|You're shifting in my eyes|내 눈에 비친 네 모습이 달라져
129.1|131.2|Drifting away|멀리 흘러가
135.3|137.7|Don't get stuck in sorrow|슬픔에 갇혀 있지 마
137.7|140.5|Get over the things from the past|지난 일들을 딛고 일어서
140.5|144.0|I'll watch your back|내가 네 뒤를 지켜 줄게
147.9|151.8|Alone in front of you|네 앞에 홀로 서서
151.8|155.5|Oh, I don't know the words|무슨 말을 해야 할지 모르겠어
156.1|159.3|Because anywhere is your home|어디든 네 집이니까
159.3|163.5|Your sweet home|네 따스한 집
164.1|168.1|No matter where you are|네가 어디에 있든
170.3|175.5|This thing, it's home, it's incredible|여기가 집이라니, 믿기지 않아
176.1|182.0|All my friends came home again|내 친구들이 모두 집으로 돌아왔어
183.1|189.1|Sometimes you cannot avoid the heavy snow|때로는 거센 눈보라를 피할 수 없어
189.1|193.0|As long as you're alive|살아 있는 한''')
rows.sort(key=lambda x:(x[0],x[1]))
(R/'data/lyrics.tsv').write_text('\n'.join('|'.join(map(str,x)) for x in rows)+'\n','utf-8')
print('authored cumulative',len(rows),'cues')

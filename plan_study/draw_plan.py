from PIL import Image, ImageDraw, ImageFont
_orig=ImageDraw.ImageDraw.rectangle
def _rect(self,xy,*a,**k):
    x0,y0,x1,y1=xy; return _orig(self,[min(x0,x1),min(y0,y1),max(x0,x1),max(y0,y1)],*a,**k)
ImageDraw.ImageDraw.rectangle=_rect
S=15; M=70; W_lot=24.6; L=80.1
im=Image.new('RGB',(1500,int(L*S)+2*M+60),(250,249,246)); d=ImageDraw.Draw(im)
F=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',15); FB=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',19); FS=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',13)
X=lambda x: M+x*S; Y=lambda y: im.size[1]-M-40-y*S
def rect(x0,x1,y0,y1,fill=None,out=(30,30,30),w=2): d.rectangle([X(x0),Y(y1),X(x1),Y(y0)],fill=fill,outline=out,width=w)
def text(x,y,t,f=F,c=(20,20,20),anchor='la'): d.multiline_text((X(x),Y(y)),t,font=f,fill=c,anchor=anchor)
W1,W2=9.92,8.83
rect(0,W_lot,0,71,fill=(236,233,228),out=(150,150,150),w=1)
rect(W2+0.5,W_lot,0,67,fill=(220,215,208)); text(W_lot-1,30,"MILANO'S BAR\n(existing, no scope)",FB,(110,105,98),'ra')
pts=[(0,0),(W1,0),(W1,26),(W2,30),(W2,67.6),(0,67.6)]; d.polygon([(X(a),Y(b)) for a,b in pts],fill=(255,255,255)); d.line([(X(a),Y(b)) for a,b in pts+[pts[0]]],fill=(10,10,10),width=4)
d.rectangle([X(0.3),Y(29),X(W1-0.3),Y(0.4)],fill=(238,240,242)); text(W1/2,13,"hexagon marble",F,(90,90,90),'ma')
d.rectangle([X(0.3),Y(35),X(W2-0.3),Y(29)],fill=(190,160,120)); text(W2/2,32,"wood patch + drain",FS,(60,40,20),'ma')
d.rectangle([X(0.3),Y(51.2),X(W2-0.3),Y(35)],fill=(244,245,246))
d.rectangle([X(0.3),Y(67.4),X(W2-5.4),Y(51.2)],fill=(150,155,160)); d.rectangle([X(W2-5.4),Y(51.2),X(W2-0.3),Y(67.4)],fill=(225,225,225))
text(0.6,60,"gray slate\n3'-6\" passage",FS,(255,255,255))
for yy in (2,8,14,20,25): d.rectangle([X(0),Y(yy+0.9),X(0.8),Y(yy)],fill=(10,10,10))
text(1.1,22,"steel portals\n+ timber header\n(video 0:01-0:16)",FS)
d.rectangle([X(W1-0.7),Y(14),X(W1),Y(10)],fill=(190,190,190),outline=(60,60,60)); text(W1-0.9,12,"AC split\n(west wall)",FS,(60,60,60),'ra')
d.rectangle([X(0),Y(51),X(0.35),Y(33)],fill=(20,20,20)); d.rectangle([X(W2-0.35),Y(42.5),X(W2),Y(33)],fill=(20,20,20))
d.rectangle([X(0.35),Y(41.2),X(0.8),Y(37.7)],fill=(255,255,255),outline=(0,0,0)); text(1.2,39.5,"plaster rosette ~3.5 ft\n+ black marble",FS)
text(W2-0.5,41.8,"black hex tile wall",FS,(255,255,255),'ra')
d.rectangle([X(W2-0.5),Y(34),X(W2),Y(33)],fill=(180,180,185)); text(W2-0.7,32.4,"stainless jamb",FS,(80,80,80),'ra')
bx0=W2-5.25; d.rectangle([X(bx0),Y(51.2),X(W2),Y(42.5)],fill=(235,235,230),outline=(10,10,10),width=3); text(bx0+0.2,50.6,"BATH 8'-8\" x 5'-3\"\nADA toilet, sink,\nmosaic floor",FS)
d.line([X(bx0),Y(45.4),X(bx0),Y(42.7)],fill=(255,99,25),width=6); text(bx0-0.2,44,"door 2'-8\"",FS,(200,70,10),'ra')
d.line([X(W2-5.4),Y(51.2),X(W2-5.4),Y(67.6)],fill=(10,10,10),width=3); text(W2-4.8,59,"rear room\n(radiator),\nwidth unknown",FS)
d.rectangle([X(0.4),Y(68.1),X(3.6),Y(67.0)],fill=(255,99,25)); text(4.0,67.3,"rear doorway (~3 ft)\nvideo 0:24-0:27",FS,(200,70,10))
rect(0,W_lot,67.6,80.1,fill=(228,228,226)); text(W_lot/2,76,"STORE EXTENSION / new storage\n12'-6\" x 24'-6\", gray slate,\nrecessed cans (video 0:29-0:32)",F,(40,40,40),'ma')
d.rectangle([X(-0.2),Y(-0.2)+2,X(W_lot),Y(-3)],fill=(60,60,60)); text(W_lot/2,-0.6,"EAST HOUSTON STREET",F,(255,255,255),'ma')
d.rectangle([X(0.6),Y(0.4),X(5.9),Y(-0.3)],fill=(150,200,220)); d.rectangle([X(5.9),Y(0.4),X(9.4),Y(-0.3)],fill=(255,99,25))
text(2.2,-3.6,"window ~5 ft",FS,(20,20,20),'ma'); text(9.5,-3.6,"glass door ~3.5 ft",FS,(200,70,10),'ma')
def vdim(x,y0,y1,t,c=(30,90,200)): d.line([X(x),Y(y0),X(x),Y(y1)],fill=c,width=2); d.text((X(x)+6,Y((y0+y1)/2)),t,font=FS,fill=c)
vdim(-1.8,0,67.6,""); vdim(-1.8,67.6,80.1,""); vdim(W_lot+2.0,0,26,"26'-0\" wide zone 9'-11\""); vdim(W_lot+2.0,26,67.6,"41'-7\" narrow 7'-11\" clear"); vdim(W_lot+9.0,42.5,51.2,"bath 8'-8\"")
d.text((20,12),"51 East Houston, ground floor: my reading of the Meridian plan + the two walk-through videos",font=FB,fill=(10,10,10)); d.text((20,40),"Street at the bottom. Walking in from the street: LEFT = east wall (steel portals), RIGHT = west wall (white wall, bath, Milano's beyond).",font=F,fill=(60,60,60))
notes=["WHAT I HAD WRONG","1  Strip is ~9 ft wide the WHOLE length. I drew a 17 ft rear room. It does not exist.","2  Portals/steel are on the EAST wall (left walking in). I put them west.","3  Bath and AC are on the WEST wall (right walking in).","4  Past the bath the passage is only ~3'-6\" wide (plan: 8'-10\" minus the 5'-3\" bath).","5  Behind the strip is a 12'-6\" x 24'-6\" storage extension, a separate room.","6  Slanted plan lines (22'-4\", 15'-9\", 14'-10\") are travel-distance dimensions, not walls.","","STILL GUESSED (need you or a tape)","- window vs door width on the glass; which end the door is on","- ceiling: ~11 ft front; lower (~9 ft) at bath and rear","- exact rear partition and the radiator room's width","- where the sink sits in the bath"]
for i,t in enumerate(notes): d.text((560,120+i*30),t,font=FB if i in (0,8) else F,fill=(190,50,20) if i in (0,8) else (20,20,20))
im.save('corrected_plan_v1.png'); print(im.size)

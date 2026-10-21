# Membangun "cangkang" gedung Kantor AI di Blender (headless, bpy) lalu ekspor .glb.
# Papan nama: KANTOR_TITLE="KANTOR XYZ" KANTOR_SUB="Slogan" python build_shell.py -- kantor-shell.glb
# Koordinat ditulis dalam sistem three.js (X kanan, Y atas, Z ke arah kamera);
# helper mengonversi ke Blender (Z atas): blender = (X, -Z, Y).
import bpy, math, random, sys
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
Y0 = 0.4
MATS = {}
def mat(name, color, alpha=1.0, emit=None, rough=0.85):
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    r,g,bb = [int(color[i:i+2],16)/255 for i in (1,3,5)]
    lin = lambda c: c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4
    b.inputs["Base Color"].default_value = (lin(r),lin(g),lin(bb),1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = 0.0
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
        try: m.surface_render_method = 'BLENDED'
        except Exception: pass
    if emit:
        er,eg,eb = [lin(int(emit[i:i+2],16)/255) for i in (1,3,5)]
        b.inputs["Emission Color"].default_value = (er,eg,eb,1)
        b.inputs["Emission Strength"].default_value = 1.5
    MATS[name] = m; return m
COL = bpy.data.collections.new("KantorShell"); scene.collection.children.link(COL)
def link(o):
    for c in o.users_collection: c.objects.unlink(o)
    COL.objects.link(o); return o
def box(x0,x1,y0,y1,z0,z1,m,bevel=0.0,name="box"):
    bpy.ops.mesh.primitive_cube_add(size=1, location=((x0+x1)/2, -(z0+z1)/2, (y0+y1)/2))
    o = bpy.context.active_object; o.name = name
    o.scale = (x1-x0, z1-z0, y1-y0); bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(m)
    if bevel>0:
        md = o.modifiers.new("bev","BEVEL"); md.width = bevel; md.segments = 2; md.limit_method='ANGLE'
    return link(o)
def boxc(w,h,d,x,y,z,m,bevel=0.0,name="box"):  # y = alas
    return box(x-w/2,x+w/2,y,y+h,z-d/2,z+d/2,m,bevel,name)
def ico(r,x,y,z,m,sub=1,sx=1,sy=1,sz=1,name="ico"):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=(x,-z,y))
    o = bpy.context.active_object; o.name=name; o.scale=(sx,sz,sy); bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(m); return link(o)
def cyl(r,h,x,y,z,m,verts=12,r2=None,name="cyl"):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=(x,-z,y+h/2))
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2, depth=h, location=(x,-z,y+h/2))
    o = bpy.context.active_object; o.name=name; o.data.materials.append(m); return link(o)

M = dict(
  wall=mat("Dinding","#F4F6F5"), trim=mat("ListTepi","#FFFFFF",rough=.6), skirt=mat("Plin","#56656B"),
  pier=mat("Kolom","#ECEFF0"), frame=mat("KusenJendela","#3A4650",rough=.5),
  glass=mat("Kaca","#BFEFEA",alpha=.28,rough=.05), kerja=mat("DindingKerja","#DCE6EA"), mainw=mat("DindingMain","#2B3742"),
  lib=mat("DindingPustaka","#E9DDC9"), server=mat("DindingServer","#33424E"), pantry=mat("DindingPantry","#F3E6DA"),
  plotw=mat("DindingKavling","#C9CDCF"), plaza=mat("Pelataran","#D3CCC1",rough=.95), curb=mat("Kanstin","#A9A196"),
  slab=mat("PlatLantai","#EDE9E1"), step=mat("Tangga","#E6E1D8"), trunk=mat("Batang","#7A5132"),
  leaf1=mat("Daun1","#3F8A4E"), leaf2=mat("Daun2","#4C9A58"), leaf3=mat("Daun3","#5FAE64"), pot=mat("Pot","#B5653A"),
  soil=mat("Tanah","#6B4A2C"), pole=mat("Tiang","#3A3A3A",rough=.4), lampw=mat("LampuJalan","#FFE3A3",emit="#FFC25A"),
  bench=mat("Bangku","#A4734A"), benchleg=mat("KakiBangku","#2E3438"), signb=mat("PapanNama","#16302C",rough=.5),
  signt=mat("HurufNama","#F3E2B3",emit="#D9AE4E",rough=.4), stone=mat("BatuSetapak","#C9C1B3"),
  f1=mat("Bunga1","#E8775F"), f2=mat("Bunga2","#F3C55B"), f3=mat("Bunga3","#C9A3D9"), canopy=mat("Kanopi","#1E8C7A",rough=.5),
)

# ---------- pelataran & lantai ----------
box(-26,26,0,.38,-20,20,M["plaza"],bevel=.08,name="Pelataran")
for (x0,x1,z0,z1) in [(-26,26,19.6,20),(-26,-10.4,-20,-19.6),(10.4,26,-20,-19.6),(-26,-25.6,-20,20),(25.6,26,-20,20)]:
    box(x0,x1,.38,.46,z0,z1,M["curb"],name="Kanstin")
box(-21.3,21.3,.34,Y0,-15.3,15.3,M["slab"],bevel=.04,name="PlatGedung")
boxc(10,.18,2,0,.38,20.6,M["step"],bevel=.03,name="Tangga1"); boxc(8,.18,1.4,0,.2,21.6,M["step"],bevel=.03,name="Tangga2")
for i in range(16):  # batu setapak
    z = 23+i*2.4; x = math.sin(i*.55)*1.6
    boxc(1.6,.06,1.1,x,0,z,M["stone"],bevel=.15,name="Setapak")

# ---------- dinding ----------
def split(s,e,doors):
    segs=[(s,e)]
    for a,b in doors:
        n=[]
        for p,q in segs:
            if a>=q or b<=p: n.append((p,q))
            else:
                if a-p>.05: n.append((p,a))
                if q-b>.05: n.append((b,q))
        segs=n
    return segs
T=.22
def wall_x(x,z0,z1,doors,h,m,windows=()):
    for s,e in split(z0,z1,doors):
        cuts=[(c-w/2,c+w/2) for c,w in windows if s<c<e]
        prev=s
        for a,b in sorted(cuts):
            if a>prev: box(x-T/2,x+T/2,Y0,Y0+h,prev,a,m,name="Dinding")
            box(x-T/2,x+T/2,Y0,Y0+.9,a,b,m,name="Dinding"); box(x-T/2,x+T/2,Y0+2.05,Y0+h,a,b,m,name="Dinding")
            box(x-.03,x+.03,Y0+.9,Y0+2.05,a,b,M["glass"],name="KacaJendela")
            for zz in (a,b,(a+b)/2): box(x-.07,x+.07,Y0+.9,Y0+2.05,zz-.04,zz+.04,M["frame"],name="Kusen")
            box(x-.12,x+.12,Y0+.86,Y0+.94,a,b,M["frame"],name="Ambang"); box(x-.07,x+.07,Y0+2.01,Y0+2.09,a,b,M["frame"],name="Kusen")
            prev=b
        if e>prev: box(x-T/2,x+T/2,Y0,Y0+h,prev,e,m,name="Dinding")
        box(x-T/2-.04,x+T/2+.04,Y0+h,Y0+h+.06,s,e,M["trim"],name="ListAtas")
        box(x-T/2-.02,x+T/2+.02,Y0,Y0+.12,s,e,M["skirt"],name="Plin")
    for a,b in doors:
        if z0<a<z1: box(x-T/2,x+T/2,Y0+1.95,Y0+h,a,b,m,name="Lintel")
def wall_z(z,x0,x1,doors,h,m,windows=(),lintel=True):
    for s,e in split(x0,x1,doors):
        cuts=[(c-w/2,c+w/2) for c,w in windows if s<c<e]
        prev=s
        for a,b in sorted(cuts):
            if a>prev: box(prev,a,Y0,Y0+h,z-T/2,z+T/2,m,name="Dinding")
            box(a,b,Y0,Y0+.9,z-T/2,z+T/2,m,name="Dinding"); box(a,b,Y0+2.05,Y0+h,z-T/2,z+T/2,m,name="Dinding")
            box(a,b,Y0+.9,Y0+2.05,z-.03,z+.03,M["glass"],name="KacaJendela")
            for xx in (a,b,(a+b)/2): box(xx-.04,xx+.04,Y0+.9,Y0+2.05,z-.07,z+.07,M["frame"],name="Kusen")
            box(a,b,Y0+.86,Y0+.94,z-.12,z+.12,M["frame"],name="Ambang"); box(a,b,Y0+2.01,Y0+2.09,z-.07,z+.07,M["frame"],name="Kusen")
            prev=b
        if e>prev: box(prev,e,Y0,Y0+h,z-T/2,z+T/2,m,name="Dinding")
        box(s,e,Y0+h,Y0+h+.06,z-T/2-.04,z+T/2+.04,M["trim"],name="ListAtas")
        box(s,e,Y0,Y0+.12,z-T/2-.02,z+T/2+.02,M["skirt"],name="Plin")
    if lintel:
        for a,b in doors:
            if x0<a<x1 and h>1.95: box(a,b,Y0+1.95,Y0+h,z-T/2,z+T/2,m,name="Lintel")
WH,IW=2.6,2.1
# luar: belakang per ruang dengan warna sendiri
wall_z(-15,-21.1,-7,[],WH,M["kerja"],windows=[(-19.2,1.8),(-9.2,2.2)])
wall_z(-15,-7,7,[],WH,M["mainw"],windows=[(-5,1.5),(5,1.5)])
wall_z(-15,7,21.1,[],WH,M["lib"])
wall_x(-21,-15,15,[],WH,M["wall"],windows=[(-10,3),(12,2.4)])
wall_x(21,-15,15,[],WH,M["wall"],windows=[(-3.4,1.6),(3.4,1.6)])
# depan: dinding kaca berkusen
for s,e in split(-21.1,21.1,[(-1.6,1.6)]):
    box(s,e,Y0,Y0+1.1,15-.03,15+.03,M["glass"],name="KacaDepan")
    box(s,e,Y0+1.08,Y0+1.16,15-.08,15+.08,M["frame"],name="RelKaca"); box(s,e,Y0,Y0+.1,15-.08,15+.08,M["frame"],name="RelKaca")
    n=max(1,round((e-s)/3.5))
    for i in range(n+1): xx=s+(e-s)*i/n; box(xx-.05,xx+.05,Y0,Y0+1.1,15-.06,15+.06,M["frame"],name="TiangKaca")
# kanopi pintu depan
boxc(4.6,.1,2.4,0,Y0+2.5,16.2,M["canopy"],bevel=.03,name="Kanopi")
for xx in (-2.1,2.1): boxc(.12,2.5,.12,xx,Y0,17.25,M["frame"],name="TiangKanopi")
# kolom struktur
for x in (-21,-7,7,21):
    for z in (-15,-5,5,15):
        h=WH+.2 if (abs(x)==21 or z==-15) else (IW+.2 if z!=15 else 1.4)
        if z==15: h=1.4
        boxc(.42,h,.42,x,Y0,z,M["pier"],bevel=.04,name="Kolom")
# dalam
wall_x(-7,-15,-5,[(-11,-9)],IW,M["wall"]); wall_x(7,-15,-5,[(-11,-9)],IW,M["wall"])
wall_x(-7,-5,5,[(-1.2,1.2)],IW,M["server"]); wall_x(7,-5,5,[(-1.2,1.2)],IW,M["wall"])
wall_x(-7,5,15,[],IW,M["pantry"]); wall_x(7,5,15,[],1.2,M["plotw"])
wall_z(-5,-21,-7,[(-14.2,-11.8)],IW,M["wall"]); wall_z(-5,-7,7,[(-1.2,1.2)],IW,M["wall"]); wall_z(-5,7,21,[(12.8,15.2)],IW,M["wall"])
wall_z(5,-21,-7,[(-10.2,-7.8)],IW,M["pantry"]); wall_z(5,-7,7,[(-1.2,1.2)],1.2,M["plotw"]); wall_z(5,7,21,[(10.4,12.6)],1.2,M["plotw"])

# ---------- lansekap ----------
def tree(x,z,s=1.0):
    cyl(.22*s,1.3*s,x,0,z,M["trunk"],verts=8,r2=.16*s,name="Pohon")
    for i,(r,y,m) in enumerate([(1.5,1.9,"leaf1"),(1.2,2.9,"leaf2"),(.85,3.7,"leaf3")]):
        cyl(r*s,1.6*s,x,(y-.4)*s,z,M[m],verts=7,r2=.05,name="Pohon")
def roundtree(x,z,s=1.0):
    cyl(.2*s,1.6*s,x,0,z,M["trunk"],verts=8,name="PohonBulat")
    ico(1.2*s,x,2.3*s,z,M["leaf2"],sub=1,name="PohonBulat"); ico(.8*s,x+.6*s,2.0*s,z+.3*s,M["leaf1"],sub=1,name="PohonBulat"); ico(.7*s,x-.6*s,2.6*s,z-.2*s,M["leaf3"],sub=1,name="PohonBulat")
for t in [(-34,-22,1.2),(-38,8,1),(34,-24,1.3),(38,12,1),(-46,-6,1.4),(46,-2,1.2),(-12,-34,1),(16,-36,1.2),(-52,20,1.1),(52,24,1),(-28,-38,1.1),(30,-40,1)]: tree(*t)
for t in [(-30,30,1),(30,32,1.1),(-40,-28,.9),(42,-16,1),(-8,32,.8),(10,34,.9),(-56,-4,1.1),(58,6,1)]: roundtree(*t)
for i in range(26):  # semak
    a=random.random()*math.tau; r=30+random.random()*22; x=math.cos(a)*r; z=math.sin(a)*r*.8
    if -12<x<12 and z<-17: continue
    ico(.6+random.random()*.5,x,.35,z,M[random.choice(["leaf1","leaf2","leaf3"])],sub=1,sy=.7,name="Semak")
# bedeng bunga depan
for x0 in (-20,-8,6):
    boxc(10 if x0!=-8 else 4,.32,1.1,x0+(5 if x0!=-8 else 2),.38,17.9,M["pot"],bevel=.03,name="Bedeng")
    w=10 if x0!=-8 else 4
    boxc(w-.2,.05,.9,x0+w/2,.7,17.9,M["soil"],name="TanahBedeng")
    for i in range(int(w*2.2)):
        xx=x0+.3+random.random()*(w-.6); zz=17.6+random.random()*.6
        ico(.11,xx,.86,zz,M[random.choice(["f1","f2","f3"])],sub=1,name="Bunga")
        ico(.16,xx+.1,.8,zz+.1,M["leaf2"],sub=1,sy=.6,name="DaunBunga")
# pot tanaman besar di depan
for x in (-18,-6,6,18):
    cyl(.38,.55,x,.38,16.6,M["pot"],verts=10,r2=.3,name="PotDepan")
    ico(.6,x,1.35,16.6,M["leaf1"],sub=1,name="PotDepan"); ico(.4,x+.3,1.6,16.5,M["leaf3"],sub=1,name="PotDepan")
# bangku taman
for x in (-11,11):
    boxc(2.4,.08,.6,x,.85,18.9,M["bench"],bevel=.02,name="Bangku"); boxc(2.4,.5,.08,x,.9,19.2,M["bench"],bevel=.02,name="Bangku")
    for dx in (-1,1): boxc(.1,.47,.5,x+dx,.38,18.9,M["benchleg"],name="KakiBangku")
# tiang lampu untai (sama posisi dengan halaman)
for x,z in [(-25,-19),(25,-19),(25,19),(-25,19)]:
    cyl(.09,4.4,x,.4,z,M["pole"],verts=8,r2=.07,name="TiangLampu")
    boxc(.3,.08,.3,x,4.75,z,M["pole"],name="TiangLampu"); ico(.16,x,4.95,z,M["lampw"],sub=1,name="LampuTiang")
# papan nama gedung
boxc(6.4,1.5,.4,-15.5,.38,19.0,M["signb"],bevel=.05,name="PapanNama")
boxc(.3,.2,.3,-18.3,.38,19,M["pole"],name="PapanNama"); boxc(.3,.2,.3,-12.7,.38,19,M["pole"],name="PapanNama")
def text3d(t,size,x,y,z,m,ext=.05):
    bpy.ops.object.text_add(location=(x,-z,y)); o=bpy.context.active_object
    o.data.body=t; o.data.size=size; o.data.extrude=ext; o.data.align_x='CENTER'; o.data.align_y='CENTER'
    o.rotation_euler=(math.pi/2,0,0); o.data.materials.append(m)
    bpy.ops.object.convert(target='MESH'); o=bpy.context.active_object; o.name="Teks"; return link(o)
import os
text3d(os.environ.get("KANTOR_TITLE","KANTOR AI"),.62,-15.5,1.42,19.25,M["signt"])
text3d(os.environ.get("KANTOR_SUB","AI Agent Office"),.26,-15.5,.88,19.25,M["signt"],ext=.03)

# ---------- MENARA (4 lantai + rooftop) ----------
TM=dict(slab=mat("LantaiMenara","#E3E8EC",rough=.5),frame=mat("RangkaMenara","#2A323C",rough=.35),
  back=mat("DindingMenara","#18212B",rough=.6),led=mat("LEDMenara","#5FE1FF",emit="#33D6FF",rough=.3),
  gl=mat("KacaMenara","#9FE3F0",alpha=.13,rough=.02),gls=mat("KacaSamping","#9FE3F0",alpha=.2,rough=.02),
  dark=mat("PanelGelap","#232A31",rough=.4),solar=mat("PanelSurya","#1E3A6E",rough=.2),pad=mat("LandasanDrone","#2B3138",rough=.5),
  white=mat("PutihFuturis","#F2F5F7",rough=.3),seat=mat("KursiFuturis","#3B4A5A",rough=.4),green=mat("TamanLangit","#4C9A58"),
  warm=mat("BarHangat","#B07A4F",rough=.5),floorD=mat("LantaiDataCenter","#101820",rough=.4))
TX0,TX1,TZ0,TZ1,FH=-8.0,8.0,-32.0,-20.0,3.4
top=lambda k: Y0+(k-1)*FH
box(-10.4,10.4,0,.38,-34,-19.6,M["plaza"],bevel=.06,name="PelataranMenara")
box(TX0-.3,TX1+.3,.34,Y0,TZ0-.3,TZ1+.3,TM["slab"],name="LantaiMenara")
for k in (2,3,4,5):
    t=top(k); box(TX0-.2,TX1+.2,t-.3,t,TZ0-.2,TZ1+.2,TM["slab"],bevel=.04,name="PlatMenara")
    box(TX0-.2,TX1+.2,t-.22,t-.12,TZ1+.2,TZ1+.26,TM["led"],name="LEDTepi")
    for xx in (TX0-.2,TX1+.2): box(xx-.03,xx+.03,t-.22,t-.12,TZ0-.2,TZ1+.2,TM["led"],name="LEDTepi")
H=top(5)
for x,z in [(TX0,TZ0),(TX1,TZ0),(TX0,TZ1),(TX1,TZ1)]: box(x-.18,x+.18,Y0,H+1.1,z-.18,z+.18,TM["frame"],name="KolomMenara")
box(TX0,TX1,Y0,H,TZ0-.12,TZ0+.08,TM["back"],name="DindingMenara")
for x in (-6,-2,2,6): box(x-.04,x+.04,Y0+.2,H-.2,TZ0+.08,TZ0+.12,TM["led"],name="LEDVertikal")
for k in (1,2,3,4):
    b,t=top(k),top(k+1)-.3
    box(TX0,TX1,b,t,TZ1-.02,TZ1+.02,TM["gl"],name="KacaDepanMenara")
    for x in (-4,0,4): box(x-.05,x+.05,b,t,TZ1-.05,TZ1+.05,TM["frame"],name="MullionMenara")
    for xx in (TX0,TX1):
        box(xx-.02,xx+.02,b,t,TZ0,TZ1,TM["gls"],name="KacaSampingMenara")
        for z in (-29,-26,-23): box(xx-.05,xx+.05,b,t,z-.05,z+.05,TM["frame"],name="MullionMenara")
# parapet kaca rooftop
for (x0,x1,z0,z1) in [(TX0,TX1,TZ1-.03,TZ1+.03),(TX0,TX1,TZ0-.03,TZ0+.03),(TX0-.03,TX0+.03,TZ0,TZ1),(TX1-.03,TX1+.03,TZ0,TZ1)]:
    box(x0,x1,H,H+1.0,z0,z1,TM["gls"],name="ParapetKaca")
box(TX0,TX1,H+.98,H+1.06,TZ1-.06,TZ1+.06,TM["led"],name="LEDParapet")
# tabung lift kaca
cyl(.95,H+.6-Y0,6.2,Y0,-29.4,TM["gls"],verts=24,name="TabungLift")
for k in (1,2,3,4,5):
    bpy.ops.mesh.primitive_torus_add(major_radius=.97,minor_radius=.04,location=(6.2,29.4,top(k)+.02)); o=bpy.context.active_object; o.data.materials.append(TM["led"]); link(o)
# L1 lobi: meja resepsionis
boxc(3.4,1.0,.9,0,Y0,-24.6,TM["white"],bevel=.08,name="Resepsionis"); boxc(3.4,.06,.92,0,Y0+.62,-24.6,TM["led"],name="LEDResepsionis")
for x in (-3.5,3.5): boxc(1.2,.45,1.2,x,Y0,-28.5,TM["seat"],bevel=.15,name="KursiLobi")
# L2 data center: lantai gelap + rak kabel
b2=top(2); box(TX0+.3,TX1-.3,b2,b2+.04,TZ0+.3,TZ1-.3,TM["floorD"],name="LantaiDC")
box(TX0+.5,TX1-.5,b2+2.7,b2+2.78,-28.6,-28.4,TM["frame"],name="RakKabel")
# L3 ruang strategi: meja bundar
b3=top(3); cyl(1.5,.06,0,b3+.72,-26,TM["white"],verts=40,name="MejaHologram"); cyl(.35,.72,0,b3,-26,TM["dark"],verts=16,name="KakiMeja")
bpy.ops.mesh.primitive_torus_add(major_radius=1.5,minor_radius=.04,location=(0,26,b3+.78)); o=bpy.context.active_object; o.data.materials.append(TM["led"]); link(o)
for ang in (0,1.57,3.14,4.71): cyl(.3,.45,math.cos(ang)*2.4,b3,-26+math.sin(ang)*2.4,TM["seat"],verts=14,name="KursiStrategi")
# L4 sky lounge
b4=top(4)
for x in (-4.6,.6): boxc(1.6,.45,.9,x,b4,-27,TM["seat"],bevel=.12,name="SofaLangit"); boxc(1.6,.5,.25,x+(-.0),b4+.4,-27.4 if x<0 else -27.4,TM["seat"],bevel=.08,name="SofaLangit")
boxc(1.2,.4,.7,-2,b4,-27,TM["white"],bevel=.08,name="MejaLounge")
boxc(3.4,1.05,.7,4,b4,-24.6,TM["warm"],bevel=.06,name="BarLangit"); boxc(3.4,.05,.72,4,b4+1.0,-24.6,TM["led"],name="LEDBar")
for x in (-6.5,-4,-1.5,1.5): boxc(1.6,.5,.6,x,b4,-31.3,TM["dark"],name="PotTaman"); ico(.55,x,b4+.8,-31.3,TM["green"],sub=1,sx=1.3,name="TamanLangit")
# rooftop: landasan drone, panel surya, antena
cyl(2.1,.12,-2,H,-26,TM["pad"],verts=32,name="LandasanDrone")
bpy.ops.mesh.primitive_torus_add(major_radius=1.7,minor_radius=.06,location=(-2,26,H+.14)); o=bpy.context.active_object; o.data.materials.append(TM["led"]); link(o)
for (x0,x1,z0,z1) in [(-2.5,-2.3,-27,-25),(-1.7,-1.5,-27,-25),(-2.3,-1.7,-26.1,-25.9)]: box(x0,x1,H+.12,H+.16,z0,z1,TM["led"],name="HurufH")
for i in range(3):
    for j in range(2):
        o=boxc(1.6,.06,1.0,3.4+j*2.0,H+.6,-30.5+i*1.6,TM["solar"],name="PanelSurya"); o.rotation_euler=(math.radians(-25),0,0)
        boxc(.08,.6,.08,3.4+j*2.0,H,-30.5+i*1.6,TM["frame"],name="TiangPanel")
cyl(.07,3.2,-6.8,H,-31,TM["frame"],verts=8,r2=.03,name="Antena")

# ---------- gabung per material (hemat draw call) ----------
groups={}
for o in list(COL.objects):
    if o.type!='MESH' or not o.data.materials: continue
    groups.setdefault(o.data.materials[0].name,[]).append(o)
for name,objs in groups.items():
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
        for md in list(o.modifiers): bpy.context.view_layer.objects.active=o; bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.context.view_layer.objects.active=objs[0]
    if len(objs)>1: bpy.ops.object.join()
    bpy.context.active_object.name=name
# ---------- ekspor ----------
bpy.ops.object.select_all(action='SELECT')
for o in bpy.context.selected_objects:
    if o.type=='MESH':
        for p in o.data.polygons: p.use_smooth=False
out = sys.argv[sys.argv.index("--")+1] if "--" in sys.argv else "/home/claude/blender/kantor-shell.glb"
bpy.ops.wm.save_as_mainfile(filepath=out.replace(".glb",".blend"))
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_apply=True, export_yup=True, use_selection=False, export_materials='EXPORT')
print("OK", out, len(bpy.data.objects), "objek")

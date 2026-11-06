import bpy, math, os, json
from mathutils import Vector
from math import sin,cos,pi
OUT='/workspace/output'
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
 if c.name!='Collection': bpy.data.collections.remove(c)
base=bpy.data.collections.get('Collection'); base.name='TIGER_I_EARLY'
collections={}
def group(name):
 if name not in collections:
  c=bpy.data.collections.new(name); bpy.context.scene.collection.children.link(c); collections[name]=c
 return collections[name]
current='01_Hull'
def put(o,name,mat):
 o.name=name
 for c in list(o.users_collection): c.objects.unlink(o)
 group(current).objects.link(o)
 if mat:o.data.materials.append(mat)
 return o
def material(name,color,metal=0,rough=.5):
 m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1); p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=rough
 return m
paint=material('Dunkelgelb satin armour',(.33,.29,.17),.45,.48)
edge=material('Machined steel',(.23,.25,.25),.8,.32)
track=material('Cast track steel',(.105,.115,.115),.75,.65)
rubber=material('Rubber tyres',(.025,.03,.032),.05,.75)
black=material('Recesses',(.009,.013,.014),.2,.7)
wood=material('Tool handles',(.23,.12,.045),0,.7)
# Fine cast/rolled surface: subtle bump, no displacement of measured geometry.
for m in [paint,track]:
 n=m.node_tree.nodes; l=m.node_tree.links; noise=n.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=170; noise.inputs['Detail'].default_value=2
 bump=n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.12; bump.inputs['Distance'].default_value=.002
 l.new(noise.outputs['Fac'],bump.inputs['Height']); l.new(bump.outputs['Normal'],n.get('Principled BSDF').inputs['Normal'])
def bevel(o,w=.006):
 if w:
  mod=o.modifiers.new('Small manufactured edge bevel','BEVEL'); mod.width=w; mod.segments=2
  mod=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
 return o
def box(name,loc,dim,mat=paint,b=.005):
 x,y,z=[a/2 for a in dim]
 v=[(-x,-y,-z),(-x,-y,z),(-x,y,-z),(-x,y,z),(x,-y,-z),(x,-y,z),(x,y,-z),(x,y,z)]
 f=[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]
 o=mesh(name,v,[tuple(reversed(face)) for face in f],mat,b);o.location=loc;return o
def cyl(name,loc,r,depth,mat=paint,axis='Z',verts=64,r2=None,b=.003):
 rr=r if r2 is None else r2
 v=[(rad*cos(i*2*pi/verts),rad*sin(i*2*pi/verts),z) for z,rad in [(-depth/2,r),(depth/2,rr)] for i in range(verts)]
 f=[tuple(range(verts-1,-1,-1)),tuple(range(verts,2*verts))]+[(i,(i+1)%verts,(i+1)%verts+verts,i+verts) for i in range(verts)]
 o=mesh(name,v,f,mat,b);o.location=loc
 if axis=='Y':o.rotation_euler[0]=pi/2
 if axis=='X':o.rotation_euler[1]=pi/2
 for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
 return o
def mesh(name,v,f,mat=paint,b=.005):
 me=bpy.data.meshes.new(name); me.from_pydata(v,[],f); me.update(); o=bpy.data.objects.new(name,me); group(current).objects.link(o); 
 if mat:o.data.materials.append(mat)
 return bevel(o,b)
def tube(name,loc,outer,inner,length,mat=paint,axis='X',n=64):
 v=[]
 for z,r in [(-length/2,outer),(length/2,outer),(-length/2,inner),(length/2,inner)]:
  v.extend([(r*cos(i*2*pi/n),r*sin(i*2*pi/n),z) for i in range(n)])
 f=[]
 for i in range(n):
  j=(i+1)%n; f.extend([(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),(i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)])
 o=mesh(name,v,f,mat,.001);o.location=loc
 if axis=='X':o.rotation_euler[1]=pi/2
 if axis=='Y':o.rotation_euler[0]=pi/2
 return o
def rod(name,a,b,r,mat=paint):
 a,b=Vector(a),Vector(b);o=cyl(name,(a+b)/2,r,(b-a).length,mat,b=.001);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def bolt(name,loc,axis='Z',r=.012):return cyl(name,loc,r,.012,edge,axis,6,b=.001)
def handle(name,x,y,z,w=.14):
 rod(name,(x-w/2,y,z),(x+w/2,y,z),.009)
 for s in [-1,1]:rod(name+' foot',(x+s*w/2,y,z),(x+s*w/2,y,z-.035),.009)
# Revision 2: explicit frontal plate planes instead of the old steep wedge.
# German nominal angles, from vertical: driver 9 deg, nose 25 deg, glacis 80 deg.
DRIVER_ANGLE=math.radians(9);GLACIS_ANGLE=math.radians(80);NOSE_ANGLE=math.radians(25)
DRIVER_BASE=(2.65,1.34)
DRIVER_TOP=(DRIVER_BASE[0]-(1.825-DRIVER_BASE[1])*math.tan(DRIVER_ANGLE),1.825)
NOSE_TOP=(3.158,DRIVER_BASE[1]-(3.158-DRIVER_BASE[0])/math.tan(GLACIS_ANGLE))
NOSE_BOTTOM=(NOSE_TOP[0]-(NOSE_TOP[1]-.60)*math.tan(NOSE_ANGLE),.60)
profile=[(-3.158,.72),(-2.75,.47),(2.55,.47),NOSE_BOTTOM,NOSE_TOP,DRIVER_BASE,(DRIVER_TOP[0],1.800),(-2.96,1.800)]
v=[(x,y,z) for y in [-.99,.99] for x,z in profile];n=len(profile)
f=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
mesh('Lower hull shaped plate shell',v,f)
# Upper side armour stops at the driver plate, rather than protruding through it.
for side in [-1,1]:
 poly=[(-2.97,1.295),(2.65,1.295),(2.65,1.34),(DRIVER_TOP[0],1.800),(-2.97,1.800)]
 vv=[(x,y,z) for y in [side*.99,side*1.404] for x,z in poly];nn=len(poly)
 ff=[tuple(range(nn-1,-1,-1)),tuple(range(nn,2*nn))]+[(i,(i+1)%nn,(i+1)%nn+nn,i+nn) for i in range(nn)]
 mesh('Sponson side %s'%side,vv,ff)
box('Main roof',((-2.97+DRIVER_TOP[0])/2,0,1.8125),(DRIVER_TOP[0]+2.97,2.808,.025))
def plate_between(name,a,b,width,thickness):
 mid=((a[0]+b[0])/2,0,(a[1]+b[1])/2)
 o=box(name,mid,(thickness,width,math.dist(a,b)),paint,.002)
 o.rotation_euler[1]=math.atan2(b[0]-a[0],b[1]-a[1]);return o
plate_between('Driver armour 100mm 9deg',DRIVER_BASE,DRIVER_TOP,2.808,.100)
plate_between('Glacis armour 60mm 80deg',NOSE_TOP,DRIVER_BASE,2.808,.060)
plate_between('Nose armour 100mm 25deg',NOSE_BOTTOM,NOSE_TOP,1.98,.100)
def driver_x(z):return DRIVER_BASE[0]-(z-DRIVER_BASE[1])*math.tan(DRIVER_ANGLE)+.052
# Front driver's vision and bow MG.
o=box('Driver visor surround',(driver_x(1.64),.67,1.64),(.04,.38,.18),paint);o.rotation_euler[1]=-DRIVER_ANGLE
box('Driver vision slit',(driver_x(1.655)+.025,.67,1.655),(.012,.27,.033),black,.001)
box('Driver visor lower lip',(driver_x(1.59)+.025,.67,1.59),(.055,.36,.055))
bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,radius=.135,location=(driver_x(1.59),-.69,1.59));o=put(bpy.context.object,'Bow MG ball mount',paint);o.scale=(.48,1,1)
cyl('Bow MG jacket',(driver_x(1.59)+.20,-.69,1.59),.025,.38,edge,'X');tube('Bow MG open muzzle',(driver_x(1.59)+.40,-.69,1.59),.026,.012,.04,edge)
for y in [-.76,.76]:
 cyl('Driver radio operator hatch',(2.10,y,1.85),.255,.035)
 handle('Hatch handle',2.10,y,1.91)
 box('Periscope base',(2.43,y,1.88),(.18,.20,.07));box('Periscope glass',(2.525,y,1.89),(.008,.12,.032),black,.001)
for s in [-1,1]:
 for x in [2.98,-2.96]:
  box('Tow shackle bracket',(x,s*1.04,.98),(.18,.12,.22));tube('Tow shackle eye',(x+.07,s*1.04,1.0),.086,.047,.10,edge,'Y')
 for i in range(6):
  x=-2.55+i*.93;box('Segmented side fender',(x,s*1.62,1.35),(.91,.43,.035))
  for dx in [-.34,.34]:bolt('Fender fastener',(x+dx,s*1.43,1.378))
 box('Front mudguard',(2.90,s*1.49,1.32),(.48,.725,.035))
 cyl('Headlamp housing',(2.64,s*1.12,1.94),.083,.12,paint,'X')
 cyl('Headlamp lens',(2.705,s*1.12,1.94),.066,.008,black,'X')
 box('Headlamp blackout slit',(2.713,s*1.12,1.94),(.01,.112,.009),edge,.001)
# Running gear: 20 metal wheels / 24 tyres per side, including 4 twin-tyre wheels.
# All eight roadwheel stations retain 515mm pitch and 800mm tyre diameter.
current='02_Running_Gear'
WHEEL_Z=.455
PITCH=.130
DRIVE_PITCH_R=PITCH/(2*math.sin(pi/20))
DRIVE_X=2.54;DRIVE_Z=.94;IDLER_Z=.78;IDLER_R=.35
# Construct the track loop from wheel support geometry and solve idler location
# so 96 hinge-to-hinge chords close with the 130mm nominal pitch.
def convex_hull(points):
 pts=sorted(set(points))
 def cross2(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
 lo=[];hi=[]
 for p in pts:
  while len(lo)>=2 and cross2(lo[-2],lo[-1],p)<=0:lo.pop()
  lo.append(p)
 for p in reversed(pts):
  while len(hi)>=2 and cross2(hi[-2],hi[-1],p)<=0:hi.pop()
  hi.append(p)
 return lo[:-1]+hi[:-1]
def track_path(idler_x):
 circles=[(DRIVE_X,DRIVE_Z,DRIVE_PITCH_R),(idler_x,IDLER_Z,IDLER_R+.0275)]
 circles += [(1.87-i*.515,WHEEL_Z,.4275) for i in range(8)]
 pts=[(x+r*cos(k*2*pi/240),z+r*sin(k*2*pi/240)) for x,z,r in circles for k in range(240)]
 hull=convex_hull(pts)
 # Introduce the return-run sag over the road wheels. Lower support stays exact.
 points=[]
 for i,a in enumerate(hull):
  b=hull[(i+1)%len(hull)];points.append(a)
  # Hull is CCW; upper supporting bridge travels towards rear (-X).
  if b[0]<a[0]-.8 and a[1]>.9 and b[1]>.9:
   for k in range(1,81):
    t=k/81;x=a[0]+t*(b[0]-a[0]);linear=a[1]+t*(b[1]-a[1])
    floor=WHEEL_Z+.4275
    z=max(floor,linear-.30*math.sin(pi*t))
    points.append((x,z))
 points.append(points[0]);return points
# Return 96 successive points and the unwrapped curve coordinate after step 96.
def march(points):
 ext=points[:-1]+points;idx=0;t0=0.;pos=Vector(points[0]);pins=[pos.copy()]
 for step in range(96):
  found=False
  while idx<len(ext)-1:
   a=Vector(ext[idx]);d=Vector(ext[idx+1])-a;q=a-pos
   A=d.dot(d);B=2*q.dot(d);C=q.dot(q)-PITCH*PITCH;disc=B*B-4*A*C
   if A>1e-18 and disc>=0:
    root=(-B+math.sqrt(disc))/(2*A)
    if root>t0+1e-9 and root<=1+1e-9:
     pos=a+root*d;t0=root;found=True;break
   idx+=1;t0=0.
  if not found:raise RuntimeError('Track marching exceeded loop')
  if step<95:pins.append(pos.copy())
 return pins,idx+t0-(len(points)-1)
lo,hi=-3.1,-1.90
flo=march(track_path(lo))[1];fhi=march(track_path(hi))[1]
assert flo*fhi<0,'Track idler root not bracketed'
for _ in range(48):
 mid=(lo+hi)/2;fm=march(track_path(mid))[1]
 if fm*flo>0:lo=mid;flo=fm
 else:hi=mid
IDLER_X=(lo+hi)/2
points=track_path(IDLER_X);track_pins,closure=march(points)
print('TRACK_CONSTRAINT',IDLER_X,closure,flush=True)
for side in [-1,1]:
 for i in range(8):
  x=1.87-i*.515;z=WHEEL_Z
  rod('Suspension swing arm',(x-.16*side,side*1.0,.65),(x,side*1.30,z),.055)
  # Odd stations: central twin tyre + detachable outer wheel. Even: three singles.
  entries=[(1.32,True),(1.64,False)] if i%2==0 else [(1.18,False),(1.46,False),(1.765,False)]
  for lateral,twin in entries:
   y=side*lateral
   offsets=[-.043,.043] if twin else [0]
   for offset in offsets:
    ty=y+side*offset
    # Forged tyre profile: 90mm max width and 60mm flat running surface.
    n=64;v=[]
    rings=[(-.045,.370),(-.030,.400),(.030,.400),(.045,.370)]
    for axial,r in rings:v.extend([(x+r*cos(k*2*pi/n),ty+axial,z+r*sin(k*2*pi/n)) for k in range(n)])
    f=[tuple(range(n-1,-1,-1)),tuple(range(3*n,4*n))]
    for ring in range(3):
     for k in range(n):f.append((ring*n+k,ring*n+(k+1)%n,(ring+1)*n+(k+1)%n,(ring+1)*n+k))
    mesh('800mm tyre twin' if twin else '800mm tyre single',v,f,rubber,.001)
   cyl('Wheel dished steel face',(x,y+side*.008,z),.344,.078,paint,'Y',r2=.319)
   cyl('Wheel axle cap',(x,y+side*(.106 if twin else .064),z),.095,.045,paint,'Y')
   for k in range(6):
    a=2*pi*k/6;bolt('Six wheel hub bolts',(x+.127*cos(a),y+side*(.105 if twin else .063),z+.127*sin(a)),'Y',.011)
 for x,z,r,kind in [(DRIVE_X,DRIVE_Z,DRIVE_PITCH_R-.025,'Drive sprocket'),(IDLER_X,IDLER_Z,IDLER_R,'Rear idler')]:
  laterals=[1.15,1.58] if kind=='Drive sprocket' else [1.275,1.365]
  for y0 in laterals:
   y=side*y0
   cyl(kind,(x,y,z),r,.060,paint,'Y');cyl(kind+' recessed face',(x,y+side*.034,z),r*.70,.010,black,'Y');cyl(kind+' hub',(x,y+side*.046,z),r*.30,.045,paint,'Y')
   if kind=='Drive sprocket':
    for k in range(20):
     a=k*2*pi/20;o=box('Sprocket tooth',(x+(DRIVE_PITCH_R+.003)*cos(a),y,z+(DRIVE_PITCH_R+.003)*sin(a)),(.050,.060,.032),edge,.003);o.rotation_euler[1]=-a
   else:
    for k in range(6):
     a=k*2*pi/6;rod('Idler radial spoke',(x+.07*cos(a),y,z+.07*sin(a)),(x+.27*cos(a),y,z+.27*sin(a)),.025)
# Articulated links. Each hinge is a measured point; adjacent hinges are 130mm apart.
current='03_Tracks'
for side in [-1,1]:
 for i,p in enumerate(track_pins):
  q=track_pins[(i+1)%96];center=(p+q)/2;d=q-p;ang=-math.atan2(d.y,d.x)
  # CCW loop means the interior is to the left of the direction of travel.
  inward=Vector((-d.y,d.x)).normalized()
  # Local positive Z after rotation is the inward normal for this CCW path.
  for j,(offset,width) in enumerate([(-.320,.085),(-.230,.055),(-.085,.170),(.115,.170),(.310,.105)]):
   o=box('Track %s link %02d panel %d'%('L' if side==1 else 'R',i+1,j),(center.x,side*(1.49+offset),center.y),(.126,width,.055),track,.002);o.rotation_euler[1]=ang
  # The transport-width sprocket windows lie inboard of the 205mm outer extension.
  # Guide teeth sit around the central twin-tyre row, not at the combat-track centre.
  for lateral in [1.235,1.405]:
   tpos=center+inward*.085
   o=box('Inner guide tooth',(tpos.x,side*lateral,tpos.y),(.048,.024,.120),track,.002);o.rotation_euler[1]=ang
  cyl('Track hinge pin %s %02d'%(side,i),(p.x,side*1.49,p.y),.014,.725,edge,'Y',16,b=.001)
# Turret shell, asymmetric U plan. Front +X, rear arc uses separate left/right widths.
current='04_Turret'
cx=.57; bottom=1.835; roof=2.625
outline=[(1.02,-.99),(1.02,1.10),(.35,1.10),(.05,1.10)]
for i in range(1,49):
 a=pi/2+pi*i/48;outline.append((.05+1.16*cos(a), (1.10 if sin(a)>=0 else .99)*sin(a)))
outline.append((.35,-.99))
front_tilt=math.tan(math.radians(5));roof_tilt=math.tan(math.radians(9));break_x=cx+.35
v=[(cx+x,y,bottom) for x,y in outline]
for x,y in outline:
 world_x=cx+x
 if x>.9:world_x=(world_x-front_tilt*(roof-bottom+roof_tilt*break_x))/(1-front_tilt*roof_tilt)
 z=roof-roof_tilt*max(0,world_x-break_x);v.append((world_x,y,z))
n=len(outline)
f=[tuple(range(n-1,-1,-1)),tuple(range(n+2,2*n)),(n,n+1,n+2,2*n-1)]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
mesh('Asymmetric curved turret exterior',v,f,paint,.008)
cyl('Turret ring nominal clearance',(cx,0,1.827),.925,.016,black)
# Roof panels are part of the turret mesh; no overlapping plate hides the bend.
rod('Turret roof bend seam',(break_x,-.99,roof+.001),(break_x,1.10,roof+.001),.002,paint)
# Mantlet is 110mm wider to left. Geometric approximation of cast contour.
cyl('Curved full width mantlet',(cx+1.12,.055,2.23),.390,1.63,paint,'Y',96)
o=box('Mantlet flat casting face',(cx+1.37,.055,2.23),(.11,1.74,.65),paint,.025)
box('Early mantlet splash strip',(cx+1.13,.055,2.575),(.14,1.63,.025))
cyl('Gun sleeve',(2.00,0,2.23),.175,.62,paint,'X')
cyl('Gun collar',(2.31,0,2.23),.14,.10,edge,'X')
# Long gun, separate tapered sections, hollow muzzle brake with real boolean ports.
cyl('88mm tapered gun tube',(3.49,0,2.23),.102,2.30,paint,'X',96,r2=.074)
tube('Muzzle coupling',(4.70,0,2.23),.105,.044,.18,paint)
brake=cyl('Double baffle muzzle brake',(4.992,0,2.23),.145,.60,paint,'X',64)
# bore along X
cut=cyl('Bore cutter',(4.995,0,2.23),.044,.9,None,'X',48,b=0)
bpy.context.view_layer.update();bpy.context.view_layer.objects.active=brake
mod=brake.modifiers.new('Open 88mm bore','BOOLEAN');mod.object=cut
bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
for x in [4.86,5.08]:
 cut=box('Port cutter',(x,0,2.23),(.13,.5,.13),None,0);cut.rotation_euler[2]=math.radians(18)
 bpy.context.view_layer.update();bpy.context.view_layer.objects.active=brake;mod=brake.modifiers.new('Through muzzle brake gas port','BOOLEAN');mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
for y in [.39,.48]:cyl('Binocular sight recess',(2.095,y,2.32),.021,.02,black,'X',32)
cyl('Coaxial MG opening',(2.095,-.55,2.28),.026,.025,black,'X',32)
# Early tall cupola, no late cast cupola or late Zimmerit.
cyl('Early drum commanders cupola',(.10,.63,2.765),.31,.28)
cyl('Cupola top hatch',(.10,.63,2.922),.324,.035)
cyl('Cupola base ring',(.10,.63,2.635),.34,.035)
for j in range(5):
 a=j*2*pi/5; o=box('Cupola vision slit',(.10+.307*cos(a),.63+.307*sin(a),2.78),(.016,.125,.038),black,.001);o.rotation_euler[2]=a
handle('Cupola hatch handle',.10,.63,2.97,.17)
cyl('Loader circular hatch',(.55,-.57,2.65),.27,.035);handle('Loader hatch handle',.55,-.57,2.705)
cyl('Turret roof ventilator',(.0,-.03,2.675),.145,.09);cyl('Ventilator cover',(.0,-.03,2.728),.17,.025)
# Rear stowage bin.
box('Turret rear stowage bin',(-.88,.02,2.22),(.50,1.82,.57))
box('Stowage bin lid',(-.88,.02,2.523),(.53,1.85,.035))
for y in [-.60,.60]:box('Bin latch',(-1.145,y,2.30),(.025,.045,.18),edge)
# Side vision ports, right escape hatch, early smoke dischargers.
for s in [-1,1]:
 box('Turret side vision block',(1.03,s*(1.105 if s==1 else .995),2.32),(.20,.035,.10))
 for i in range(3):
  x=1.34-i*.16;y=s*(1.13 if s==1 else 1.02)
  o=tube('Smoke discharger',(x,y,2.45),.055,.041,.19,paint,'Z',32);o.rotation_euler[0]=s*.55
  rod('Smoke launcher support',(x,y,2.30),(x,y,2.40),.018)
cyl('Right circular escape hatch',(.05,-.956,2.18),.245,.06,paint,'Y')
# Engine deck, grilles, rear exhausts and Feifel filters.
current='05_Engine_Deck_and_Fittings'
box('Engine access deck',(-2.00,0,1.849),(1.72,1.00,.035))
for s in [-1,1]:
 for x in [-2.48,-1.55]:
  box('Radiator grille dark well',(x,s*.97,1.846),(.79,.64,.025),black)
  for j in range(12):box('Radiator grille slat',(x-.36+j*.065,s*.97,1.872),(.022,.64,.025),paint,.002)
  for y in [s*.66,s*1.27]:box('Grille frame',(x,y,1.88),(.82,.025,.03))
 cyl('Rear exhaust stack',(-3.18,s*.48,1.35),.105,.70,track)
 cyl('Exhaust mushroom cap',(-3.18,s*.48,1.735),.15,.06,paint)
 box('Exhaust armour guard',(-3.29,s*.48,1.16),(.12,.39,.60))
 cyl('Feifel air filter canister',(-3.20,s*1.06,1.48),.17,.65)
 cyl('Feifel filter lid',(-3.20,s*1.06,1.82),.185,.035)
 rod('Air filter outlet',(-3.20,s*1.06,1.82),(-2.55,s*.55,1.92),.055)
 for x in [-2.65,-1.05]:
  handle('Engine deck lifting handle',x,s*.25,1.91)
 # Tow cable visible along each deck edge, curved polyline.
 pts=[(2.08,s*1.30,1.87),(1.75,s*1.32,1.91),(-.70,s*1.32,1.92),(-2.45,s*1.31,1.91),(-2.72,s*1.10,1.91)]
 for a,b in zip(pts,pts[1:]):rod('Tow cable',a,b,.021,edge)
 # Shovel and prybar tool kit.
 rod('Pioneer tool wooden handle',(.25,s*1.21,1.91),(1.22,s*1.21,1.91),.025,wood)
 box('Shovel steel head',(1.36,s*1.21,1.91),(.28,.17,.025),edge)
 for x in [.4,.95]:box('Tool retaining clamp',(x,s*1.21,1.94),(.035,.10,.045),paint)
# Hull plate welding seams (small modeled beads).
for s in [-1,1]:rod('Roof longitudinal weld',(-2.87,s*1.39,1.836),(2.62,s*1.39,1.836),.007,edge)
# Recalculate outward normals, including custom tyre and plate prisms.
import bmesh
for collection in collections.values():
 for obj in collection.objects:
  if obj.type=='MESH':
   bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free();obj.data.update()
print('GEOMETRY_COMPLETE', flush=True)
# Root for model transforms, turret and gun remain individually editable.
allmodel=[o for c in collections.values() for o in c.objects]
root=bpy.data.objects.new('TIGER I - EARLY - visual reconstruction (metres)',None);base.objects.link(root)
for o in allmodel:o.parent=root
root['revision']='2 - source-constrained hull planes, mantlet radius, tyre layout, articulated tracks'
root['accuracy']='Reference-informed visual reconstruction. Not a metrology-certified replica. See research notes.'
root['reference_track_width_mm']=725;root['reference_roadwheel_diameter_mm']=800;root['reference_hull_width_mm']=2808
# Studio setup separate from export.
current='99_Studio'
floor=material('Studio warm graphite',(.055,.067,.078),.1,.65)
box('Studio floor',(0,0,-.09),(200,200,.1),floor,0)
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
def area(name,loc,power,size,color):
 bpy.ops.object.light_add(type='AREA',location=loc);o=put(bpy.context.object,name,None);o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.data.color=color;aim(o,(0,0,1))
area('Key softbox',(3,5,9),1800,7,(1,.90,.75));area('Fill softbox',(1,-6,5),1500,6,(.72,.85,1));area('Rim strip',(-5,2,7),2200,5,(1,.96,.87))
bpy.ops.object.camera_add(location=(10,-12,7.7));cam=put(bpy.context.object,'Camera_hero',None);aim(cam,(.55,0,1.35));cam.data.type='ORTHO';cam.data.ortho_scale=11.2;bpy.context.scene.camera=cam
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.length_unit='METERS'
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=False
scene.render.resolution_x=1400;scene.render.resolution_y=920;scene.render.resolution_percentage=100
scene.world.color=(.18,.18,.18);scene.view_settings.view_transform='AgX'
# Open comfortably in solid/material view.
for screen in bpy.data.screens:
 for ar in screen.areas:
  if ar.type=='VIEW_3D':
   ar.spaces.active.region_3d.view_distance=11;ar.spaces.active.region_3d.view_location=Vector((.5,0,1.2));ar.spaces.active.clip_end=1000
bpy.ops.object.select_all(action='DESELECT')
for o in allmodel:o.select_set(True)
bpy.context.view_layer.objects.active=allmodel[0]
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Tiger_I_Early.blend')
bpy.ops.export_scene.gltf(filepath=OUT+'/Tiger_I_Early.glb',export_format='GLB',use_selection=True,export_apply=True)
scene.render.filepath=OUT+'/Tiger_I_preview.png';bpy.ops.render.render(write_still=True) if os.environ.get('TIGER_RENDER','1')=='1' else None
# Second rear view verifies the engine deck and exhaust equipment.
cam.location=(-9,10,6.5);aim(cam,(.1,0,1.35));cam.data.ortho_scale=10.3
scene.render.filepath=OUT+'/Tiger_I_rear.png';bpy.ops.render.render(write_still=True) if os.environ.get('TIGER_RENDER','1')=='1' else None
# Nominal envelope and topology report for review.
coords=[o.matrix_world@Vector(v) for o in allmodel for v in o.bound_box]
report={'mesh_objects':len(allmodel),'nominal_reference_dimensions_mm':{'bare_hull_width':2808,'combat_track_width':725,'road_wheel_diameter':800,'turret_roof_height':2625,'axle_station_pitch':515},'model_envelope_m':{k:round(max(v[i] for v in coords)-min(v[i] for v in coords),4) for i,k in enumerate(['length','width','height'])},'scope':'Visual exterior only; no functional mechanisms or internal weapon construction; many small fittings interpreted.'}
with open(OUT+'/validation.json','w') as f:json.dump(report,f,indent=2)
print('BUILD_COMPLETE',json.dumps(report))

# Measure the generated meshes independently of their intended target values.
checks=[]
def check(label,actual,reference,unit,tolerance,source):
 checks.append(dict(label=label,actual=actual,reference=reference,unit=unit,error=actual-reference,tolerance=tolerance,passed=abs(actual-reference)<=tolerance,source=source))
def plate_angle(name):
 o=bpy.data.objects[name];normal=o.rotation_euler.to_matrix()@Vector((1,0,0));return math.degrees(math.acos(min(1,abs(normal.x))))
check('Driver plate inclination from vertical',plate_angle('Driver armour 100mm 9deg'),9,'deg',.0001,'German plate specifications, Jentz/Doyle')
check('Glacis inclination from vertical',plate_angle('Glacis armour 60mm 80deg'),80,'deg',.0001,'German plate specifications, Jentz/Doyle')
check('Nose inclination from vertical',plate_angle('Nose armour 100mm 25deg'),25,'deg',.0001,'German plate specifications, Jentz/Doyle')
roof_o=bpy.data.objects['Main roof'];check('Bare hull width',roof_o.dimensions.y*1000,2808,'mm',.001,'TIGER1.INFO Hull dimensions')
check('Turret underside clearance',(bpy.data.objects['Asymmetric curved turret exterior'].location.z+min(v.co.z for v in bpy.data.objects['Asymmetric curved turret exterior'].data.vertices)-max((roof_o.matrix_world@v.co).z for v in roof_o.data.vertices))*1000,10,'mm',.001,'TIGER1.INFO Turret dimensions')
front_o=bpy.data.objects['Asymmetric curved turret exterior'];verts=front_o.data.vertices;fronts=[v.co for v in verts if v.co.x>cx+.9];zlo=min(p.z for p in fronts);zhi=max(p.z for p in fronts);xlo=max(p.x for p in fronts if abs(p.z-zlo)<1e-5);xhi=max(p.x for p in fronts if abs(p.z-zhi)<1e-5);check('Turret front inclination',math.degrees(math.atan2(xlo-xhi,zhi-zlo)),5,'deg',.0001,'TIGER1.INFO Turret front plates')
m=bpy.data.objects['Curved full width mantlet'];rad=max(math.hypot(v.co.x,v.co.y) for v in m.data.vertices);check('Mantlet cylinder radius',rad*1000,390,'mm',.001,'TIGER1.INFO Mantlet protector')
for side in [-1,1]:
 pins=[bpy.data.objects['Track hinge pin %s %02d'%(side,i)].location for i in range(96)]
 pitches=[(pins[(i+1)%96]-p).length*1000 for i,p in enumerate(pins)]
 check('Track %s maximum pitch residual'%side,max(abs(p-130) for p in pitches),0,'mm',.01,'Kgs 63/725/130 nominal link pitch')
 check('Track %s link count'%side,len(pins),96,'count',0,'96-link reference configuration')
check('Twin-tyre assemblies',sum(1 for o in allmodel if o.name.startswith('800mm tyre twin'))//2,8,'count',0,'TIGER1.INFO Double wheel')
check('Tyres overall',sum(1 for o in allmodel if o.name.startswith('800mm tyre')),48,'count',0,'20 metal wheels / 24 tyres on each side')
report['revision']=2;report['checks']=checks;report['idler_x_m']=IDLER_X;report['track_constraint_note']='Idler location is solved to close the 96 x 130mm chain. It is not independently survey-verified.'
with open(OUT+'/validation.json','w') as f:json.dump(report,f,indent=2)
assert all(c['passed'] for c in checks),json.dumps([c for c in checks if not c['passed']])
print('DIMENSION_CHECKS_PASSED',len(checks),flush=True)

for label,prefix in [('Roadwheel diameter','800mm tyre'),('Track link width','Track hinge pin')]:
 matches=[o for o in allmodel if o.name.startswith(prefix)]
 if prefix=='800mm tyre':
  diameters=[(max(v.co.z for v in o.data.vertices)-min(v.co.z for v in o.data.vertices))*1000 for o in matches]
  check(label,max(abs(d-800) for d in diameters),0,'mm',.001,'TIGER1.INFO ExternalTyreWheels')
 else:
  widths=[(max(v.co.z for v in o.data.vertices)-min(v.co.z for v in o.data.vertices))*1000 for o in matches]
  check(label,max(abs(w-725) for w in widths),0,'mm',.001,'TIGER1.INFO Hull dimensions')
wheel_positions=sorted(set(round(o.location.x,6) for o in allmodel if o.name.startswith('Wheel dished steel face')))
check('Axle station spacing',max(abs((b-a)*1000-515) for a,b in zip(wheel_positions,wheel_positions[1:])),0,'mm',.001,'TIGER1.INFO RoadWheelSpacing')
check('Overall envelope width',report['model_envelope_m']['width']*1000,3705,'mm',.1,'Combat track envelope target; fittings kept inside')
report['checks']=checks
with open(OUT+'/validation.json','w') as f:json.dump(report,f,indent=2)
assert all(c['passed'] for c in checks),json.dumps([c for c in checks if not c['passed']])
print('ALL_CHECKS_PASSED',len(checks),flush=True)
